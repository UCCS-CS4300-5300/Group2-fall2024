"""
views.py
Views for the Home application.
This module includes functionalities for:
- **User Authentication**:
    - Login, Logout, and Registration.
    - Password and account management.
- **Calendar Management**:
    - Monthly and Weekly Calendar Views.
    - Event creation, editing, deletion, and detailed view.
    - Handling recurring events and sharing calendars via tokens.
- **Friendship Management**:
    - Sending, accepting, declining, and deleting friend requests.
    - Viewing friends and managing friend lists.
- **AJAX Utilities**:
    - Dynamic user search.
    - Fetching and responding to friend requests asynchronously.
    - Generating and validating calendar sharing links.
Features:
    - Permission-based access control for events and calendars.
    - Token-based calendar sharing for secure access.
    - Rich event recurrence handling (daily, weekly, monthly).
    - Interactive to-do lists grouped by associated games.
    - Dynamic UI interactions using AJAX endpoints.
Classes:
    - `CalendarView`: Handles monthly calendar views with event rendering.
    - `CalendarViewWeek`: Extends `CalendarView` to handle weekly views.
Functions:
    - `index`: Home page displaying currently playing games.
    - `event`: Handles event creation and editing.
    - `event_detail`: Provides a detailed view of an event.
    - `deleteEvent`: Deletes events for authenticated users.
    - `create_game`: Handles game creation and editing.
    - `register`: User registration.
    - `Login`: User login.
    - `update_account`: User profile updates.
    - `update_password`: Handles password updates.
    - `friends`: Displays friend lists and search functionalities.
    - `ajax_search`: AJAX endpoint for user search.
    - `send_friend_request`: Sends a friend request.
    - `view_friend_requests`: Displays pending friend requests.
    - `accept_friend_request`: Accepts a friend request.
    - `decline_friend_request`: Declines a friend request.
    - `generate_calendar_link`: Generates a shareable calendar link.
    - `calendar_access`: Provides calendar access via token.
Notes:
    - Relies on models like `Event`, `Game`, `FriendRequest`, and `CalendarAccess`.
    - Utilizes custom forms such as `EventForm`, `GameForm`, and `CustomPasswordChangeForm`.
    - Includes utility methods for managing recurring events and navigation between calendar views.
Examples:
    - **Create an Event**:
        ```
        response = client.post(reverse('event_new'), {
            'title': 'New Event',
            'start_time': '2024-01-01T10:00',
            'end_time': '2024-01-01T11:00',
            'recurrence': 'daily',
        })
        ```
    - **Generate a Calendar Link**:
        ```
        share_link = generate_calendar_link(request)
        ```
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, forms, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse, QueryDict
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.test import TestCase
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views import generic
from guardian.decorators import permission_required_or_403
from collections import OrderedDict
from datetime import datetime, timedelta, date

from .models import Game, Event, FriendRequest, CalendarAccess
from .utils import Calendar, CalendarWeek
from .forms import CustomUserCreationForm, EventForm, GameForm, UsersForm, CustomPasswordChangeForm

import json
import calendar




# Create your views here.

def index(request):
    """
    Renders the home page with currently playing games for the authenticated user.
    If the user is logged in, it fetches the games associated with their events
    and displays them on the home page.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: The rendered home page.
    """
    # Gather games currently associated to user's events to display "currently playing" on the home page. 
    currently_playing_games = Game.objects.filter(events__user=request.user).distinct() if request.user.is_authenticated else None
    return render(request, 'index.html', {'currently_playing_games': currently_playing_games})

class CalendarView(generic.ListView):
    """
    Handles the monthly calendar view, displaying user events.
    Attributes:
        model (Event): The model used for retrieving event data.
        template_name (str): The template used for rendering the calendar view.
    """
    model = Event
    template_name = 'calendar.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Verifies access permissions before handling the request.
        Checks whether the user is authenticated, is the calendar owner, or is a friend
        of the calendar owner. Also supports token-based access for shared calendars.
        Args:
            request (HttpRequest): The incoming HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            HttpResponse: Redirects or processes the request.
        """
        user_id = self.kwargs.get('user_id')

        # Check if a token-based session is set, allowing access regardless of authentication
        token_user_id = self.request.session.get('calendar_access_user_id')
        
        if token_user_id == user_id:
                # Clear the token after access is granted
                #del self.request.session['calendar_access_user_id']
                # User is accessing calendar via token, no need to clear token yet
                pass
        
        # Allow access if the user is the owner or has a valid token
        elif not request.user.is_authenticated:
            
            return redirect('index')  # Redirect unauthenticated users without a token

        elif request.user.id != user_id:
            # Check if the user is a friend of the requested user
            is_friend = FriendRequest.objects.filter(
                (Q(from_user=request.user, to_user__id=user_id) |
                 Q(from_user__id=user_id, to_user=request.user)) &
                Q(accepted=True)
            ).exists()

            # If not a friend and not the owner, check token-based access
            if not is_friend:
                if token_user_id == user_id:
                    #del self.request.session['calendar_access_user_id']  # Clear token after use
                    pass
                else:
                    return redirect(reverse('calendar', args=[request.user.id]))  # Redirect if access denied

        # Proceed with the normal dispatch if everything is valid
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Prepares and provides context data for rendering the calendar view.
        Fetches user events for the specified month, theme preferences, and navigation links
        for adjacent months. Adds metadata about the calendar owner and friend permissions.
        Args:
            **kwargs: Additional keyword arguments.
        Returns:
            dict: Context data for the calendar template.
        """
        context = super().get_context_data(**kwargs)

        # Get the current user from the request
        user_id = self.kwargs.get('user_id')
        
        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))

        # Get user-specific information about theme
        current_theme = self.request.COOKIES.get('theme', 'light')  # Default to 'light'

        # Instantiate our calendar class with the specified year and month
        cal = Calendar(d.year, d.month)

        # Query for events relevant to the selected month, including recurring events from past months
        events = Event.objects.filter(
            Q(user_id=user_id),
            Q(start_time__year=d.year, start_time__month=d.month) |
            Q(recurrence__in=['daily', 'weekly', 'monthly'], start_time__date__lte=d)
        )

        # Generate the calendar HTML with events
        html_cal = cal.formatmonth(events=events, withyear=True)
        context['calendar'] = mark_safe(html_cal)

        # Get adjacent months for navigation
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)

        # Add theme
        context['current_theme'] = current_theme

        
        token_user_id = self.request.session.get('calendar_access_user_id')
        if not self.request.user.is_authenticated:
            context['is_friend_calendar'] = True
        elif token_user_id == user_id:
            #del self.request.session['calendar_access_user_id']  # Clear token after use
            context['is_friend_calendar'] = True
        else:
            #if not self:
            # Check if the calendar belongs to a friend (or self)
            context['is_friend_calendar'] = is_friend_calendar(self, user_id)
        

        context['owner'] = get_object_or_404(User, pk=user_id)

        return context

def get_date(req_day):
    """
    Parses a date string and returns the first day of the month.
    Args:
        req_day (str): Date string in the format 'YYYY-MM'.
    Returns:
        datetime.date: The first day of the specified month.
    """
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    """
    Calculates the previous month for navigation.
    Args:
        d (datetime.date): The current date.
    Returns:
        str: URL parameter for the previous month in the format 'month=YYYY-MM'.
    """
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    """
    Calculates the next month for navigation.
    Args:
        d (datetime.date): The current date.
    Returns:
        str: URL parameter for the next month in the format 'month=YYYY-MM'.
    """
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

########### create event ##################################### 
def get_last_day_of_month(year, month):
    """Return the last day of the specified month."""
    if month == 12:
        return 31
    else:
        return (datetime(year, month + 1, 1) - timedelta(days=1)).day
def is_friend_calendar(self, user_id):
    # Check if the user is trying to view a friend's calendar
    if self.request.user.id != user_id:
        # Check if the user_id belongs to a friend
        is_friend = FriendRequest.objects.filter(
            (Q(from_user=self.request.user, to_user__id=user_id) |
             Q(from_user__id=user_id, to_user=self.request.user)) &
            Q(accepted=True)
        ).exists()
        return is_friend


def event(request, event_id=None):
    """
    Handles the creation and editing of events.
    If an event ID is provided, it retrieves and updates the event. Otherwise,
    it creates a new event. Supports recurring events with automatic generation
    of future occurrences.
    Args:
        request (HttpRequest): The incoming HTTP request object.
        event_id (int, optional): ID of the event to edit. Defaults to None.
    Returns:
        HttpResponse: Redirects to the calendar view or renders the event form.
    """
    instance = Event()
    if event_id:
        instance = get_object_or_404(Event, pk=event_id)

    form = EventForm(request.POST or None, instance=instance, user=request.user)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.user = request.user  # Assign the current user
        event.save()

        # Handle recurrence for a single event
        recurrence_type = event.recurrence
        if recurrence_type != 'none':
            current_start = event.start_time
            current_end = event.end_time
            recurrence_end = form.cleaned_data.get('recurrence_end')

            # Ensure current_start and current_end are timezone-aware
            current_start = timezone.make_aware(current_start) if timezone.is_naive(current_start) else current_start
            current_end = timezone.make_aware(current_end) if timezone.is_naive(current_end) else current_end

            # Ensure recurrence_end is a datetime and timezone-aware for comparison
            if recurrence_end:
                if isinstance(recurrence_end, date) and not isinstance(recurrence_end, datetime):
                    recurrence_end = timezone.make_aware(datetime.combine(recurrence_end + timedelta(days=1), datetime.min.time()))
                if timezone.is_naive(recurrence_end):
                    recurrence_end = timezone.make_aware(recurrence_end)

            # Loop to create recurring events
            while True:
                if recurrence_end and current_start > recurrence_end:
                    break
                # Check if we should create a new event
                overlap_exists = Event.objects.filter(
                    user=event.user,
                    start_time__lt=current_end,
                    end_time__gt=current_start,
                ).exists()

                if not overlap_exists:
                    # Create a new event for the recurrence
                    new_event = Event(
                        user=event.user,
                        title=event.title,
                        description=event.description,
                        start_time=current_start,
                        end_time=current_end,
                        recurrence='none'  # Set recurrence to none for created events
                    )
                    new_event.save()

                # Update start and end times based on recurrence type
                if recurrence_type == 'daily':
                    current_start += timedelta(days=1)
                    current_end += timedelta(days=1)
                elif recurrence_type == 'weekly':
                    current_start += timedelta(weeks=1)
                    current_end += timedelta(weeks=1)
                elif recurrence_type == 'monthly':
                    # Move to the next month and ensure valid day
                    next_month = (current_start.month % 12) + 1
                    next_year = current_start.year + (current_start.month // 12)

                    # Get the last day of the next month
                    last_day_next_month = get_last_day_of_month(next_year, next_month)

                    # Adjust the current day if it exceeds the last day of the next month
                    current_day = current_start.day
                    if current_day > last_day_next_month:
                        current_day = last_day_next_month
                    
                    current_start = current_start.replace(year=next_year, month=next_month, day=current_day)
                    current_end = current_end.replace(year=next_year, month=next_month, day=current_day)


        return redirect('calendar', user_id=request.user.id)

    return render(request, 'event.html', {'form': form, 'event_id': event_id})

# Function to return the detailed view of a specific event
def event_detail(request, event_id):
    
    event = get_object_or_404(Event, pk=event_id)

    owner = event.user

    # Check if a token-based session is set, allowing access regardless of authentication
    token_user_id = request.session.get('calendar_access_user_id')
    
    is_friend = False

    if token_user_id == owner.id:
        #del self.request.session['calendar_access_user_id']  # Clear token after use
        is_friend = True
    elif request.user.id != owner.id:
        # Check if the user_id belongs to a friend
        is_friend = FriendRequest.objects.filter(
            (Q(from_user=request.user, to_user__id=owner.id) |
            Q(from_user__id=owner.id, to_user=request.user)) &
            Q(accepted=True)
        ).exists()

    if request.user.has_perm('view_event', event) | is_friend:
        return render(request, 'event_detail.html', {'event': event, 'is_friend':is_friend, 'owner':owner})
    else:
        return HttpResponse(status=204)

@login_required(login_url = 'login')
#method to delete a event for a user
def deleteEvent(request, user_id, id):
    """
    Deletes an event for the specified user.

    Redirect unauthorized users with an appropriate error message.
    """

    #sets the event based on the id from the url
    event = get_object_or_404(Event, pk=id)

    # Check if the current user has permission to delete the event
    if request.user != event.user:
        messages.error(request, "You don't have permission to delete this event.")
        return redirect('calendar', user_id)  # Redirect unauthorized users to the calendar

    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully.")
        return redirect('calendar', user_id)
    
    context = {'event': event}
    return render(request, 'delete.html', context)


# Function to create a new game or edit exisiting
@login_required
def create_game(request, game_id=None):
    """
    Handles the creation and editing of games.
    If a game ID is provided, it retrieves and updates the game. Otherwise,
    it creates a new game.
    Args:
        request (HttpRequest): The incoming HTTP request object.
        game_id (int, optional): ID of the game to edit. Defaults to None.

    Returns:
        HttpResponse: Redirects to the calendar view or renders the game form.
    """

    # Retrieve the game instance if editing, or create a new one if game_id is None
    game = get_object_or_404(Game, id=game_id, user=request.user) if game_id else None

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES, instance=game)
        if form.is_valid():
            game = form.save(commit=False)
            game.user = request.user
            game.save()
            return redirect(reverse('calendar', args=[request.user.id]))  # Redirect to the calendar
    else:
        form = GameForm(instance=game)

    return render(request, 'create_game.html', {'form': form})
  
########### register here ##################################### 

def register(request):
    """
    Handles user registration.
    Displays a registration form and creates a new user upon form submission.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the login page or renders the registration form.
    """  
    if request.method == 'POST':  
        form = CustomUserCreationForm(request.POST)  
        if form.is_valid():  
            
            user = form.save()  
            messages.success(request, 'Your account has been created successfully!')
            return redirect("login")
    else:  
        form = CustomUserCreationForm()  
    context = {  
        'form':form  
    }  
    return render(request, 'registration/register.html', context)  

################ user page ################################################### 
@login_required(login_url = 'login')
def userPage(request):
    user_id = request.user.id
    
    user = User.objects.get(id=user_id)
    form = UsersForm(instance = user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST' and 'password_form' not in request.POST:
        form = UsersForm(request.POST, request.FILES, instance = user)
        if form.is_valid():
            
            form.save()
            messages.success(request, 'Your account has been updated successfully!')
            return redirect("index")
    
    context = {'user':user,'form':form}
    return render(request, 'user.html', context)

    ################ login forms################################################### 
def Login(request):
    """
    Handles user login.
    Authenticates the user and logs them in upon valid credentials.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the home page or renders the login form.
    """
    if request.method == 'POST':
  
        # AuthenticationForm_can_also_be_used__
  
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        if user is not None:
            form = login(request, user)
            messages.success(request, f' welcome {username} !!')
            return redirect('index')
        else:
            messages.info(request, f'Please enter a correct username and password. Note that both fields may be case-sensitive.')
    form = AuthenticationForm()
    return render(request, 'login.html', {'form':form, 'title':'log in'})


################ Update Password################################################### 
@login_required
def update_account(request):
    """
    Handles user account updates.
    Displays a form pre-filled with the user's current details and allows 
    updates to their profile information. 
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the user profile page or renders the update form.
    """
    user_form = UsersForm(instance=request.user)
    if request.method == 'POST':
        user_form = UsersForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your account has been updated successfully!.')
            return redirect('user_page')
    return render(request, 'update_account.html', {'user_form': user_form})

@login_required
def update_password(request):
    """
    Handles user password updates.
    Displays a password change form and updates the user's password upon valid input.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the user profile page or renders the password update form.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Keeps the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user_page')  # Redirect to the user profile page after successful update
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'update_password.html', {'password_form': form})

