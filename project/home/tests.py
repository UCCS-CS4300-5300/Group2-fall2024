from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from home.models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from .forms import CustomUserCreationForm, EventForm, GameForm
from django.contrib.messages import get_messages
from django.utils.http import urlencode


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
        
        # Ensure we stay on the same page on login failure
        self.assertEqual(response.status_code, 200)
        
        # Check if errors exist in the form (non-field errors)
        self.assertTrue(response.context['form'].errors)
        
        # Optionally, check for partial text in the error message
        error_message = str(response.context['form'].errors.get('__all__'))
        self.assertIn('Please enter a correct username and password', error_message)

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
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        form_data = {
            'title': 'Test Event',
            'description': 'This is a test event.',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'recurrence': 'none',  # Use a valid choice from RECURRING_CHOICES
            'priority': 2,         # Assuming this is a valid priority
        }

        response = self.client.post(reverse('event_new'), form_data)

        # Check if it was supposed to redirect (302)
        if response.status_code == 200:
            # Only print form errors if the form was re-rendered
            print(response.context.get('form').errors)

        # Assert redirect as expected
        self.assertRedirects(response, reverse('calendar', args=[self.user.id]))

    def test_calendar_view(self):
        # Test access to calendar view
        response = self.client.get(reverse('calendar', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_edit_event(self):
        url = reverse('event_edit', args=[self.event.id])
        
        # Make a POST request to update the event
        response = self.client.post(url, {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'start_time': '2024-01-01T12:00',  # Adjusted format for datetime-local
            'end_time': '2024-01-01T13:00',
            'recurrence': 'none',  # Valid recurrence choice
            'priority': 2          # Valid priority choice
        })

        # Check if it was supposed to redirect (302)
        if response.status_code == 200:
            # Print form errors if the form was re-rendered
            print(response.context.get('form').errors)

        # Assert redirect as expected
        self.assertEqual(response.status_code, 302)


class EventDeletionTests(TestCase):
    def setUp(self):
        # Create a user and log them in
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

        # Create an event for the user
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            user=self.user
        )

    def test_delete_event(self):
        # Attempt to delete the event
        response = self.client.post(reverse('delete_event', args=[self.user.id, self.event.id]))

        # Check if the response is a redirect (successful deletion)
        self.assertEqual(response.status_code, 302)

        # Confirm the event was deleted
        event_exists = Event.objects.filter(id=self.event.id).exists()
        self.assertFalse(event_exists)


class EventDetailTests(TestCase):
    def setUp(self):
        # Create two users
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass456')

        # Create an event for the first user
        self.event = Event.objects.create(
            title='User Event',
            description='Event for testing details',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            user=self.user
        )

    def test_event_detail_view_user_has_permission(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_detail.html')
        self.assertContains(response, 'User Event')



class TodoListViewTests(TestCase):
    def setUp(self):
        # Create two users and log in the first one
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass456')
        self.client.login(username='testuser', password='testpass123')

        # Use the current date in the test setup to match the view's filter
        current_date = timezone.localtime(timezone.now()).date()
        start_time_user = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
        end_time_user = start_time_user + timedelta(hours=1)
        
        start_time_other_user = start_time_user + timedelta(hours=2)
        end_time_other_user = start_time_other_user + timedelta(hours=1)

        # Create events for each user
        self.event1 = Event.objects.create(
            title='User Event',
            start_time=start_time_user,
            end_time=end_time_user,
            user=self.user
        )
        self.event2 = Event.objects.create(
            title='Other User Event',
            start_time=start_time_other_user,
            end_time=end_time_other_user,
            user=self.other_user
        )

    def test_todo_list_view_shows_only_user_events(self):
        response = self.client.get(reverse('todo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Event')
        self.assertNotContains(response, 'Other User Event')

class GameCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_create_game_view(self):
        form_data = {
            'name': 'New Game',
            'description': 'Game description',
            'color': '#FF5733',  # Use a valid color choice
            'platform': '',       # Optional
            'developer': '',      # Optional
            'release_date': '',   # Optional
            'genre': '',          # Optional
            'picture_link': '',   # Optional
        }

        response = self.client.post(reverse('create_game'), form_data)

        # Check if it was supposed to redirect (302)
        if response.status_code == 200:
            # Only print form errors if the form was re-rendered
            print(response.context.get('form').errors)

        # Assert redirect as expected
        self.assertRedirects(response, reverse('calendar', args=[self.user.id]))


class CustomUserCreationFormTests(TestCase):
    def test_username_already_exists(self):
        User.objects.create_user(username='existinguser', password='password123')
        form_data = {
            'username': 'existinguser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'email': 'newemail@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_already_exists(self):
        User.objects.create_user(username='user1', email='test@example.com', password='password123')
        form_data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'email': 'test@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_passwords_do_not_match(self):
        form_data = {
            'username': 'testuser',
            'password1': 'testpass123',
            'password2': 'differentpass123',
            'email': 'testuser@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class EventFormTests(TestCase):
    def test_event_form_valid(self):
        form_data = {
            'title': 'Valid Event',
            'description': 'An event description',
            'start_time': '2024-01-01T10:00',
            'end_time': '2024-01-01T12:00',
            'recurrence': 'none',  # Use 'none' as per RECURRING_CHOICES
            'priority': 2,         # Assuming 1 is Low, 2 is Medium, 3 is High
            'recurrence_end': ''    # Optional field
        }
        form = EventForm(data=form_data)
        print(form.errors)  # Debugging line to check any validation errors
        self.assertTrue(form.is_valid())

    def test_event_form_end_time_before_start_time(self):
        form_data = {
            'title': 'Invalid Event',
            'description': 'An invalid event',
            'start_time': '2024-01-01T10:00',
            'end_time': '2024-01-01T09:00'
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)


class EventEdgeCaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_event_same_start_and_end_time(self):
        response = self.client.post(reverse('event_new'), {
            'title': 'Instant Event',
            'description': 'An event that starts and ends instantly',
            'start_time': '2024-01-01T10:00',
            'end_time': '2024-01-01T10:00'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End time must be after start time')


class FormSaveTests(TestCase):
    def test_custom_user_creation_form_save(self):
        form_data = {
            'username': 'newuser',
            'password1': 'saphire1',
            'password2': 'saphire1',
            'email': 'newuser@example.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')


class GameFormTests(TestCase):
    def test_game_form_with_optional_fields(self):
        form_data = {
            'name': 'Test Game',
            'description': 'A game description',
            'release_date': '',  # Optional
            'genre': '',         # Optional
            'platform': '',      # Optional
            'developer': '',     # Optional
            'color': '#FF5733',  # Valid choice from COLOR_CHOICES
            'picture_link': '',  # Optional
        }
        form = GameForm(data=form_data)
        print(form.errors)
        self.assertTrue(form.is_valid())

class RecurringEventTests(TestCase):

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create an event
        self.event = Event.objects.create(
            title='Test Recurring Event',
            description='Test Description',
            start_time=timezone.make_aware(datetime(2024, 1, 1, 10, 0, 0)),
            end_time=timezone.make_aware(datetime(2024, 1, 1, 11, 0, 0)),
            user=self.user,
            recurrence='daily',  # Setting recurrence to daily for the test
            recurrence_end=datetime(2024, 1, 10)  # End after 10th January
        )

    def test_daily_recurring_event_creation(self):
        # Create recurring event
        response = self.client.post(reverse('event_new'), {
            'title': 'Test Recurring Event',
            'description': 'Test Description',
            'start_time': self.event.start_time,
            'end_time': self.event.end_time,
            'user': self.user.id,
            'recurrence': 'daily',
            'recurrence_end': '2024-01-10',  # Set the end date for recurrence
            'priority': 2,
        })

        # Ensure the event was created
        event_exists = Event.objects.filter(title='Test Recurring Event', user=self.user).count()
        self.assertEqual(event_exists, 10)  # Should create 10 events (from Jan 1 to Jan 10)

    def test_weekly_recurring_event_creation(self):
        # Create weekly recurring event
        response = self.client.post(reverse('event_new'), {
            'title': 'Test Weekly Recurring Event',
            'description': 'Test Description',
            'start_time': self.event.start_time,
            'end_time': self.event.end_time,
            'user': self.user.id,
            'recurrence': 'weekly',
            'recurrence_end': '2024-01-31',  # Set the end date for recurrence
            'priority': 2,
        })

        # Ensure the event was created weekly
        event_exists = Event.objects.filter(title='Test Weekly Recurring Event', user=self.user).count()
        self.assertEqual(event_exists, 5)  # Should create 5 events (one per week)

    def test_monthly_recurring_event_creation(self):
        # Create monthly recurring event
        response = self.client.post(reverse('event_new'), {
            'title': 'Test Monthly Recurring Event',
            'description': 'Test Description',
            'start_time': self.event.start_time,
            'end_time': self.event.end_time,
            'user': self.user.id,
            'recurrence': 'monthly',
            'recurrence_end': '2024-12-31',  # Set the end date for recurrence
            'priority': 2,
        })

        # Ensure the event was created monthly
        event_exists = Event.objects.filter(title='Test Monthly Recurring Event', user=self.user).count()
        self.assertGreaterEqual(event_exists, 1)  # Should create at least one event in the first month

class UpdatePasswordTests(TestCase):
    
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='oldpassword')
        self.client.login(username='testuser', password='oldpassword')
    
    def test_update_password_mismatch(self):
        # Try submitting a mismatched password form
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword',
            'new_password2': 'mismatchpassword',  # Mismatch in new passwords
        })
        self.assertFormError(response, 'password_form', 'new_password2', "Passwords do not match.")
    
    def test_update_password_success(self):
        # Try submitting a valid password update form
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword123',  # Valid new password
            'new_password2': 'newpassword123',  # Matching confirmation password
        })
        # Check if redirected correctly after successful update
        self.assertRedirects(response, reverse('user_page'))
        
        # Verify user can log in with the new password
        self.client.logout()
        login = self.client.login(username='testuser', password='newpassword123')
        self.assertTrue(login)
    
    def test_password_update_shows_success_message(self):
        # Check if success message is shown after password update
        url = reverse('update_password')
        response = self.client.post(url, {
            'old_password': 'oldpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })
        # Verify that the success message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Your password was successfully updated!')
