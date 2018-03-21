from django.utils.module_loading import autodiscover_modules
from .base import batch_execute, remote_task  # noqa
from .decorators import task

__version__ = '0.0.1'


def autodiscover():
    autodiscover_modules('cloud_tasks')


default_app_config = 'django_cloud_tasks.apps.DCTConfig'
