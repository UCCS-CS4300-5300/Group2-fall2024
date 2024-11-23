"""
tests.py

This module contains comprehensive unit and integration tests for the Home application. The tests are designed to verify the 
functionality, edge cases, and reliability of the application. 

Tests included:
    - User authentication (e.g., login, registration, password update).
    - Event management (e.g., creation, editing, deletion, and recurrence handling).
    - Calendar functionalities (e.g., calendar view, sharing, and token-based access).
    - Friend request management (e.g., sending, accepting, and removing friends).
    - Game management (e.g., creating and associating games with events).

Features:
    - Ensures proper view rendering and template usage.
    - Verifies form validation and error handling.
    - Validates model interactions, relationships, and properties.
    - Tests asynchronous and token-based functionalities, such as calendar sharing.

Setup:
    - Each test uses Django's TestCase class, which provides database isolation for test reliability.
    - Test data is set up in the `setUp` method for each test case.
    - Tear down happens automatically to ensure no residual data affects other tests.
"""

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.test import TestCase, Client
from home.models import Event, Game, FriendRequest, CalendarAccess
from datetime import datetime, timedelta
from uuid import uuid4
from .forms import CustomUserCreationForm, EventForm, GameForm
import json






# ======================= UNIT TESTS ======================= #

class ViewsTestCase(TestCase):
    """
    Tests for the basic views in the application, such as index and login.
    """
    def setUp(self):
        # Create a test user for login tests
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_index_view(self):
        """
        Test the index view for proper response and template usage.
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_login_invalid_credentials(self):
        """
        Test login functionality with invalid credentials.
        """
        response = self.client.post(reverse('login'), {
            'username': 'invaliduser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        error_message = str(response.context['form'].errors.get('__all__'))
        self.assertIn('Please enter a correct username and password', error_message)

    def test_login_valid_credentials(self):
        """
        Test login functionality with valid credentials.
        """
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect after successful login
        self.assertRedirects(response, reverse('index'))


class UserCreationTests(TestCase):
    """
    Tests for user registration and creation functionalities.
    """
    def setUp(self):
        self.client = Client()

    def test_user_registration(self):
        """
        Test the user registration process and ensure successful user creation.
        """
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password1': 'saphire1',
            'password2': 'saphire1',
            'email': 'testuser@example.com'
        })
        self.assertRedirects(response, reverse('login'))
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)


class EventTests(TestCase):
    """
    Tests for event creation, editing, and calendar views.
    """
    def setUp(self):
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
        """
        Test the event creation process.
        """
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        form_data = {
            'title': 'Test Event',
            'description': 'This is a test event.',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'recurrence': 'none',
            'priority': 2,
        }

        response = self.client.post(reverse('event_new'), form_data)
        self.assertRedirects(response, reverse('calendar', args=[self.user.id]))

    def test_calendar_view(self):
        """
        Test access to the calendar view for the logged-in user.
        """
        response = self.client.get(reverse('calendar', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_edit_event(self):
        """
        Test editing an existing event.
        """
        url = reverse('event_edit', args=[self.event.id])
        response = self.client.post(url, {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'start_time': '2024-01-01T12:00',
            'end_time': '2024-01-01T13:00',
            'recurrence': 'none',
            'priority': 2
        })
        self.assertEqual(response.status_code, 302)


class EventDeletionTests(TestCase):
    """
    Tests for deleting events.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            user=self.user
        )

    def test_delete_event(self):
        """
        Test the deletion of an event.
        """
        response = self.client.post(reverse('delete_event', args=[self.user.id, self.event.id]))
        self.assertEqual(response.status_code, 302)
        event_exists = Event.objects.filter(id=self.event.id).exists()
        self.assertFalse(event_exists)


class FriendRequestTests(TestCase):
    """
    Tests for sending, accepting, and deleting friend requests.
    """
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')

    def test_send_friend_request(self):
        """
        Test sending a friend request from one user to another.
        """
        self.client.login(username='user1', password='testpass123')
        response = self.client.post(reverse('send_friend_request'), {
            'user_id': self.user2.id
        })
        self.assertEqual(response.status_code, 200)
        friend_request = FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2).exists()
        self.assertTrue(friend_request)

    def test_accept_friend_request(self):
        """
        Test accepting a friend request.
        """
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        self.client.login(username='user2', password='testpass123')
        response = self.client.post(reverse('accept_friend_request'), {
            'request_id': friend_request.id
        })
        self.assertEqual(response.status_code, 200)
        friend_request.refresh_from_db()
        self.assertTrue(friend_request.accepted)