################ logout ################################################### 

def CustomLogoutView(self, request):
    """
    Logs out the user and redirects to the home page.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the home page.
    """
    logout(request)  # Log the user out
    return redirect("index")  # Redirect to the home page or your desired URL


@login_required(login_url='login')
def todo_list(request):
    """
    Displays a to-do list of events for the current day.
    Groups events by associated game and organizes them by the earliest 
    start time and highest priority.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: The rendered to-do list template with event data.
    """
    current_date = timezone.localtime(timezone.now()).date()
    events = Event.objects.filter(user=request.user, start_time__date=current_date).order_by('game__name', 'start_time', '-priority')

    # Organize events by game and track the earliest start time and highest priority for sorting
    games_with_events = {}

    for event in events:
        game = event.game  # Get the Game instance associated with the event
        game_name = game.name if game else "No Game"
        
        if game_name not in games_with_events:
            games_with_events[game_name] = {
                'game': game,          # Store the actual Game object
                'events': [],          # List to hold events for this game
                'earliest_start': event.start_time,  # Track the earliest start time in this game
                'highest_priority': event.priority   # Track the highest priority in this game
            }
        
        # Add the event to the list of events for this game
        games_with_events[game_name]['events'].append(event)
        
        # Update the earliest start time for the game if this event is earlier
        if event.start_time < games_with_events[game_name]['earliest_start']:
            games_with_events[game_name]['earliest_start'] = event.start_time
        
        # Update the highest priority for the game if this event has a higher priority
        if event.priority > games_with_events[game_name]['highest_priority']:
            games_with_events[game_name]['highest_priority'] = event.priority

    # Sort games by earliest start time (primary) and highest priority (secondary), with higher priority first
    sorted_games_with_events = OrderedDict(
        sorted(
            games_with_events.items(),
            key=lambda x: (x[1]['earliest_start'], -x[1]['highest_priority'])
        )
    )

    context = {
        'games_with_events': sorted_games_with_events
    }

    return render(request, 'todo_list.html', context)

