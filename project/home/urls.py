from django.urls import path, re_path, include
from . import views
from .views import *
from django.contrib.auth import views as auth
from .forms import *
from django.conf import settings




urlpatterns = [
    path('', index, name='index'),
    # include home path on url to match our navbar route
    path('home', index, name='home'),
    
    #login/registration urls
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout/', CustomLogoutView, name='logout'),  # Use your custom logout view
    path('accounts/register/', register, name = "register"),
    path('accounts/profile/', views.userPage, name = "user_page"),

    
    path('calendar/<int:user_id>/', CalendarView.as_view(), name = 'calendar' ),
    #path('calendar/<token>/', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
    
    # Add URL path for the event detail view
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    # URl path for the create game view
    path('calendar/create_game/', views.create_game, name='create_game'),
    #url for event deletion that takes in user id and recipe id
    path('event_delete/<int:user_id>/<int:id>', views.deleteEvent, name='delete_event'),

  
    path('friends/', views.friends, name='friends'),  # Standard search page
    path('view_friends/', views.view_friends, name='view_friends'),
    path('ajax_view_friends/', views.ajax_view_friends, name='ajax_view_friends'),
    path('search/', views.ajax_search, name='ajax_search'),  # AJAX search endpoint
    
    path('calendar/view/<int:user_id>/', CalendarView.as_view(), name='view_friend_calendar'),

    path('send_friend_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-requests/', views.view_friend_requests, name='view_friend_requests'),
    path('ajax/friend-requests/', views.ajax_friend_requests, name='ajax_friend_requests'),
    path('accept-friend-request/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-friend-request/', views.decline_friend_request, name='decline_friend_request'),
    
    path('delete_friend/<int:user_id>/', views.delete_friend, name='delete_friend'),
]