class CalendarAccessTests(TestCase):
    """
    Tests for calendar sharing and access functionalities using tokens.
    """
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_create_calendar_access(self):
        """
        Test the creation of a calendar access token for a user.
        """
        access = CalendarAccess.objects.create(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    def test_calendar_access_retrieval(self):
        """
        Test retrieving a calendar access object using its token.
        """
        access = CalendarAccess.objects.create(user=self.user)
        retrieved_access = CalendarAccess.objects.get(token=access.token)
        self.assertEqual(retrieved_access, access)

    def test_link_creation(self):
        """
        Test generating a shareable calendar link.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('generate_calendar_link'), {'owner_id': self.user.id})
        self.assertEqual(response.status_code, 200)
        access = CalendarAccess.objects.get(user=self.user)
        self.assertIsNotNone(access.token)

    def test_link_usage(self):
        """
        Test using a calendar sharing link (via token) to access a user's calendar.
        """
        access = CalendarAccess.objects.create(user=self.user)
        response = self.client.get(reverse('view_shared_calendar'), {'token': access.token})
        self.assertEqual(response.status_code, 302)  # Expect redirect to the owner's calendar


class GameCreationTests(TestCase):
    """
    Tests for game creation functionality.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_create_game_view(self):
        """
        Test the creation of a new game.
        """
        form_data = {
            'name': 'New Game',
            'color': '#FF5733',  # Valid color choice
            'platform': '',       # Optional field
            'developer': '',      # Optional field
            'release_date': '',   # Optional field
            'genre': '',          # Optional field
            'picture_link': '',   # Optional field
        }
        response = self.client.post(reverse('create_game'), form_data)
        if response.status_code == 200:
            print(response.context.get('form').errors)  # Debugging line
        self.assertRedirects(response, reverse('calendar', args=[self.user.id]))


class RecurringEventTests(TestCase):
    """
    Tests for recurring event creation functionalities.
    """
    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        # Create a recurring event
        self.event = Event.objects.create(
            title='Test Recurring Event',
            description='Test Description',
            start_time=timezone.make_aware(datetime(2024, 1, 1, 10, 0, 0)),
            end_time=timezone.make_aware(datetime(2024, 1, 1, 11, 0, 0)),
            user=self.user,
            recurrence='daily',
            recurrence_end=datetime(2024, 1, 10)
        )

    def test_daily_recurring_event_creation(self):
        """
        Test the creation of daily recurring events.
        """
        start_time = timezone.make_aware(datetime(2024, 1, 1, 10, 0))
        end_time = timezone.make_aware(datetime(2024, 1, 1, 11, 0))

        response = self.client.post(reverse('event_new'), {
            'title': 'Test Daily Recurring Event',
            'description': 'Test Description',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'recurrence': 'daily',
            'recurrence_end': '2024-01-10',  # Set the correct end date
            'priority': 2,
        })

        # Calculate expected count
        recurrence_start_date = start_time.date()
        recurrence_end_date = datetime.strptime('2024-01-10', '%Y-%m-%d').date()
        expected_count = (recurrence_end_date - recurrence_start_date).days + 1  # Include both start and end dates

        # Check that the number of created events matches the expected count
        event_count = Event.objects.filter(title='Test Daily Recurring Event').count()
        created_events = Event.objects.filter(title='Test Daily Recurring Event').order_by('start_time')
        # print("Created Events:")
        # for event in created_events:
        #     print(f"Event Start: {event.start_time}, Event End: {event.end_time}")

        self.assertEqual(event_count, expected_count)

    def test_weekly_recurring_event_creation(self):
        """
        Test the creation of weekly recurring events.
        """
        start_time = timezone.make_aware(datetime(2024, 1, 1, 10, 0))
        end_time = timezone.make_aware(datetime(2024, 1, 1, 11, 0))

        response = self.client.post(reverse('event_new'), {
            'title': 'Test Weekly Recurring Event',
            'description': 'Test Description',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'recurrence': 'weekly',
            'recurrence_end': '2024-01-31',  # Set the correct end date
            'priority': 2,
        })

        # Check that exactly 5 events were created
        event_count = Event.objects.filter(title='Test Weekly Recurring Event').count()
        self.assertEqual(event_count, 5)

    def test_monthly_recurring_event_creation(self):
        """
        Test the creation of monthly recurring events.
        """
        response = self.client.post(reverse('event_new'), {
            'title': 'Test Monthly Recurring Event',
            'description': 'Monthly recurrence test',
            'start_time': self.event.start_time,
            'end_time': self.event.end_time,
            'recurrence': 'monthly',
            'recurrence_end': '2024-12-31',
            'priority': 2,
        })
        event_count = Event.objects.filter(title='Test Monthly Recurring Event', user=self.user).count()
        self.assertGreaterEqual(event_count, 1)  # Should create at least one event


class UpdatePasswordTests(TestCase):
    """
    Tests for updating user passwords.
    """
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='oldpassword')
        self.client.login(username='testuser', password='oldpassword')

    def test_update_password_mismatch(self):
        """
        Test password update with mismatched new passwords.
        """
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword',
            'new_password2': 'mismatchpassword',
        })
        self.assertFormError(response, 'password_form', 'new_password2', "Passwords do not match.")

    def test_update_password_success(self):
        """
        Test successful password update.
        """
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })
        self.assertRedirects(response, reverse('user_page'))
        self.client.logout()
        login = self.client.login(username='testuser', password='newpassword123')
        self.assertTrue(login)

    def test_password_update_shows_success_message(self):
        """
        Test if success message is displayed after a password update.
        """
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Your password was successfully updated!')