@login_required
def friends(request):
    """
    Displays a list of users for searching and sending friend requests.
    Handles user search queries submitted via POST.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: The rendered social view with search results.
    """
    # Initialize the list of users to be empty
    users = []
    
    # Handle POST request (when searching)
    if request.method == 'POST':
        query = request.POST.get('query', '')
        if query:
            users = User.objects.filter(username__icontains=query)  # Filter users by search term
    
    return render(request, 'social.html', {'users': users})  # Render the template with the results

@login_required
def ajax_search(request):
    """
    Handles AJAX requests for searching users.
    Returns a JSON response with a list of users and their friendship status
    relative to the logged-in user.
    Args:
        request (HttpRequest): The incoming AJAX request object.
    Returns:
        JsonResponse: A JSON object containing user search results and statuses.
    """
    try:
        query = request.GET.get('query', '').strip()
        results = []
        if query:
            users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
            for user in users:
                # Check friendship status
                is_friend = FriendRequest.objects.filter(
                    Q(from_user=request.user, to_user=user) | Q(from_user=user, to_user=request.user),
                    accepted=True
                ).exists()

                # Check if a pending friend request exists
                has_pending_request = FriendRequest.objects.filter(
                    Q(from_user=request.user, to_user=user) | Q(from_user=user, to_user=request.user), accepted=False
                ).exists()

                status = 'Send Friend Request'
                if is_friend:
                    status = 'Already Friends'
                elif has_pending_request:
                    status = 'Request Pending'

                results.append({
                    'username': user.username,
                    'user_id': user.id,
                    'status': status  # Send status to the frontend
                })

        return JsonResponse(results, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)  # Return error details in response

