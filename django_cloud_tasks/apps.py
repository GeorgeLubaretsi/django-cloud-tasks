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
    def app_engine_routing(cls):
        return cls._settings().get('app_engine_routing', None)

    @classmethod
    def http_request_domain(cls):
        return cls._settings().get('http_request_domain', 'https://example.com')

    @classmethod
    def request_target(cls):
        return cls._settings().get('request_target', 'app_engine')

    @classmethod
    def execute_locally(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_EXECUTE_LOCALLY', False)

    @classmethod
    def block_remote_tasks(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_BLOCK_REMOTE_TASKS', False)

    @classmethod
    def handler_secret(cls):
        return getattr(settings, 'DJANGO_CLOUD_TASKS_HANDLER_SECRET', None)
