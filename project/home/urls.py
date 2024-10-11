from django.urls import path, re_path
from .views import *
from . import views, Login, Register
from django.contrib.auth import views as auth

urlpatterns = [
    path('', index, name='index'),
    path('login/',  Login, name ='login'),
    #path('logout/', auth.LogoutView.as_view(template_name ='logout.html'), name ='logout'),
    path('register/', Register, name ='register'),
    path('calendar', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
]
