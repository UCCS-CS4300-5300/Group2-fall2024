from django.urls import path, re_path
from . import views
from .views import *
from django.contrib.auth import views as auth

urlpatterns = [
    path('', index, name='index'),
    # include home path on url to match our navbar route
    path('home', index, name='home'),

    path('login/',  views.login_view, name ='login'),
    path('logout/', views.logout_view, name ='logout'),
    path('register/', views.register_view, name ='register'),
    
    path('calendar/<int:user_id>', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
]
