============================
Django Cloud Tasks
============================
Integrate `Google Cloud Tasks <https://goo.gl/Ya0AZd>`_ with Django.

Package provides easy to use decorator to create task handlers.

App looks for tasks in ``cloud_tasks.py`` files in your installed applications and auto-registers them.

Package is in early alpha and it does not have any real security at the moment. You need to authorize requests coming
to your instances yourself.

Prerequisites
=============

- Django 1.8+
- Python 3.4, 3.5, 3.6

Dependencies
============

- `google-api-python-client <https://pypi.python.org/pypi/google-api-python-client/>`_

Documentation
=============

TODO

Installation
============

(1) Install latest version from Github:

    .. code-block:: sh

        pip install https://github.com/GeorgeLubaretsi/django-cloud-tasks.git


(2) Add ``django_cloud_tasks`` to ``INSTALLED_APPS``:

    .. code-block:: python

        INSTALLED_APPS = (
            # ...
            'django_cloud_tasks',
            # ...
        )


(3) Add configuration to your settings

    .. code-block:: python

        DJANGO_CLOUD_TASKS={
            'project_location_name': 'projects/{project_name}/locations/us-central1',
            'task_handler_root_url': '/_tasks/',
        },


(4) Add cloud task views to your urls.py (must resolve to the same url as ``task_handler_root_url``)

    .. code-block:: python

        # urls.py
        # ...
        from django.urls import path, include
        from django_cloud_tasks import urls as dct_urls

        urlpatterns = [
            # ...
            path('_tasks/', include(dct_urls)),
        ]



Quick start
===========

Simply import the task decorator and define the task inside ``cloud_tasks.py`` in your app.

.. code-block:: python

    # cloud_tasks.py
    # ...
    from django_cloud_tasks.decorators import task

    @task(queue='default')
    def example_task(p1, p2):
        print(p1, p2)


Pushing the task to the queue:

.. code-block:: python

    from my_app.cloud_tasks import example_task

    example_task(p1='1', p2='2').execute()


You can also send tasks in batch if latency is an issue and you have to send many small tasks to the queue
(limited to 1000 at a time):

.. code-block:: python

    from my_app.cloud_tasks import example_task
    from django_cloud_tasks.base import batch_execute

    tasks = []
    for i in range(0, 420):
        task = example_task(p1=i, p2=i)
        tasks.append(task)

    batch_execute(tasks)



It is also possible to run an actual function using ``run`` method of ``CloudTaskWrapper`` object instance that is returned after task is called (this can be useful for debugging):

.. code-block:: python

    task = example_task(p1=i, p2=i)
    task.run()


