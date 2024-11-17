"""
urls.py
This module defines the URL patterns for the Home application. It maps views and functionalities to their respective routes 
to ensure proper navigation and interaction within the application.
Routes included:
    - Authentication: Handles login, logout, registration, account updates, and password updates.
    - Calendar: Provides calendar views (monthly, weekly) and event management (create, edit, delete, detail view).
    - Games: Allows for game creation, editing, and association with events.
    - Friend Requests: Includes functionalities for sending, accepting, declining, and managing friend requests.
    - Calendar Sharing: Implements token-based calendar sharing and access.
    - Search: Provides endpoints for standard and AJAX-based user and friend searches.
    - Media: Configures media handling for image uploads during development.
Features:
    - Integrates Django's built-in authentication system.
    - Implements custom views for extended functionalities, such as custom logout and user registration.
    - Supports dynamic routes with user IDs, event IDs, and game IDs for specific operations.
Setup:
    - Uses Django's `path` and `re_path` utilities for URL mapping.
    - Includes static file handling for development environments using `settings.MEDIA_URL` and `settings.MEDIA_ROOT`.
Notes:
    - All AJAX endpoints are clearly labeled to distinguish them from standard views.
    - Routes are modular and intuitive to support easy navigation and future scalability.
"""

from django.urls import path, re_path, include
from . import views
from .views import *
from .forms import CustomPasswordChangeForm, CustomUserCreationForm, EventForm, Game, UsersForm
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth
from django.urls import path, re_path, include



urlpatterns = [
    path('', index, name='index'),
    # include home path on url to match our navbar route
    path('home', index, name='home'),
    
    #login/registration urls
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout/', CustomLogoutView, name='logout'),  # Use your custom logout view
    path('accounts/register/', register, name = "register"),
    path('accounts/profile/', views.userPage, name = "user_page"),
    path('accounts/update_password/', views.update_password, name = "update_password"),
    path('accounts/update_account/', views.update_account, name = "update_account"),
    
    path('calendar/<int:user_id>/', CalendarView.as_view(), name = 'calendar' ),
    re_path(r'^event/new/$', views.event, name='event_new'),
    re_path(r'^event/edit/(?P<event_id>\d+)/$', views.event, name='event_edit'),
    
    # Add URL path for the event detail view
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    # URl path for the create game view
    path('calendar/create_game/', views.create_game, name='create_game'),
    # URL for editing an existing game
    path('game/edit/<int:game_id>/', views.create_game, name='edit_game'), 
    #url for event deletion that takes in user id and recipe id
    path('event_delete/<int:user_id>/<int:id>', views.deleteEvent, name='delete_event'),
    path('todo-list/', views.todo_list, name='todo_list'),

    # Standard search page
    path('friends/', views.friends, name='friends'),  
    path('view_friends/', views.view_friends, name='view_friends'),
    path('ajax_view_friends/', views.ajax_view_friends, name='ajax_view_friends'), # AJAX friends endpoint
    path('search/', views.ajax_search, name='ajax_search'),  # AJAX search endpoint
    
    #path to generate link with token
    path('generate_calendar_link/', views.generate_calendar_link, name='generate_calendar_link'),
    #path to grant access based on token
    path('calendar/access/', views.calendar_access, name='view_shared_calendar'),

    #handling Friend requests
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('friend-requests/', views.view_friend_requests, name='view_friend_requests'),
    path('ajax/friend-requests/', views.ajax_friend_requests, name='ajax_friend_requests'),
    path('accept-friend-request/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-friend-request/', views.decline_friend_request, name='decline_friend_request'),
    
    path('delete_friend/', views.delete_friend, name='delete_friend'),
]

#stuff for image upload
if settings.DEBUG:
       urlpatterns += static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)