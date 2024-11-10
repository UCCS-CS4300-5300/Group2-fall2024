from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views import generic
from django.utils.safestring import mark_safe
import calendar
from .models import *
from django.contrib.auth.models import User
from .utils import *
from .forms import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, forms
from django.contrib.auth.decorators import login_required
from guardian.decorators import permission_required_or_403
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse



# Create your views here.

def index(request):
    return render(request, 'index.html')

class CalendarView(generic.ListView):
    model = Event
    template_name = 'calendar.html'

    def dispatch(self, request, *args, **kwargs):
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
        context = super().get_context_data(**kwargs)

        # Get the current user from the request
        user_id = self.kwargs.get('user_id')
        
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

    if event_id:
        instance = get_object_or_404(Event, pk=event_id)
        if not request.user.has_perm('view_event', instance):
            messages.error(request, "You do not have permission to edit this event.")
            return HttpResponse(status=204)
            
    else:
        instance = Event()
    
    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        event = form.save(commit=False)
        event.user = request.user  # Assign the current user
        event.save()

        return HttpResponseRedirect(reverse('calendar',  args=[request.user.id]))
        
    return render(request, 'event.html', {'form': form})

# Function to return the detailed view of a specific event
def event_detail(request, event_id):
    
    event = get_object_or_404(Event, pk=event_id)

    owner = event.user

    # Check if a token-based session is set, allowing access regardless of authentication
    token_user_id = request.session.get('calendar_access_user_id')
    


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

    #sets the event based on the id from the url
    event = get_object_or_404(Event, pk=id)

    if request.user.has_perm('view_event', event):
        

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

    return redirect(reverse('event_detail', args=[id]))  # Redirect to a list of games or wherever

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
    

    if request.method == 'POST':
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

################ logout ################################################### 

def CustomLogoutView(self, request):
        logout(request)  # Log the user out
        return redirect("index")  # Redirect to the home page or your desired URL

@login_required
def friends(request):
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
                    from_user=request.user, to_user=user, accepted=False
                ).exists()

                status = 'Send Friend Request'
                if is_friend:
                    status = 'Already Friends'
                elif has_pending_request:
                    status = 'Request Sent'

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
def send_friend_request(request, user_id):
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
    # Get all friend requests that are sent to the current user and not accepted
    pending_requests = FriendRequest.objects.filter(to_user=request.user, accepted=False)

    return render(request, 'social.html', {'pending_requests': pending_requests})

@login_required
def ajax_friend_requests(request):
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
def delete_friend(request, user_id):
    try:
        user = request.user
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
def generate_calendar_link(request, user_id):
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
    token = request.GET.get('token')
    user_id = request.GET.get('user_id')

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