# ========================================================= #
# Add more test cases as needed for specific functionalities.
class FriendRequestTests(TestCase):
    """
    Tests for friend request functionality, including sending, accepting,
    and deleting friend requests, as well as retrieving friends.
    """
    def setUp(self):
        # Create two users for testing
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')

    def test_send_friend_request(self):
        """
        Test sending a friend request from one user to another.
        """
        self.client.login(username='user1', password='testpass123')  # Ensure user1 is logged in

        # Send POST request to send a friend request
        response = self.client.post(reverse('send_friend_request'), {
            'user_id': self.user2.id  # Pass the target user's ID
        })

        # Ensure the response status is 200
        self.assertEqual(response.status_code, 200)

        # Check if the friend request was created
        friend_request = FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2).first()
        self.assertIsNotNone(friend_request)
        self.assertEqual(friend_request.from_user, self.user1)
        self.assertEqual(friend_request.to_user, self.user2)

    def test_accept_friend_request(self):
        """
        Test accepting a friend request sent by another user.
        """
        # Create a friend request
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

        # Log in as the receiving user (to_user)
        self.client.login(username='user2', password='testpass123')

        # Send POST request to accept the friend request
        response = self.client.post(reverse('accept_friend_request'), {
            'request_id': friend_request.id  # Pass the friend request ID
        })

        # Check if the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Refresh the friend request and verify it was accepted
        friend_request.refresh_from_db()
        self.assertTrue(friend_request.accepted)

    def test_get_friends(self):
        """
        Test retrieving the list of friends for a user.
        """
        # Create an accepted friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)

        # Verify that user2 is in the list of friends for user1
        friends = FriendRequest.objects.filter(from_user=self.user1, accepted=True).values_list('to_user', flat=True)
        self.assertIn(self.user2.id, friends)

    def test_delete_friends(self):
        """
        Test deleting a friend from the friend list.
        """
        # Create an accepted friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)

        # Log in as the second user
        self.client.login(username='user2', password='testpass123')

        # Send DELETE request to remove the friend
        response = self.client.generic('DELETE', reverse('delete_friend'), json.dumps({
            'friend_id': self.user1.id  # Specify the friend's user ID
        }), content_type='application/json')

        # Ensure the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Verify the friendship was deleted
        is_friends = FriendRequest.objects.filter(
            (Q(from_user=self.user1, to_user=self.user2) |
             Q(from_user=self.user2, to_user=self.user1)) & Q(accepted=True)
        ).exists()
        self.assertFalse(is_friends)


