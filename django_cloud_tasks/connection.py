import googleapiclient.discovery


class GoogleCloudClient(object):
    def __init__(self):
        self.project_location_name = None
        self.task_handler_root_url = None
        self.client = None

    def configure(self, project_location_name, task_handler_root_url):
        self.project_location_name = project_location_name
        self.task_handler_root_url = task_handler_root_url
        self.client = googleapiclient.discovery.build('cloudtasks', 'v2beta2')
        return self


connection = GoogleCloudClient()
