from django.urls import path, re_path
from .views import *
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('calendar', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
]