class CalendarAccessTests(TestCase):
    """
    Tests for calendar sharing and token-based access functionalities.
    """
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_create_calendar_access(self):
        """
        Test creating a calendar access token for a user.
        """
        access = CalendarAccess.objects.create(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    def test_calendar_access_retrieval(self):
        """
        Test retrieving a calendar access object using a token.
        """
        access = CalendarAccess.objects.create(user=self.user)
        retrieved_access = CalendarAccess.objects.get(token=access.token)
        self.assertEqual(retrieved_access, access)

    def test_link_creation(self):
        """
        Test generating a shareable calendar link for a user.
        """
        self.client.login(username='testuser', password='testpass123')

        # Send GET request to generate a calendar link
        response = self.client.get(reverse('generate_calendar_link'), {
            'owner_id': self.user.id  # Specify the owner's user ID
        })

        # Ensure the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Verify the calendar access object was created
        access = CalendarAccess.objects.get(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    def test_link_usage(self):
        """
        Test accessing a shared calendar using a valid token.
        """
        access = CalendarAccess.objects.create(user=self.user)

        # Send GET request with the token to access the shared calendar
        response = self.client.get(reverse('view_shared_calendar'), {
            'token': access.token  # Provide the token as a query parameter
        })

        # Check if the response status is 302 (redirect to the owner's calendar)
        self.assertEqual(response.status_code, 302)


class CalendarViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.friend = User.objects.create_user(username='friend', password='testpass123')
        self.stranger = User.objects.create_user(username='stranger', password='testpass123')
        FriendRequest.objects.create(from_user=self.owner, to_user=self.friend, accepted=True)

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(reverse('calendar', args=[self.owner.id]))
        self.assertRedirects(response, reverse('index'))

    def test_stranger_access_denied(self):
        self.client.login(username='stranger', password='testpass123')
        response = self.client.get(reverse('calendar', args=[self.owner.id]))
        self.assertRedirects(response, reverse('calendar', args=[self.stranger.id]))

    def test_friend_access_granted(self):
        self.client.login(username='friend', password='testpass123')
        response = self.client.get(reverse('calendar', args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)

    def test_owner_access_granted(self):
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('calendar', args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)


class EventDetailViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.friend = User.objects.create_user(username='friend', password='testpass123')
        self.stranger = User.objects.create_user(username='stranger', password='testpass123')
        FriendRequest.objects.create(from_user=self.owner, to_user=self.friend, accepted=True)

        # Create an event
        self.event = Event.objects.create(
            title='Test Event',
            description='Event Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            user=self.owner
        )

    def test_owner_access_granted(self):
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_friend_access_granted(self):
        self.client.login(username='friend', password='testpass123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_stranger_access_denied(self):
        self.client.login(username='stranger', password='testpass123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 204)


class DeleteEventTests(TestCase):
    def setUp(self):
        # Users for testing
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.stranger = User.objects.create_user(username='stranger', password='testpass123')
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.client.login(username='owner', password='testpass123')
        # Set a default user for generic tests
        self.user = self.owner  # Use self.user for tests expecting this attribute

        # Create a standard event
        self.event = Event.objects.create(
            title='Test Event',
            description='Event Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            user=self.owner
        )

        # Create a recurring event (for recurring event tests)
        self.recurring_event = Event.objects.create(
            title='Recurring Event',
            description='Recurring Event Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            user=self.user,  # The default user
            recurrence='daily',
            recurrence_end=timezone.now() + timedelta(days=5)
        )

    def test_owner_deletes_event(self):
        self.client.login(username='owner', password='testpass123')
        response = self.client.post(reverse('delete_event', args=[self.owner.id, self.event.id]))
        self.assertRedirects(response, reverse('calendar', args=[self.owner.id]))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_stranger_cannot_delete_event(self):
        """
        Test that a user who is not the owner of an event cannot delete it.
        """
        self.client.login(username='stranger', password='testpass123')
        response = self.client.post(reverse('delete_event', args=[self.owner.id, self.event.id]), follow=True)

        # Verify the user is redirected
        self.assertEqual(response.status_code, 200)

        # Check for the error message in the response context
        messages = list(response.context['messages'])
        self.assertTrue(any("You don't have permission to delete this event." in str(msg) for msg in messages))




    def test_invalid_event_creation(self):
        """
        Test that invalid event data is rejected.
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('event_new'), {
            'title': '',  # Missing title
            'start_time': '',  # Missing start time
            'end_time': '',  # Missing end time
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'title', 'This field is required.')


    def test_invalid_calendar_access_token(self):
        """
        Test accessing a calendar with an invalid token.
        """
        invalid_token = uuid4()  # Generate a valid UUID
        CalendarAccess.objects.create(user=self.owner, token=invalid_token)  # Save valid token to avoid crashes

        # Pass a different invalid token for the test
        response = self.client.get(reverse('view_shared_calendar'), {'token': '00000000-0000-0000-0000-000000000000'})
        self.assertEqual(response.status_code, 404)



    def test_duplicate_friend_request(self):
        """
        Test that duplicate friend requests cannot be sent.
        """
        # Create an initial friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

        # Log in as the sending user
        self.client.login(username='user1', password='testpass123')

        # Attempt to send another friend request to the same user
        response = self.client.post(reverse('send_friend_request'), {'user_id': self.user2.id})

        # Check the status code and error message
        self.assertEqual(response.status_code, 400)  # Expecting a Bad Request response
        self.assertJSONEqual(
            response.content.decode('utf-8'),
            {'success': False, 'message': 'Friend request already sent.'}
        )


## Missing Views.py Tests ##

class FriendRequestEdgeCaseTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.client.login(username="user1", password="testpass123")

    def test_send_friend_request_to_self(self):
        response = self.client.post(reverse("send_friend_request"), {"user_id": self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("You cannot send a friend request to yourself", response.json()["message"])

    def test_accept_nonexistent_friend_request(self):
        self.client.login(username="user2", password="testpass123")
        response = self.client.post(reverse("accept_friend_request"), {"request_id": 999})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Friend request not found", response.json()["error"])


class CalendarAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_access_calendar_without_token(self):
        response = self.client.get(reverse("view_shared_calendar"))
        self.assertEqual(response.status_code, 404)

    def test_access_calendar_invalid_token(self):
        response = self.client.get(reverse("view_shared_calendar") + "?token=invalid_token")
        self.assertEqual(response.status_code, 404)

    def test_access_calendar_valid_token(self):
        calendar_access = CalendarAccess.objects.create(user=self.user)
        response = self.client.get(reverse("view_shared_calendar") + f"?token={calendar_access.token}")
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/calendar/{self.user.id}", response.url)


class EventPermissionTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.event = Event.objects.create(
            title="Private Event",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            user=self.user1,
        )
        self.client.login(username="user2", password="testpass123")

    def test_view_event_without_permission(self):
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 204)

    def test_delete_event_without_permission(self):
        response = self.client.post(reverse("delete_event", args=[self.user2.id, self.event.id]))
        self.assertEqual(response.status_code, 403)


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_update_account_invalid_data(self):
        response = self.client.post(reverse("update_account"), {"username": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_logout_redirect(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))


class GameCreationEdgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_create_game_missing_required_fields(self):
        response = self.client.post(reverse("create_game"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")



## Missing Utils.py Tests ##

class RecurringEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.event = Event.objects.create(
            title="Recurring Event",
            start_time=timezone.make_aware(datetime(2024, 1, 1, 10, 0)),
            end_time=timezone.make_aware(datetime(2024, 1, 1, 11, 0)),
            user=self.user,
            recurrence="daily",
        )

    def test_no_recurring_events_past_end_date(self):
        calendar = Calendar(2024, 1)
        recurring_events = calendar.get_recurring_events(Event.objects.all(), 15)
        self.assertEqual(recurring_events.count(), 0)

    def test_invalid_date_handling(self):
        calendar = Calendar(2024, 2)
        recurring_events = calendar.get_recurring_events(Event.objects.all(), 30)
        self.assertEqual(recurring_events.count(), 0)

# Tests for game list page - specificially page render and delete game (since create and edit games are already tested above).
class GameListTests(TestCase):
    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")
        
        # Create games associated with the user
        self.game1 = Game.objects.create(name="Game 1", user=self.user, genre="Action", platform="PC")
        self.game2 = Game.objects.create(name="Game 2", user=self.user, genre="RPG", platform="Xbox")

    def test_game_list_page(self):
        """
        Test that the Game List page renders correctly and displays the user's games.
        """
        response = self.client.get(reverse('game_list'))  
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game_list.html')  
        games = response.context['games']  
        self.assertIn(self.game1, games)
        self.assertIn(self.game2, games)
        self.assertContains(response, self.game1.name)
        self.assertContains(response, self.game2.name)

    def test_delete_game(self):
        """
        Test deleting a game works as expected.
        """
        url = reverse('delete_game', args=[self.game2.id]) 
        response = self.client.post(url)

        # Check for a successful redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('game_list'))

        # Verify the game was deleted from the database
        game_exists = Game.objects.filter(id=self.game2.id).exists()
        self.assertFalse(game_exists)