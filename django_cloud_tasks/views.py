from django.http import JsonResponse
import logging
from django.views.decorators.csrf import csrf_exempt
import json
from .registries import registry
from .base import CloudTaskRequest

logger = logging.getLogger(__name__)


@csrf_exempt
def run_task(request):
    body = json.loads(request.body.decode('utf-8'))
    request_headers = request.META
    task_name = request_headers.get('HTTP_X_APPENGINE_TASKNAME')
    task_queue_name = request_headers.get('HTTP_X_APPENGINE_QUEUENAME')

    logger_extra = {
        'taskName': task_name,
        'taskQueueName': task_queue_name,
        'taskPayload': body,
        'taskRequestHeaders': dict(request_headers)
    }
    try:
        internal_task_name = body['internal_task_name']
        data = body.get('data', dict())
        func = registry.get_task(internal_task_name)
        cloud_request = CloudTaskRequest.from_cloud_request(request)
        func.run(request=cloud_request, **data) if data else func.run(request=cloud_request)
    except Exception as e:
        logger.exception(
            e, extra=logger_extra
        )
        return JsonResponse({'status': 'error'}, status=500)

    logger.info('Task executed successfully', extra=logger_extra)
    return JsonResponse({'status': 'ok', 'message': 'ok'}, status=200)
