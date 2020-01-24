import googleapiclient.discovery
import os.path
import hashlib
import tempfile

from .apps import DCTConfig


class DiscoveryCache:
    """
    Unix file-based cache for use with the API Discovery service

    See https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-419387788
    """
    def filename(self, url):
        return os.path.join(
            tempfile.gettempdir(),
            'google_api_discovery_' + hashlib.md5(url.encode()).hexdigest())

    def get(self, url):
        try:
            with open(self.filename(url), 'rb') as f:
                return f.read().decode()
        except FileNotFoundError:
            return None

    def set(self, url, content):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content.encode())
            f.flush()
            os.fsync(f)
        os.rename(f.name, self.filename(url))


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
                cache=DiscoveryCache())
        return client

    @cached_property
    def tasks_endpoint(self):
        client = self.client
        tasks_endpoint = client.projects().locations().queues().tasks()
        return tasks_endpoint


connection = GoogleCloudClient()
