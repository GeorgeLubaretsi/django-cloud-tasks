import logging

logger = logging.getLogger(__name__)


class CloudTaskRegistry(object):
    """
    Registry of cloud tasks.
    """
    def __init__(self):
        self._registry = {}

    def register(self, base_task_class):
        self._registry[base_task_class.internal_task_name] = base_task_class
        logger.info('Task {0} registered'.format(base_task_class.internal_task_name))

    def get_task(self, name):
        return self._registry[name]


registry = CloudTaskRegistry()
