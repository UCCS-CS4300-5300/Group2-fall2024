from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
import calendar
from .models import *
from django.contrib.auth.models import User
from .utils import Calendar
from .forms import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from guardian.decorators import permission_required_or_403
from django.core.exceptions import PermissionDenied
from django.utils import timezone
 



# Create your views here.

def index(request):
    return render(request, 'index.html')

class CalendarView(generic.ListView):
    model = Event
    template_name = 'calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the current user from the request
        user_id = self.request.user.id

        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))

        # Get user-specific information about theme
        current_theme = self.request.COOKIES.get('theme', 'light')  # Default to 'light'

        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(user_id=user_id, withyear=True) 
        context['calendar'] = mark_safe(html_cal)
        # Get adjacent months
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)

        #add theme
        context['current_theme'] = current_theme

        return context

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


def event(request, event_id=None):
    instance = Event()
    if event_id:
        instance = get_object_or_404(Event, pk=event_id)

    form = EventForm(request.POST or None, instance=instance)
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
                    recurrence_end = timezone.make_aware(datetime.combine(recurrence_end, datetime.min.time()))
                if timezone.is_naive(recurrence_end):
                    recurrence_end = timezone.make_aware(recurrence_end)

            # Loop to create recurring events
            while True:
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

                # Stop if we reach the end of recurrence
                if recurrence_end and current_start > recurrence_end:
                    break

        return redirect('calendar', user_id=request.user.id)

    return render(request, 'event.html', {'form': form, 'event_id': event_id})

# Function to return the detailed view of a specific event
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.user.has_perm('view_event', event):
        return render(request, 'event_detail.html', {'event': event})
    else:
        return HttpResponse(status=204)

@login_required(login_url = 'login')
#method to delete a event for a user
def deleteEvent(request, user_id, id):

    #sets the event based on the id from the url
    event = get_object_or_404(Event, pk=id)

    #check the method is as expected
    if request.method == 'POST':
        #delete the event using funtion delete()
        event.delete()
        # Redirect back to the Calend list page
        return redirect('calendar', user_id)

    #pass in the event into the dictionary 
    context = {'event': event}
    #go to delete template with this information
    return render(request, 'delete.html', context)

# Function to create a new game
def create_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('calendar', args=[request.user.id]))  # Redirect to a list of games or wherever
    else:
        form = GameForm()

    return render(request, 'create_game.html', {'form': form})
  
########### register here ##################################### 

def register(request):  
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
            messages.info(request, f'account done not exit plz sign in')
    form = AuthenticationForm()
    return render(request, 'login.html', {'form':form, 'title':'log in'})


################ Update Password################################################### 
@login_required
def update_account(request):
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
    password_form = CustomPasswordChangeForm(user=request.user)
    if request.method == 'POST':
        password_form = CustomPasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Prevents logout after password change
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('user_page')
    return render(request, 'update_password.html', {'password_form': password_form})

################ logout ################################################### 

def CustomLogoutView(self, request):
        logout(request)  # Log the user out
        return redirect("index")  # Redirect to the home page or your desired URL

@login_required(login_url = 'login')
def todo_list(request):
    current_date = timezone.localtime(timezone.now()).date()
    events = Event.objects.filter(user=request.user, start_time__date=current_date).order_by('game__name', '-priority')

    # Organize events by game
    games_with_events = {}

    for event in events:
        game = event.game  # This gives you the actual Game instance
        game_name = game.name if game else "No Game"
        if game_name not in games_with_events:
            games_with_events[game_name] = {
                'game': game,  # Pass the actual Game object here
                'events': []   # Create a list for events
            }
        games_with_events[game_name]['events'].append(event)
    
    context = {
        'games_with_events': games_with_events
    }

    return render(request, 'todo_list.html', context)
