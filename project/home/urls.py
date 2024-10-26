from django.urls import path, re_path, include
from . import views
from .views import *
from django.contrib.auth import views as auth
from .forms import *

urlpatterns = [
    path('', index, name='index'),
    # include home path on url to match our navbar route
    path('home', index, name='home'),
    
    #login/registration urls
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('accounts/register/', register, name = "register"),
    path('accounts/profile/', views.userPage, name = "user_page"),

    
    path('calendar/<int:user_id>', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
]
