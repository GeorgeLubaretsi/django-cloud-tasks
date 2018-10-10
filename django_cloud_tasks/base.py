import base64
import json
import decimal
import logging
import time
import uuid
import datetime

from django.test import RequestFactory

from .constants import DJANGO_HANDLER_SECRET_HEADER_NAME, HANDLER_SECRET_HEADER_NAME
from .apps import DCTConfig
from .connection import connection

logger = logging.getLogger(__name__)


def _get_duration_components(duration):
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds = seconds % 60

    hours = minutes // 60
    minutes = minutes % 60

    return days, hours, minutes, seconds, microseconds


def _duration_iso_string(duration):
    if duration < datetime.timedelta(0):
        sign = '-'
        duration *= -1
    else:
        sign = ''

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = '.{:06d}'.format(microseconds) if microseconds else ""
    return '{}P{}DT{:02d}H{:02d}M{:02d}{}S'.format(sign, days, hours, minutes, seconds, ms)


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            r = obj.isoformat()
            if obj.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            if obj.utcoffset() is not None:
                raise ValueError("JSON can't represent timezone-aware times.")
            r = obj.isoformat()
            if obj.microsecond:
                r = r[:12]
            return r
        elif isinstance(obj, datetime.timedelta):
            return _duration_iso_string(obj)
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return obj.hex
        else:
            return super().default(obj)


def retry(retry_limit, retry_interval):
    """
    Decorator for retrying task scheduling
    """

    def decorator(f):
        def wrapper():
            attempts_left = retry_limit
            error = None
            while attempts_left > 1:
                try:
                    return f()
                except Exception as e:
                    error = e
                    logger.exception('Task scheduling failed. Retrying...')
                    time.sleep(retry_interval)
                    attempts_left -= 1

            # Limit exhausted
            error.args = ('Task scheduling limit exhausted',) + error.args
            raise error

        return wrapper

    return decorator


def batch_callback_logger(id, message, exception):
    if exception:
        resp, _bytes = exception.args
        decoded = json.loads(_bytes.decode('utf-8'))
        raise Exception(decoded['error']['message'])


def batch_execute(tasks, retry_limit=10, retry_interval=3):
    """
    Executes tasks in batch
    :param tasks: list of CloudTaskWrapper objects
    :param retry_limit: How many times task scheduling will be attempted
    :param retry_interval: Interval between task scheduling attempts in seconds
    """
    if len(tasks) >= 1000:
        raise Exception('Maximum number of tasks in batch cannot exceed 1000')

    if DCTConfig.execute_locally():
        for t in tasks:
            if not t._is_remote:
                t.execute_local()
            elif t._is_remote and DCTConfig.block_remote_tasks():
                logger.debug(
                    'Remote task {0} was ignored. Task data:\n {1}'.format(t._internal_task_name, t._data)
                )
        return

    client = connection.client
    batch = client.new_batch_http_request()

    # Override deprecated default batch URL
    batch._batch_uri = 'https://cloudtasks.googleapis.com/batch/v2alpha2/locations/us-central1'
    for t in tasks:
        batch.add(t.create_cloud_task(), callback=batch_callback_logger)

    if not retry_limit:
        return batch.execute()
    else:
        return retry(retry_limit=retry_limit, retry_interval=retry_interval)(batch.execute)()


class BaseTask(object):
    pass


class CloudTaskMockRequest(object):
    def __init__(self, request=None, task_id=None, request_headers=None):
        self.request = request
        self.task_id = task_id
        self.request_headers = request_headers
        self.setup()

    def setup(self):
        if not self.task_id:
            self.task_id = uuid.uuid4().hex
        if not self.request_headers:
            self.request_headers = dict()


class EmulatedTask(object):
    def __init__(self, body):
        self.body = body
        self.setup()

    def setup(self):
        payload = self.body['task']['appEngineHttpRequest']['body']
        decoded = json.loads(base64.b64decode(payload))
        self.body['task']['appEngineHttpRequest']['body'] = decoded

    def get_json_body(self):
        body = self.body['task']['appEngineHttpRequest']['body']
        return json.dumps(body)

    @property
    def request_headers(self):
        return {
            'HTTP_X_APPENGINE_TASKNAME': uuid.uuid4().hex,
            'HTTP_X_APPENGINE_QUEUENAME': 'emulated',
            DJANGO_HANDLER_SECRET_HEADER_NAME: DCTConfig.handler_secret()
        }

    def execute(self):
        from .views import run_task
        request = RequestFactory().post('/_tasks/', data=self.get_json_body(),
                                        content_type='application/json',
                                        **self.request_headers)
        return run_task(request=request)


class CloudTaskRequest(object):
    def __init__(self, request, task_id, request_headers):
        self.request = request
        self.task_id = task_id
        self.request_headers = request_headers

    @classmethod
    def from_cloud_request(cls, request):
        request_headers = request.META
        task_id = request_headers.get('HTTP_X_APPENGINE_TASKNAME')
        return cls(
            request=request,
            task_id=task_id,
            request_headers=request_headers
        )


