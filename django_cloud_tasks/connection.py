import googleapiclient.discovery
from cachetools import Cache

from .apps import DCTConfig


class MemoryCache(Cache):
    """
    In-memory cache for use with API Discovery service.

    Fixes https://github.com/googleapis/google-api-python-client/issues/325

    Solution is from https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-274349841
    """
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


class cached_property(object):
    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value


class GoogleCloudClient(object):
    @cached_property
    def client(self):
        client = googleapiclient.discovery.build('cloudtasks', 'v2beta3',
                credentials=DCTConfig.google_cloud_credentials(), 
                cache=MemoryCache())
        return client

    @cached_property
    def tasks_endpoint(self):
        client = self.client
        tasks_endpoint = client.projects().locations().queues().tasks()
        return tasks_endpoint


connection = GoogleCloudClient()
