from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from home.models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json

"""
# Create your tests here.

#============== UNIT TEST=================#
class ViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user for login tests
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    # Test the index view
    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    # Test the login view with invalid credentials
    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'invaliduser',
            'password': 'wrongpassword',
        })
        self.assertContains(response, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')  # Check for the specific error message

    # Test the login view with valid credentials
    def test_login_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect after successful login
        self.assertRedirects(response, reverse('index'))



class UserCreationTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_user_registration(self):
        # Test user registration
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password1': 'saphire1',
            'password2': 'saphire1',
            'email': 'testuser@example.com'
        })
        # Check redirect after registration
        self.assertRedirects(response, reverse('login'))
        
        # Confirm user is created
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)


class EventTests(TestCase):

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create an event
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time='2024-01-01 10:00:00',
            end_time='2024-01-01 11:00:00',
            user=self.user
        )

    def test_create_event(self):
        # Test creating an event
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        response = self.client.post(reverse('event_new'), {
            'title': 'Test Event',
            'description': 'This is a test event.',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'user': self.user.id  # Ensure the user is linked to the event
        })

        # Confirm redirect to calendar after event creation
        self.assertRedirects(response, reverse('calendar', args=[self.user.id]))  # Include user ID here

        # Confirm event is created
        event_exists = Event.objects.filter(title='Test Event', user=self.user).exists()
        self.assertTrue(event_exists)

    def test_calendar_view(self):
        # Test access to calendar view
        response = self.client.get(reverse('calendar', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_edit_event(self):
        # URL for editing the event
        url = reverse('event_edit', args=[self.event.id])
        
        # Make a POST request to update the event
        response = self.client.post(url, {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'start_time': '2024-01-01 12:00:00',
            'end_time': '2024-01-01 13:00:00'
        })

        # Check if the response is a redirect (302)
        self.assertEqual(response.status_code, 302)

        # Fetch the updated event from the database
        updated_event = Event.objects.get(id=self.event.id)
        self.assertEqual(updated_event.title, 'Updated Event')
"""
class FriendRequestTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')

    def test_send_friend_request(self):
        self.client.login(username='user1', password='testpass123')  # Ensure user1 is logged in
        

        # create friend request from user to user2
        # Send POST request with correct data
        response = self.client.post(reverse('send_friend_request'), {
            'user_id': self.user2.id  # Pass request_id instead of user IDs
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Retrieve friend request
        friend_request = FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2).first()
        self.assertIsNotNone(friend_request)
        self.assertEqual(friend_request.from_user, self.user1)
        self.assertEqual(friend_request.to_user, self.user2)

    def test_accept_friend_request(self):
        # create friend request from user to user2
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        
        # Log in as the receiving user (to_user)
        self.client.login(username='user2', password='testpass123')

        # Send POST request with correct data
        response = self.client.post(reverse('accept_friend_request'), {
            'request_id': friend_request.id  # Pass request_id instead of user IDs
        })

        # Check if the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Refresh the friend request from the database and check if accepted
        friend_request.refresh_from_db()
        self.assertTrue(friend_request.accepted)

    def test_get_friends(self):
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)
        friends = friend_request.friends
        self.assertIn(self.user2, friends)

    def test_delete_friends(self):
        # create friend request from user to user2 that has been accepted
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)

        # Log in as the receiving user (to_user)
        self.client.login(username='user2', password='testpass123')

        # Send DELETE request with correct data
        response = self.client.generic('DELETE', reverse('delete_friend'), json.dumps({
            'friend_id': self.user1.id
        }), content_type='application/json')

        # Check if the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Refresh the friend request from the database and check if accepted
        is_friends = FriendRequest.objects.filter(
                (Q(from_user=self.user1.id, to_user__id=self.user2.id) |
                 Q(from_user__id=self.user2.id, to_user=self.user1.id)) &
                Q(accepted=True)
                ).exists()
        
        self.assertTrue(not is_friends)


#this test token creation and usage
class CalendarAccessTests(TestCase):
    #create fake user
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    #test token creation
    def test_create_calendar_access(self):
        
        access = CalendarAccess.objects.create(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    #use the token to retrieval from database 
    def test_calendar_access_retrieval(self):
        access = CalendarAccess.objects.create(user=self.user)
        retrieved_access = CalendarAccess.objects.get(token=access.token)
        self.assertEqual(retrieved_access, access)

    #test link creation by user
    def test_link_creation(self):
        login = self.client.login(username='testuser', password='testpass123')  # Ensure user1 is logged in

        # Send GET request with correct data
        response = self.client.get(reverse('generate_calendar_link'), {
            'owner_id': self.user.id  # Pass owner id of calendar instead of user IDs
        })

        # Check if the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        
        
        access = CalendarAccess.objects.get(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    #test link usage by user
    def test_link_usage(self):
        access = CalendarAccess.objects.create(user=self.user)

        #share_link = f"{self.build_absolute_uri('/calendar/access/')}?token={access.token}"

        # Send GET request with correct data
        response = self.client.get(reverse('view_shared_calendar'), {
            'token': access.token,  # Pass owner id of calendar instead of user IDs
        })


        # Check if the response status is 302 because it will redirect to the owner's calendar otherwise 404
        self.assertEqual(response.status_code, 302)
        

    

