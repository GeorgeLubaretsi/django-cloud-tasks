import base64
import json

from django.conf import settings

from .connection import connection
from .apps import DCTConfig
import logging

logger = logging.getLogger(__name__)


def batch_callback_logger(id, message, exception):
    if exception:
        resp, _bytes = exception.args
        decoded = json.loads(_bytes.decode('utf-8'))
        raise Exception(decoded['error']['message'])


def batch_execute(tasks):
    """
    Executes tasks in batch
    :param tasks: list of CloudTaskWrapper objects
    """
    if len(tasks) >= 1000:
        raise Exception('Maximum number of tasks in batch cannot exceed 1000')
    client = connection.client
    batch = client.new_batch_http_request()
    for t in tasks:
        batch.add(t.create_cloud_task(), callback=batch_callback_logger)
    batch.execute()


class BaseTask(object):
    pass


class CloudTaskWrapper(object):
    def __init__(self, base_task, queue, data):
        self._base_task = base_task
        self._data = data
        self._queue = queue
        self.client = None
        self.setup()

    def setup(self):
        if not connection.client:
            con = connection.configure(**settings.DJANGO_CLOUD_TASKS)
        else:
            con = connection
        self.client = con.client

    def execute(self):
        """
        Enqueue cloud task and send for execution
        """
        return self.create_cloud_task().execute()

    def run(self):
        """
        Runs actual task function
        """
        return self._base_task.run(**self._data) if self._data else self._base_task.run()

    def set_queue(self, queue):
        self._queue = queue

    def _tasks_endpoint(self):
        return self.client.projects().locations().queues().tasks()

    @property
    def _cloud_task_queue_name(self):
        return '{}/queues/{}'.format(DCTConfig.project_location_name(), self._queue)

    def create_cloud_task(self):
        body = {
            'task': {
                'appEngineHttpRequest': {
                    'httpMethod': 'POST',
                    'relativeUrl': DCTConfig.task_handler_root_url()
                }
            }
        }

        payload = {
            'internal_task_name': self._base_task.internal_task_name,
            'data': self._data
        }
        payload = json.dumps(payload)

        base64_encoded_payload = base64.b64encode(payload.encode())
        converted_payload = base64_encoded_payload.decode()

        body['task']['appEngineHttpRequest']['payload'] = converted_payload

        task = self._tasks_endpoint().create(parent=self._cloud_task_queue_name, body=body)

        return task