class CloudTaskWrapper(object):
    def __init__(self, base_task, queue, data,
                 internal_task_name=None, task_handler_url=None,
                 is_remote=False, headers=None):
        self._base_task = base_task
        self._data = data
        self._queue = queue
        self._connection = None
        self._internal_task_name = internal_task_name or self._base_task.internal_task_name
        self._task_handler_url = task_handler_url or DCTConfig.task_handler_root_url()
        self._handler_secret = DCTConfig.handler_secret()
        self._is_remote = is_remote
        self._headers = headers or {}
        self.setup()

    def setup(self):
        self._connection = connection
        if not self._internal_task_name:
            raise ValueError('Either `internal_task_name` or `base_task` should be provided')
        if not self._task_handler_url:
            raise ValueError('Could not identify task handler URL of the worker service')

    def execute_local(self):
        return EmulatedTask(body=self.get_body()).execute()

    def execute(self, retry_limit=10, retry_interval=5):
        """
        Enqueue cloud task and send for execution
        :param retry_limit: How many times task scheduling will be attempted
        :param retry_interval: Interval between task scheduling attempts in seconds
        """
        if DCTConfig.execute_locally() and not self._is_remote:
            return self.execute_local()

        if self._is_remote and DCTConfig.block_remote_tasks():
            logger.debug(
                'Remote task {0} was ignored. Task data:\n {1}'.format(self._internal_task_name, self._data)
            )
            return None

        if not retry_limit:
            return self.create_cloud_task().execute()
        else:
            return retry(retry_limit=retry_limit, retry_interval=retry_interval)(self.create_cloud_task().execute)()

    def run(self, mock_request=None):
        """
        Runs actual task function. Used for local execution of the task handler
        :param mock_request: Task instances accept request argument that holds various attributes of the request
        coming from Cloud Tasks service. You can pass a mock request here that emulates that request. If not provided,
        default mock request is created from `CloudTaskMockRequest`
        """
        request = mock_request or CloudTaskMockRequest()
        return self._base_task.run(request=request, **self._data) if self._data else self._base_task.run(request=request)

    def set_queue(self, queue):
        self._queue = queue

    @property
    def _cloud_task_queue_name(self):
        return '{}/queues/{}'.format(DCTConfig.project_location_name(), self._queue)

    @property
    def formatted_headers(self):
        formatted = {}
        for key, value in self._headers.items():
            _key = key.replace('_', '-').upper()
            formatted[_key] = value
        # add secret key
        formatted[HANDLER_SECRET_HEADER_NAME] = self._handler_secret
        return formatted

    def get_body(self):
        body = {
            'task': {
                'appEngineHttpRequest': {
                    'httpMethod': 'POST',
                    'relativeUri': self._task_handler_url,
                    'headers': self.formatted_headers
                }
            }
        }

        payload = {
            'internal_task_name': self._internal_task_name,
            'data': self._data
        }
        payload = json.dumps(payload, cls=ComplexEncoder)
        logger.debug('Creating task with body {0}'.format(payload),
                    extra={'taskBody': payload
                           })
        base64_encoded_payload = base64.b64encode(payload.encode())
        converted_payload = base64_encoded_payload.decode()

        body['task']['appEngineHttpRequest']['body'] = converted_payload
        return body

    def create_cloud_task(self):
        task = self._connection.tasks_endpoint.create(parent=self._cloud_task_queue_name, body=self.get_body())
        return task

class RemoteCloudTask(object):
    def __init__(self, queue, handler, task_handler_url=None, headers=None):
        self.queue = queue
        self.handler = handler
        self.task_handler_url = task_handler_url or DCTConfig.task_handler_root_url()
        self.headers = headers

    def payload(self, payload):
        """
        Set payload and return task instance
        :param payload: Dict Payload
        :return: `CloudTaskWrapper` instance
        """
        task = CloudTaskWrapper(base_task=None, queue=self.queue, internal_task_name=self.handler,
                                task_handler_url=self.task_handler_url,
                                data=payload, is_remote=True, headers=self.headers)
        return task

    def __call__(self, *args, **kwargs):
        return self.payload(payload=kwargs)


def remote_task(queue, handler, task_handler_url=None, **headers):
    """
    Returns `RemoteCloudTask` instance. Can be used for scheduling tasks that are not available in the current scope
    :param queue: Queue name
    :param handler: Task handler function name
    :param task_handler_url: Entry point URL of the worker service for the task
    :param headers: Headers that will be sent to the task handler
    :return: `CloudTaskWrapper` instance
    """
    task = RemoteCloudTask(queue=queue, handler=handler, task_handler_url=task_handler_url, headers=headers)
    return task
