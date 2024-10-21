from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from home.models import Event
from django.contrib.auth.models import User


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
        self.assertContains(response, 'account done not exist plz sign in')  # Check for the specific error message

    # Test the login view with valid credentials
    def test_login_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect after successful login
        self.assertRedirects(response, reverse('index'))

    # Test user registration
    def test_register_view(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())  # Ensure the user was created
 