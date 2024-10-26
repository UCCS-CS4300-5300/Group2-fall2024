from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, Client
from home.models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta


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