@login_required
# View to handle sending friend requests
def send_friend_request(request):
    """
    Sends a friend request to another user.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        JsonResponse: A success or error message.
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            to_user = User.objects.get(id=user_id)
            # Ensure user is not sending a request to themselves
            if to_user != request.user:
                # Create a friend request instance
                from_user = request.user

                # Check if a friend request already exists between these users
                existing_request = FriendRequest.objects.filter(
                    from_user=from_user,
                    to_user=to_user,
                    accepted=False
                ).exists()

                # Check if they are already friends
                are_already_friends = FriendRequest.objects.filter(
                    (Q(from_user=from_user) & Q(to_user=to_user)) |
                    (Q(from_user=to_user) & Q(to_user=from_user)),
                    accepted=True
                ).exists()
                
                if existing_request:
                    return JsonResponse({'success': False, 'message': 'Friend request already sent.'}, status=400)
        
                if are_already_friends:
                    return JsonResponse({'success': False, 'message': 'You are already friends.'}, status=400)

                friend_request = FriendRequest(from_user=from_user, to_user=to_user)
                friend_request.save()
                return JsonResponse({'message': 'Friend request sent successfully!'})
            else:
                return JsonResponse({'message': 'You cannot send a friend request to yourself.'})
        return JsonResponse({'message': 'Invalid user ID.'})
    return JsonResponse({'message': 'Invalid request method.'})

@login_required
def view_friend_requests(request):
    """
    Displays all pending friend requests for the logged-in user.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: The rendered friend request view.
    """
    # Get all friend requests that are sent to the current user and not accepted
    pending_requests = FriendRequest.objects.filter(to_user=request.user, accepted=False)

    return render(request, 'social.html', {'pending_requests': pending_requests})

@login_required
def ajax_friend_requests(request):
    """
    Handles AJAX requests to fetch pending friend requests.
    Returns a JSON response with details about the pending requests for the logged-in user.
    Args:
        request (HttpRequest): The incoming AJAX request object.
    Returns:
        JsonResponse: A JSON object containing a list of pending friend requests.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Retrieve friend requests for the logged-in user
        friend_requests = FriendRequest.objects.filter(to_user=request.user, accepted=False)

        # Format the friend requests as JSON data
        data = {
            'requests': [
                {
                    'request_id': fr.id,
                    'from_user': fr.from_user.username,
                    'created_at': fr.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for fr in friend_requests
            ]
        }

        # Return the JSON response with the 'requests' key
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def accept_friend_request(request):
    """
    Accepts a friend request sent to the logged-in user.
    Marks the request as accepted and adds the sender to the user's friend list.

    Args:
        request (HttpRequest): The incoming AJAX POST request object.

    Returns:
        JsonResponse: A JSON object indicating success or failure.
    """


    if request.method == 'POST':
        
        try:
            # Get the friend request by ID (passed via POST)
            friend_request_id = request.POST.get('request_id')

            # Validate request_id
            if not friend_request_id:
                return JsonResponse({'success': False, 'error': 'Request ID is missing'}, status=400)
           
            friend_request = get_object_or_404(FriendRequest, id=friend_request_id)

            

            # Ensure that the request is for the current user (security check)
            if friend_request.to_user != request.user:
                return JsonResponse({'error': 'You are not authorized to accept this request.'}, status=403)

            

            # Update the 'accepted' field to True
            friend_request.accepted = True
            friend_request.save()

            # Optionally, return a success message or the updated data
            return JsonResponse({'success' : True , 'message':'Friend request accepted successfully.'})
        
        except FriendRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Friend request not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def decline_friend_request(request):
    """
    Declines a friend request sent to the logged-in user.
    Deletes the friend request without adding the sender to the user's friend list.
    Args:
        request (HttpRequest): The incoming AJAX POST request object.
    Returns:
        JsonResponse: A JSON object indicating success or failure.
    """
    if request.method == 'POST':
        
        try:
            # Get the friend request by ID (passed via POST)
            friend_request_id = request.POST.get('request_id')

            

            # Validate request_id
            if not friend_request_id:
                return JsonResponse({'success': False, 'error': 'Request ID is missing'}, status=400)
           
            friend_request = get_object_or_404(FriendRequest, id=friend_request_id)

            print(friend_request)

            # Ensure that the request is for the current user (security check)
            if friend_request.to_user != request.user:
                return JsonResponse({'error': 'You are not authorized to accept this request.'}, status=403)


            
            # delete the FriendRequest
            friend_request.delete()

            # Optionally, return a success message or the updated data
            return JsonResponse({'success' : True , 'message':'Friend request declined successfully.'})
        
        except FriendRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Friend request not found'}, status=404)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

    return JsonResponse({'success': False}, status=400)

@login_required
def ajax_view_friends(request):
    user = request.user

    # Fetch all accepted friend requests for the current user
    friends = FriendRequest.objects.filter(
        (Q(from_user=user) | Q(to_user=user)),
        accepted=True
    )

    # Get the unique friends by filtering based on the related users in the requests
    friends_list = []
    for fr in friends:
        if fr.from_user != user:
            friends_list.append(fr.from_user)
        else:
            friends_list.append(fr.to_user)
    
    data = {
        'friends': [

            {
                'username': fr.username,
                'user_id': fr.id

            }
            for fr in friends_list
            
        ]
    
    }
    return JsonResponse(data)
    
@login_required
def view_friends(request):
    """
    Displays a list of the user's current friends.
    Fetches accepted friend requests and lists the associated users.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: The rendered friends list template.
    """
    user = request.user

    # Fetch all accepted friend requests for the current user
    friends = FriendRequest.objects.filter(
        (Q(from_user=user) | Q(to_user=user)),
        accepted=True
    )

    # Get the unique friends by filtering based on the related users in the requests
    friends_list = []
    for fr in friends:
        if fr.from_user != user:
            friends_list.append(fr.from_user)
        else:
            friends_list.append(fr.to_user)

    return render(request, 'social.html', {'friends': friends_list})

@login_required
def delete_friend(request):
    """
    Deletes a friend from the user's friend list.
    Checks for an existing friendship and removes it upon confirmation.
    Args:
        request (HttpRequest): The incoming AJAX request object.
    Returns:
        JsonResponse: A JSON object indicating success or failure.
    """
    try:
        
        user = request.user

        data = json.loads(request.body)
        #data = QueryDict(request.body)
        
        user_id = data.get('friend_id')
        
        friend = User.objects.get(id=user_id)

        # Check if they are friends (i.e., there exists an accepted FriendRequest)
        friend_request = FriendRequest.objects.filter(
            (Q(from_user=user) & Q(to_user=friend)) | 
            (Q(from_user=friend) & Q(to_user=user)),
            accepted=True
        )

        

        if friend_request.exists():
            # Update the 'accepted' field to False
            #friend_request.accepted = False
            #friend_request.save()
            # Delete the friendship by deleting the FriendRequest
            friend_request.delete()

            return JsonResponse({'success': True, 'status': 'Send Friend Request', 'message': 'Friend deleted successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'No friendship found.'}, status=400)

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)

@login_required
def generate_calendar_link(request):
    """
    Generates a unique, shareable link for the user's calendar.
    Allows the logged-in user to share their calendar with others via a unique token.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        JsonResponse: A JSON object containing the shareable link or an error message.
    """
    user_id = request.GET.get('owner_id')
    user = User.objects.get(id=user_id)
    
    # Ensure the logged-in user is generating the link for their own calendar
    if user != request.user:
        return JsonResponse({'success': False, 'message': 'You are not authorized to share this calendar.'})
    
    # Create a CalendarAccess instance to generate a unique token for sharing the calendar
    calendar_access = CalendarAccess.objects.create(user=user)
    share_link = f"{request.build_absolute_uri('/calendar/access/')}?token={calendar_access.token}"

    # Return the shareable link as part of the response
    return JsonResponse({'success': True, 'share_link': share_link})

def calendar_access(request):
    """
    Handles access to a shared calendar via a unique token.
    Sets a session variable to grant access and redirects to the calendar view.
    Args:
        request (HttpRequest): The incoming HTTP request object.
    Returns:
        HttpResponse: Redirects to the calendar view for the owner of the token.
    """
    token = request.GET.get('token')
    

    if not token:
        raise Http404("Token not provided")

    try:
        calendar_access = CalendarAccess.objects.get(token=token)
    except CalendarAccess.DoesNotExist:
        raise Http404("Invalid or expired token")


    # Set a session variable indicating access for this specific user
    request.session['calendar_access_user_id'] = calendar_access.user.id

    # Redirect to CalendarView with the owner's user_id
    return redirect('calendar', user_id=calendar_access.user.id)


