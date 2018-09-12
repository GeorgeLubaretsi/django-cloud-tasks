import googleapiclient.discovery


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
        client = googleapiclient.discovery.build('cloudtasks', 'v2beta3')
        return client

    @cached_property
    def tasks_endpoint(self):
        client = self.client
        tasks_endpoint = client.projects().locations().queues().tasks()
        return tasks_endpoint


connection = GoogleCloudClient()
