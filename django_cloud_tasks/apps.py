from django.apps import AppConfig
from django.conf import settings

from .connection import connection


class DCTConfig(AppConfig):
    name = 'django_cloud_tasks'
    verbose_name = "Django Cloud Tasks"

    def ready(self):
        self.module.autodiscover()

    @classmethod
    def _settings(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS')

    @classmethod
    def default_queue(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_DEFAULT_QUEUE', 'push-default')

    @classmethod
    def project_location_name(cls):
        return cls._settings().get('project_location_name')

    @classmethod
    def task_handler_root_url(cls):
        return cls._settings().get('task_handler_root_url')

    @classmethod
    def execute_locally(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_EXECUTE_LOCALLY', False)

    @classmethod
    def block_remote_tasks(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_BLOCK_REMOTE_TASKS', False)

    @classmethod
    def handler_secret(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_HANDLER_SECRET', None)

    @classmethod
    def region(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_REGION', None)

    @classmethod
    def http_service_account(cls):
        return cls._settings().get('http_service_account')
