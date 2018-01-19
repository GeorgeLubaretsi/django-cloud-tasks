from django.http import JsonResponse
import logging
from django.views.decorators.csrf import csrf_exempt
import json
from .registries import registry
from .base import CloudTaskRequest

logger = logging.getLogger(__name__)


@csrf_exempt
def run_task(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        internal_task_name = body['internal_task_name']
        data = body.get('data', dict())
        func = registry.get_task(internal_task_name)
        cloud_request = CloudTaskRequest.from_cloud_request(request)
        func.run(request=cloud_request, **data) if data else func.run(request=cloud_request)
    except Exception as e:
        logger.error(str(e))
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    logger.info('Task executed successfully')
    return JsonResponse({'status': 'ok', 'message': 'ok'}, status=200)
