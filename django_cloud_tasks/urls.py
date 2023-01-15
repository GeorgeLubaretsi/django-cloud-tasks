from django.urls import path
from . import views

urlpatterns = [
    path('', views.run_task, name='run_task'),
]
