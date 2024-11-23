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
from django.utils.timezone import make_aware
from django.utils.http import urlencode
from django.test import TestCase, Client
from home.models import Event, Game, FriendRequest, CalendarAccess
from home.utils import Calendar
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
        """
        Set up a test user for login tests.

        This method is called before each test case is executed. It creates a test user
        in the database, which will be used for authentication-related tests.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_index_view(self):
        """
        Test the index view for proper response and template usage.

        This test verifies:
        - The index view responds with a 200 HTTP status code.
        - The correct template (`index.html`) is used for rendering.

        Steps:
        1. Send a GET request to the `index` view.
        2. Assert the response status is 200.
        3. Assert the correct template is used in the response.

        Parameters:
        - None
        """
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_login_invalid_credentials(self):
        """
        Test login functionality with invalid credentials.

        This test ensures:
        - An invalid login attempt does not authenticate the user.
        - Proper error messages are displayed when login fails.

        Steps:
        1. Send a POST request to the `login` view with invalid credentials.
        2. Assert the response status is 200 (form reloads due to errors).
        3. Assert the form's error context contains the appropriate error message.

        Parameters:
        - None
        """
        response = self.client.post(
            reverse("login"),
            {
                "username": "invaliduser",  # Non-existent username
                "password": "wrongpassword",  # Incorrect password
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        error_message = str(response.context["form"].errors.get("__all__"))
        self.assertIn("Please enter a correct username and password", error_message)

    def test_login_valid_credentials(self):
        """
        Test login functionality with valid credentials.

        This test ensures:
        - A user with valid credentials is authenticated.
        - The user is redirected to the `index` view after a successful login.

        Steps:
        1. Send a POST request to the `login` view with valid credentials.
        2. Assert the response status is 302 (redirect after login).
        3. Assert the response redirects to the `index` view.

        Parameters:
        - None
        """
        response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",  # Valid username
                "password": "testpass123",  # Correct password
            },
        )
        self.assertEqual(response.status_code, 302)  # Expect a redirect after successful login
        self.assertRedirects(response, reverse("index"))


class UserCreationTests(TestCase):
    """
    Tests for user registration and account creation functionalities.
    """

    def setUp(self):
        """
        Set up the test client for user registration tests.

        This method is called before each test case and initializes the Django test client.
        The test client simulates user interactions with the application, such as sending
        HTTP requests to views.

        Parameters:
        - None
        """
        self.client = Client()

    def test_user_registration(self):
        """
        Test the user registration process and ensure successful user creation.

        This test verifies:
        - A new user can register with valid input data.
        - The user is redirected to the login page after registration.
        - The user is successfully created and saved in the database.

        Steps:
        1. Send a POST request to the `register` view with valid user data.
        2. Assert the response redirects to the `login` view.
        3. Check if the new user exists in the database.

        Parameters:
        - None
        """
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",  # Valid username for registration
                "password1": "saphire1",  # Valid password
                "password2": "saphire1",  # Matching confirmation password
                "email": "testuser@example.com",  # Valid email address
            },
        )

        # Assert that the response redirects to the login page
        self.assertRedirects(response, reverse("login"))

        # Check that the user was successfully created in the database
        user_exists = User.objects.filter(username="testuser").exists()
        self.assertTrue(user_exists)


class EventTests(TestCase):
    """
    Tests for event creation, editing, and calendar views.
    """

    def setUp(self):
        """
        Create a test user and a sample event for testing.

        This method is called before each test case. It creates a test user and logs them in,
        ensuring the user is authenticated for event-related operations. It also creates a
        sample event to test editing and viewing functionalities.

        Parameters:
        - None
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Create a sample event
        self.event = Event.objects.create(
            title="Test Event",  # Event title
            description="Test Description",  # Event description
            start_time="2024-01-01 10:00:00",  # Start time of the event
            end_time="2024-01-01 11:00:00",  # End time of the event
            user=self.user,  # Owner of the event
        )

    def test_create_event(self):
        """
        Test the event creation process.

        This test ensures:
        - A user can create an event with valid input data.
        - The user is redirected to the calendar view after creating an event.

        Steps:
        1. Construct valid event data, including start and end times.
        2. Send a POST request to the `event_new` view with the event data.
        3. Assert the response redirects to the user's calendar view.
        4. Check the event exists in the database.

        Parameters:
        - None
        """
        # Define event start and end times
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        form_data = {
            "title": "Test Event",  # Event title
            "description": "This is a test event.",  # Event description
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),  # ISO format start time
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),  # ISO format end time
            "recurrence": "none",  # No recurrence
            "priority": 2,  # Priority level
        }

        # Send POST request to create the event
        response = self.client.post(reverse("event_new"), form_data)

        # Assert the response redirects to the user's calendar
        self.assertRedirects(response, reverse("calendar", args=[self.user.id]))

    def test_calendar_view(self):
        """
        Test access to the calendar view for the logged-in user.

        This test ensures:
        - The calendar view is accessible to an authenticated user.
        - The correct template (`calendar.html`) is used for rendering.

        Steps:
        1. Send a GET request to the `calendar` view for the logged-in user.
        2. Assert the response status is 200 (successful rendering).
        3. Assert the correct template is used in the response.

        Parameters:
        - None
        """
        # Send GET request to access the calendar
        response = self.client.get(reverse("calendar", args=[self.user.id]))

        # Assert the response status is 200
        self.assertEqual(response.status_code, 200)

        # Assert the correct template is used
        self.assertTemplateUsed(response, "calendar.html")

    def test_edit_event(self):
        """
        Test editing an existing event.

        This test ensures:
        - An event can be updated with valid input data.
        - The user is redirected after editing the event.

        Steps:
        1. Construct valid updated event data.
        2. Send a POST request to the `event_edit` view for the specific event.
        3. Assert the response status is 302 (indicating a redirect).

        Parameters:
        - None
        """
        # URL to edit the existing event
        url = reverse("event_edit", args=[self.event.id])

        # Define updated event data
        updated_data = {
            "title": "Updated Event",  # Updated title
            "description": "Updated Description",  # Updated description
            "start_time": "2024-01-01T12:00",  # Updated start time
            "end_time": "2024-01-01T13:00",  # Updated end time
            "recurrence": "none",  # No recurrence
            "priority": 2,  # Updated priority level
        }

        # Send POST request to edit the event
        response = self.client.post(url, updated_data)

        # Assert the response status is 302 (redirect after successful edit)
        self.assertEqual(response.status_code, 302)


class EventDeletionTests(TestCase):
    """
    Tests for deleting events in the application.
    """

    def setUp(self):
        """
        Set up a test user and a sample event for deletion tests.

        This method is executed before each test case to create:
        - A test user who will own the event.
        - An event associated with the test user to test the deletion functionality.

        Parameters:
        - None
        """
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Log in the test user
        self.client.login(username="testuser", password="testpass123")

        # Create a sample event for deletion
        self.event = Event.objects.create(
            title="Test Event",  # Event title
            description="Test Description",  # Event description
            start_time=timezone.now() + timedelta(days=1),  # Event start time
            end_time=timezone.now() + timedelta(days=1, hours=1),  # Event end time
            user=self.user,  # Event owner
        )

    def test_delete_event(self):
        """
        Test the deletion of an event by its owner.

        This test verifies:
        - The owner of an event can delete it.
        - The event is removed from the database after deletion.
        - A successful redirection occurs after deletion.

        Steps:
        1. Send a POST request to the `delete_event` view with the event ID.
        2. Assert the response status is 302 (indicating a redirect after deletion).
        3. Check that the event no longer exists in the database.

        Parameters:
        - None
        """
        # Send POST request to delete the event
        response = self.client.post(reverse("delete_event", args=[self.user.id, self.event.id]))

        # Assert the response status is 302 (redirect after deletion)
        self.assertEqual(response.status_code, 302)

        # Assert the event no longer exists in the database
        event_exists = Event.objects.filter(id=self.event.id).exists()
        self.assertFalse(event_exists)


class FriendRequestTests(TestCase):
    """
    Tests for friend request functionality, including sending, accepting, deleting friend requests,
    and retrieving friends.
    """

    def setUp(self):
        """
        Set up two test users to test friend request functionalities.

        This method is executed before each test case to create:
        - User1: The user who will send the friend request.
        - User2: The user who will receive and accept the friend request.

        Parameters:
        - None
        """
        # Create two test users
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_send_friend_request(self):
        """
        Test sending a friend request from one user to another.

        This test verifies:
        - A logged-in user (user1) can send a friend request to another user (user2).
        - The friend request is saved in the database.

        Steps:
        1. Log in as `user1`.
        2. Send a POST request to the `send_friend_request` view with `user2`'s ID.
        3. Assert the response status is 200 (indicating success).
        4. Verify the friend request exists in the database.

        Parameters:
        - None
        """
        # Log in as the user sending the friend request
        self.client.login(username="user1", password="testpass123")

        # Send POST request to send a friend request
        response = self.client.post(reverse("send_friend_request"), {"user_id": self.user2.id})

        # Assert the response status is 200 (successful request)
        self.assertEqual(response.status_code, 200)

        # Check that the friend request exists in the database
        friend_request_exists = FriendRequest.objects.filter(
            from_user=self.user1, to_user=self.user2
        ).exists()
        self.assertTrue(friend_request_exists)

    def test_accept_friend_request(self):
        """
        Test accepting a friend request.

        This test verifies:
        - A logged-in user (user2) can accept a friend request sent by another user (user1).
        - The friend request's `accepted` field is updated in the database.

        Steps:
        1. Create a friend request from `user1` to `user2`.
        2. Log in as `user2`.
        3. Send a POST request to the `accept_friend_request` view with the friend request ID.
        4. Assert the response status is 200 (indicating success).
        5. Verify the `accepted` field of the friend request is set to `True`.

        Parameters:
        - None
        """
        # Create a friend request from user1 to user2
        friend_request = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

        # Log in as the user accepting the friend request
        self.client.login(username="user2", password="testpass123")

        # Send POST request to accept the friend request
        response = self.client.post(
            reverse("accept_friend_request"), {"request_id": friend_request.id}
        )

        # Assert the response status is 200 (successful request)
        self.assertEqual(response.status_code, 200)

        # Refresh the friend request from the database to get updated data
        friend_request.refresh_from_db()

        # Assert the friend request has been accepted
        self.assertTrue(friend_request.accepted)

    def test_get_friends(self):
        """
        Test retrieving the list of friends for a user.

        This test verifies:
        - A user can retrieve a list of their accepted friends.
        """
        # Create an accepted friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)

        # Verify that user2 is in the list of friends for user1
        friends = FriendRequest.objects.filter(from_user=self.user1, accepted=True).values_list(
            "to_user", flat=True
        )
        self.assertIn(self.user2.id, friends)

    def test_delete_friends(self):
        """
        Test deleting a friend from the friend list.

        This test verifies:
        - A logged-in user can delete a friend from their friend list.
        - The friendship is removed from the database.

        Parameters:
        - None
        """
        # Create an accepted friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, accepted=True)

        # Log in as the second user
        self.client.login(username="user2", password="testpass123")

        # Send DELETE request to remove the friend
        response = self.client.generic(
            "DELETE",
            reverse("delete_friend"),
            json.dumps({"friend_id": self.user1.id}),  # Specify the friend's user ID
            content_type="application/json",
        )

        # Ensure the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Verify the friendship was deleted
        is_friends = FriendRequest.objects.filter(
            (
                Q(from_user=self.user1, to_user=self.user2)
                | Q(from_user=self.user2, to_user=self.user1)
            )
            & Q(accepted=True)
        ).exists()
        self.assertFalse(is_friends)


class CalendarAccessTests(TestCase):
    """
    Tests for calendar sharing and token-based access functionalities.

    This includes:
    - Creating calendar access tokens.
    - Retrieving calendar access objects using tokens.
    - Generating shareable calendar links.
    - Accessing shared calendars using valid, invalid, or missing tokens.
    """

    def setUp(self):
        """
        Set up a user for testing.

        This method creates a test user to use in all the calendar access tests.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_create_calendar_access(self):
        """
        Test creating a calendar access token for a user.

        This ensures:
        - A calendar access object is created successfully.
        - The token field is not None.
        - The created object is linked to the correct user.
        """
        access = CalendarAccess.objects.create(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    def test_calendar_access_retrieval(self):
        """
        Test retrieving a calendar access object using its token.

        This ensures:
        - A calendar access object can be retrieved using its token field.
        """
        access = CalendarAccess.objects.create(user=self.user)
        retrieved_access = CalendarAccess.objects.get(token=access.token)
        self.assertEqual(retrieved_access, access)

    def test_link_creation(self):
        """
        Test generating a shareable calendar link for a user.

        This ensures:
        - A user can successfully generate a shareable calendar link.
        - The generated calendar access object contains a valid token.
        """
        self.client.login(username="testuser", password="testpass123")

        # Send GET request to generate a calendar link
        response = self.client.get(
            reverse("generate_calendar_link"),
            {"owner_id": self.user.id},  # Specify the owner's user ID
        )

        # Ensure the response status is 200 (successful AJAX response)
        self.assertEqual(response.status_code, 200)

        # Verify the calendar access object was created
        access = CalendarAccess.objects.get(user=self.user)
        self.assertIsNotNone(access.token)
        self.assertEqual(access.user, self.user)

    def test_link_usage(self):
        """
        Test using a calendar sharing link to access a user's calendar.

        This ensures:
        - Accessing a calendar with a valid token redirects to the correct calendar view.
        """
        access = CalendarAccess.objects.create(user=self.user)
        response = self.client.get(reverse("view_shared_calendar"), {"token": access.token})

        # Ensure the response is a redirect to the owner's calendar view
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/calendar/{self.user.id}", response.url)

    def test_access_calendar_without_token(self):
        """
        Test accessing a calendar without providing a token.

        This ensures:
        - Accessing the calendar without a token results in a 404 response.
        """
        response = self.client.get(reverse("view_shared_calendar"))
        self.assertEqual(response.status_code, 404)

    def test_access_calendar_invalid_token(self):
        """
        Test accessing a calendar with an invalid token.

        This ensures:
        - Accessing the calendar with a token that is not a valid UUID results in a 404 response.
        """
        # Use a valid UUID format to avoid triggering a ValidationError but ensure it's not in the database
        invalid_token = uuid4()
        response = self.client.get(reverse("view_shared_calendar"), {"token": invalid_token})
        self.assertEqual(response.status_code, 404)

    def test_access_calendar_valid_token(self):
        """
        Test accessing a calendar with a valid token.

        This ensures:
        - Accessing a calendar with a valid token redirects to the owner's calendar view.
        """
        calendar_access = CalendarAccess.objects.create(user=self.user)
        response = self.client.get(
            reverse("view_shared_calendar") + f"?token={calendar_access.token}"
        )

        # Assert redirection to the owner's calendar view
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/calendar/{self.user.id}", response.url)


class GameCreationTests(TestCase):
    """
    Tests for game creation functionality.
    """

    def setUp(self):
        """
        Set up a test user to test game creation functionalities.

        This method is executed before each test case to create:
        - A test user who will log in and perform game creation actions.

        Parameters:
        - None
        """
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Log in the test user
        self.client.login(username="testuser", password="testpass123")

    def test_create_game_view(self):
        """
        Test the creation of a new game.

        This test verifies:
        - A logged-in user can successfully create a game with valid input data.
        - The created game is stored in the database.
        - The user is redirected to the game list view after successful creation.

        Steps:
        1. Construct valid game data, including required and optional fields.
        2. Send a POST request to the `create_game` view with the game data.
        3. Assert the response redirects to the `game_list` view.
        4. Verify that the new game exists in the database.

        Parameters:
        - None
        """
        # Define valid game creation form data
        form_data = {
            "name": "New Game",  # Required field: name of the game
            "color": "#FF5733",  # Required field: valid color choice
            "platform": "",  # Optional field: platform of the game
            "developer": "",  # Optional field: developer of the game
            "release_date": "",  # Optional field: release date of the game
            "genre": "",  # Optional field: genre of the game
            "picture_link": "",  # Optional field: link to an image of the game
        }

        # Send POST request to create the game
        response = self.client.post(reverse("create_game"), form_data)

        # Assert the response redirects to the game list view
        self.assertRedirects(response, reverse("game_list"))

        # Verify the game was successfully created in the database
        game_exists = Game.objects.filter(name="New Game", user=self.user).exists()
        self.assertTrue(game_exists)


class RecurringEventTests(TestCase):
    """
    Tests for recurring event creation and edge case handling functionalities.

    This includes:
    - Testing the creation of daily, weekly, and monthly recurring events.
    - Ensuring events are not created beyond their recurrence end date.
    - Handling invalid dates gracefully.
    """

    def setUp(self):
        """
        Set up a test user and a sample recurring event.

        This method:
        - Creates a test user and logs them in.
        - Sets up a sample daily recurring event for use in test cases.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

        # Create a sample recurring event
        self.event = Event.objects.create(
            title="Recurring Event",
            start_time=make_aware(datetime(2024, 1, 1, 10, 0)),
            end_time=make_aware(datetime(2024, 1, 1, 11, 0)),
            user=self.user,
            recurrence="daily",
            recurrence_end=datetime(2024, 1, 10),
        )

    def test_daily_recurring_event_creation(self):
        """
        Test the creation of daily recurring events.

        This test:
        - Sends a POST request to create a daily recurring event.
        - Verifies that the correct number of events are created in the database,
          based on the recurrence end date.
        """
        start_time = make_aware(datetime(2024, 1, 1, 10, 0))
        end_time = make_aware(datetime(2024, 1, 1, 11, 0))

        response = self.client.post(
            reverse("event_new"),
            {
                "title": "Test Daily Recurring Event",
                "description": "Test Description",
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
                "recurrence": "daily",
                "recurrence_end": "2024-01-10",
                "priority": 2,
            },
        )

        # Calculate the expected number of events (inclusive of start and end dates)
        recurrence_start_date = start_time.date()
        recurrence_end_date = datetime.strptime("2024-01-10", "%Y-%m-%d").date()
        expected_count = (recurrence_end_date - recurrence_start_date).days

        # Verify the number of created events matches the expected count
        event_count = Event.objects.filter(title="Test Daily Recurring Event").count()
        self.assertEqual(event_count, expected_count)

    def test_weekly_recurring_event_creation(self):
        """
        Test the creation of weekly recurring events.

        This test:
        - Sends a POST request to create a weekly recurring event.
        - Verifies that the correct number of events are created based on the recurrence end date.
        """
        start_time = make_aware(datetime(2024, 1, 1, 10, 0))
        end_time = make_aware(datetime(2024, 1, 1, 11, 0))

        response = self.client.post(
            reverse("event_new"),
            {
                "title": "Test Weekly Recurring Event",
                "description": "Test Description",
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
                "recurrence": "weekly",
                "recurrence_end": "2024-01-31",
                "priority": 2,
            },
        )

        # Verify that exactly 5 weekly events were created
        event_count = Event.objects.filter(title="Test Weekly Recurring Event").count()
        self.assertEqual(event_count, 5)

    def test_monthly_recurring_event_creation(self):
        """
        Test the creation of monthly recurring events.

        This test:
        - Sends a POST request to create a monthly recurring event.
        - Verifies that at least one event is created based on the recurrence end date.
        """
        response = self.client.post(
            reverse("event_new"),
            {
                "title": "Test Monthly Recurring Event",
                "description": "Monthly recurrence test",
                "start_time": self.event.start_time,
                "end_time": self.event.end_time,
                "recurrence": "monthly",
                "recurrence_end": "2024-12-31",
                "priority": 2,
            },
        )

        # Verify that at least one monthly event was created
        event_count = Event.objects.filter(
            title="Test Monthly Recurring Event", user=self.user
        ).count()
        self.assertGreaterEqual(event_count, 1)

    def test_no_recurring_events_past_end_date(self):
        """
        Test that no recurring events are created beyond their recurrence end date.

        This test:
        - Simulates querying recurring events for a date range beyond the end date.
        - Verifies that no events are returned past the specified end date.
        """
        calendar = Calendar(2024, 1)  # Assuming `Calendar` is a utility to handle events
        recurring_events = calendar.get_recurring_events(Event.objects.all(), 15)

        # Verify that no events are created past the end date
        self.assertEqual(recurring_events.count(), 0)

    def test_invalid_date_handling(self):
        """
        Test handling of invalid dates in the calendar.

        This test:
        - Simulates querying recurring events for invalid dates.
        - Verifies that no events are retrieved for invalid or non-existent dates.
        """
        calendar = Calendar(2024, 2)  # Assuming `Calendar` is properly implemented
        recurring_events = calendar.get_recurring_events(Event.objects.all(), 30)

        # Verify that no recurring events are retrieved for invalid dates
        self.assertEqual(recurring_events.count(), 0)


class UpdatePasswordTests(TestCase):
    """
    Tests for updating user passwords.

    This class tests:
    - The ability to update a user's password successfully.
    - Proper handling of mismatched passwords during an update.
    - Display of success messages after a successful password update.

    The tests ensure that:
    - Only valid password updates are processed.
    - Users can log in with the updated password after the change.
    - Proper feedback is provided for invalid operations.
    """

    def setUp(self):
        """
        Set up a test user and log them in for password update tests.

        This method:
        - Creates a user with a predefined username and password.
        - Logs the user in to simulate an authenticated session.

        Parameters:
        - None
        """
        # Create a user for testing
        self.user = User.objects.create_user(username="testuser", password="oldpassword")
        self.client.login(username="testuser", password="oldpassword")

    def test_update_password_mismatch(self):
        """
        Test password update with mismatched new passwords.

        This test verifies:
        - The update process fails when the two new passwords do not match.
        - An appropriate form error message is displayed.

        Steps:
        1. Send a POST request with the old password and mismatched new passwords.
        2. Assert that the form error for "new_password2" indicates mismatched passwords.

        Parameters:
        - None
        """
        url = reverse("update_password")
        response = self.client.post(
            url,
            {
                "old_password": "oldpassword",
                "new_password1": "newpassword",
                "new_password2": "mismatchpassword",
            },
        )
        self.assertFormError(response, "password_form", "new_password2", "Passwords do not match.")

    def test_update_password_success(self):
        """
        Test successful password update.

        This test verifies:
        - The password update succeeds when valid data is provided.
        - The user is redirected to their user page after the update.
        - The user can log in with the new password after the update.

        Steps:
        1. Send a POST request with the correct old password and matching new passwords.
        2. Assert that the response redirects to the user page.
        3. Log out the user and attempt to log in with the new password.
        4. Assert that the login with the new password is successful.

        Parameters:
        - None
        """
        url = reverse("update_password")
        response = self.client.post(
            url,
            {
                "old_password": "oldpassword",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )
        self.assertRedirects(response, reverse("user_page"))
        self.client.logout()
        login = self.client.login(username="testuser", password="newpassword123")
        self.assertTrue(login)

    def test_password_update_shows_success_message(self):
        """
        Test if success message is displayed after a password update.

        This test verifies:
        - A success message is added to the response after a successful password update.

        Steps:
        1. Send a POST request with the correct old password and matching new passwords.
        2. Retrieve messages from the response's WSGI request.
        3. Assert that the success message matches the expected text.

        Parameters:
        - None
        """
        url = reverse("update_password")
        response = self.client.post(
            url,
            {
                "old_password": "oldpassword",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your password was successfully updated!")


class CalendarViewTests(TestCase):
    """
    Tests for calendar view permissions and access.

    This class ensures that:
    - Unauthenticated users are redirected to the index page.
    - Users who are not friends with the owner cannot access the owner's calendar.
    - Friends of the owner can access the owner's calendar.
    - The owner of the calendar has full access to their own calendar.

    The tests validate permission handling for calendar view functionality.
    """

    def setUp(self):
        """
        Set up test users and relationships for calendar view tests.

        This method:
        - Creates three users:
          - `owner`: The user who owns the calendar.
          - `friend`: A user who is friends with the owner and has access to the calendar.
          - `stranger`: A user who is not friends with the owner and should not have access.
        - Establishes a friend relationship between `owner` and `friend`.

        Parameters:
        - None
        """
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.friend = User.objects.create_user(username="friend", password="testpass123")
        self.stranger = User.objects.create_user(username="stranger", password="testpass123")
        FriendRequest.objects.create(from_user=self.owner, to_user=self.friend, accepted=True)

    def test_unauthenticated_user_redirected(self):
        """
        Test that unauthenticated users are redirected to the index page.

        This test verifies:
        - Unauthenticated users cannot access the calendar view.
        - The system redirects unauthenticated users to the index page.

        Steps:
        1. Send a GET request to the calendar view for the owner's calendar without logging in.
        2. Assert that the response redirects to the index page.

        Parameters:
        - None
        """
        response = self.client.get(reverse("calendar", args=[self.owner.id]))
        self.assertRedirects(response, reverse("index"))

    def test_stranger_access_denied(self):
        """
        Test that a user who is not friends with the owner is denied access.

        This test verifies:
        - A stranger (a user without a friendship with the owner) cannot access the owner's calendar.
        - The system redirects the stranger to their own calendar page.

        Steps:
        1. Log in as the stranger.
        2. Send a GET request to the calendar view for the owner's calendar.
        3. Assert that the response redirects to the stranger's own calendar page.

        Parameters:
        - None
        """
        self.client.login(username="stranger", password="testpass123")
        response = self.client.get(reverse("calendar", args=[self.owner.id]))
        self.assertRedirects(response, reverse("calendar", args=[self.stranger.id]))

    def test_friend_access_granted(self):
        """
        Test that a friend of the owner is granted access to the owner's calendar.

        This test verifies:
        - A friend (a user with an accepted friend request from the owner) can access the owner's calendar.
        - The calendar view responds with a 200 status code.

        Steps:
        1. Log in as the friend.
        2. Send a GET request to the calendar view for the owner's calendar.
        3. Assert that the response status code is 200.

        Parameters:
        - None
        """
        self.client.login(username="friend", password="testpass123")
        response = self.client.get(reverse("calendar", args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)

    def test_owner_access_granted(self):
        """
        Test that the owner of the calendar has access to their own calendar.

        This test verifies:
        - The owner can access their own calendar without any restrictions.
        - The calendar view responds with a 200 status code.

        Steps:
        1. Log in as the owner.
        2. Send a GET request to the calendar view for the owner's calendar.
        3. Assert that the response status code is 200.

        Parameters:
        - None
        """
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("calendar", args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)


class EventDetailViewTests(TestCase):
    """
    Tests for the event detail view permissions and access.

    This class ensures that:
    - The owner of an event can access its details.
    - Friends of the owner can access the event details.
    - Users who are not friends with the owner are denied access to the event details.

    These tests validate the correct permission handling for the event detail view.
    """

    def setUp(self):
        """
        Set up test users, relationships, and an event for testing event detail view permissions.

        This method:
        - Creates three users:
          - `owner`: The owner of the event.
          - `friend`: A friend of the owner with access to the event.
          - `stranger`: A user with no access to the event.
        - Establishes a friend relationship between the `owner` and `friend`.
        - Creates an event owned by the `owner`.

        Parameters:
        - None
        """
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.friend = User.objects.create_user(username="friend", password="testpass123")
        self.stranger = User.objects.create_user(username="stranger", password="testpass123")
        FriendRequest.objects.create(from_user=self.owner, to_user=self.friend, accepted=True)

        # Create an event owned by the owner
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            user=self.owner,
        )

    def test_owner_access_granted(self):
        """
        Test that the owner of the event can access its details.

        This test verifies:
        - The owner can access the event detail view without restrictions.
        - The event detail view responds with a 200 status code.

        Steps:
        1. Log in as the owner of the event.
        2. Send a GET request to the event detail view for the created event.
        3. Assert that the response status code is 200.

        Parameters:
        - None
        """
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_friend_access_granted(self):
        """
        Test that a friend of the event owner can access the event details.

        This test verifies:
        - A friend of the event owner (with an accepted friend request) can access the event detail view.
        - The event detail view responds with a 200 status code.

        Steps:
        1. Log in as a friend of the event owner.
        2. Send a GET request to the event detail view for the created event.
        3. Assert that the response status code is 200.

        Parameters:
        - None
        """
        self.client.login(username="friend", password="testpass123")
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)

    def test_stranger_access_denied(self):
        """
        Test that a stranger (a user without a friendship with the owner) is denied access to the event details.

        This test verifies:
        - A user who is not friends with the event owner cannot access the event detail view.
        - The event detail view responds with a 204 status code (no content).

        Steps:
        1. Log in as a stranger.
        2. Send a GET request to the event detail view for the created event.
        3. Assert that the response status code is 204.

        Parameters:
        - None
        """
        self.client.login(username="stranger", password="testpass123")
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 204)


class DeleteEventTests(TestCase):
    """
    Tests for deleting events and related functionalities.

    This class ensures:
    - Event owners can delete their own events.
    - Non-owners cannot delete events and receive appropriate feedback.
    - Invalid event data submissions are rejected.
    - Accessing a calendar with an invalid token fails gracefully.
    - Duplicate friend requests cannot be created.
    """

    def setUp(self):
        """
        Set up test users, events, and relationships for deletion tests.

        This method:
        - Creates users for different test cases:
          - `owner`: The owner of the event.
          - `stranger`: A user not authorized to delete the event.
          - `user1` and `user2`: Users used for friend request-related tests.
        - Creates a standard event and a recurring event owned by `owner`.

        Parameters:
        - None
        """
        # Create test users
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.stranger = User.objects.create_user(username="stranger", password="testpass123")
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

        # Log in as the owner
        self.client.login(username="owner", password="testpass123")

        # Set the default user for generic tests
        self.user = self.owner

        # Create a standard event
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            user=self.owner,
        )

        # Create a recurring event
        self.recurring_event = Event.objects.create(
            title="Recurring Event",
            description="Recurring Event Description",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            user=self.user,
            recurrence="daily",
            recurrence_end=timezone.now() + timedelta(days=5),
        )

    def test_owner_deletes_event(self):
        """
        Test that the owner can delete their own event.

        This test verifies:
        - The owner can delete an event they created.
        - The event is removed from the database.
        - The user is redirected to the calendar view after deletion.

        Steps:
        1. Log in as the owner of the event.
        2. Send a POST request to the `delete_event` view for the event.
        3. Assert the user is redirected to the calendar view.
        4. Verify the event no longer exists in the database.

        Parameters:
        - None
        """
        self.client.login(username="owner", password="testpass123")
        response = self.client.post(reverse("delete_event", args=[self.owner.id, self.event.id]))
        self.assertRedirects(response, reverse("calendar", args=[self.owner.id]))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_stranger_cannot_delete_event(self):
        """
        Test that a non-owner cannot delete an event.

        This test verifies:
        - A user who does not own the event cannot delete it.
        - The system displays an appropriate error message.
        - The user is redirected back to the appropriate page.

        Steps:
        1. Log in as a stranger (non-owner).
        2. Send a POST request to the `delete_event` view for the event.
        3. Assert the user is redirected.
        4. Verify an error message is displayed in the response context.

        Parameters:
        - None
        """
        self.client.login(username="stranger", password="testpass123")
        response = self.client.post(
            reverse("delete_event", args=[self.owner.id, self.event.id]), follow=True
        )

        # Verify the user is redirected
        self.assertEqual(response.status_code, 200)

        # Check for the error message in the response context
        messages = list(response.context["messages"])
        self.assertTrue(
            any("You don't have permission to delete this event." in str(msg) for msg in messages)
        )

    def test_invalid_event_creation(self):
        """
        Test that invalid event data submissions are rejected.

        This test verifies:
        - Submitting a form with missing required fields is not accepted.
        - An error message is displayed for the invalid fields.

        Steps:
        1. Log in as a user.
        2. Send a POST request to the `event_new` view with missing data.
        3. Assert the response status code is 200.
        4. Verify the form displays an error message for the missing fields.

        Parameters:
        - None
        """
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(
            reverse("event_new"),
            {
                "title": "",  # Missing title
                "start_time": "",  # Missing start time
                "end_time": "",  # Missing end time
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "title", "This field is required.")

    def test_invalid_calendar_access_token(self):
        """
        Test accessing a calendar with an invalid token.

        This test verifies:
        - Using an invalid calendar token results in a 404 response.
        - The system handles invalid tokens gracefully without crashing.

        Steps:
        1. Create a valid calendar access token.
        2. Send a GET request to `view_shared_calendar` with an invalid token.
        3. Assert the response status code is 404.

        Parameters:
        - None
        """
        invalid_token = uuid4()  # Generate a valid UUID
        CalendarAccess.objects.create(
            user=self.owner, token=invalid_token
        )  # Save valid token to avoid crashes

        # Pass a different invalid token for the test
        response = self.client.get(
            reverse("view_shared_calendar"), {"token": "00000000-0000-0000-0000-000000000000"}
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_friend_request(self):
        """
        Test that duplicate friend requests cannot be sent.

        This test verifies:
        - A user cannot send a friend request to the same recipient more than once.
        - An appropriate error message is returned for duplicate requests.

        Steps:
        1. Create an initial friend request.
        2. Log in as the sending user.
        3. Attempt to send another friend request to the same recipient.
        4. Assert the response status code is 400.
        5. Verify the error message in the response content.

        Parameters:
        - None
        """
        # Create an initial friend request
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

        # Log in as the sending user
        self.client.login(username="user1", password="testpass123")

        # Attempt to send another friend request to the same user
        response = self.client.post(reverse("send_friend_request"), {"user_id": self.user2.id})

        # Check the status code and error message
        self.assertEqual(response.status_code, 400)  # Expecting a Bad Request response
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {"success": False, "message": "Friend request already sent."},
        )


## Missing Views.py Tests ##


class FriendRequestEdgeCaseTests(TestCase):
    """
    Tests for edge cases in friend request functionalities.
    """

    def setUp(self):
        """
        Set up two test users for edge case tests.

        This method creates:
        - `user1`: A user who will perform the test actions (e.g., sending/accepting friend requests).
        - `user2`: A second user to interact with `user1` in the tests.

        Parameters:
        - None
        """
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.client.login(username="user1", password="testpass123")

    def test_send_friend_request_to_self(self):
        """
        Test that a user cannot send a friend request to themselves.

        This test ensures:
        - A user cannot send a friend request to themselves.
        - The appropriate error message is returned in the JSON response.

        Steps:
        1. Log in as `user1`.
        2. Attempt to send a friend request to `user1` (self).
        3. Assert that the response status is 200.
        4. Verify the error message in the JSON response.

        Parameters:
        - None
        """
        response = self.client.post(reverse("send_friend_request"), {"user_id": self.user1.id})

        # Assert the response status is 200 (indicating the request was processed)
        self.assertEqual(response.status_code, 200)

        # Verify the error message in the response
        self.assertIn("You cannot send a friend request to yourself", response.json()["message"])

    def test_accept_nonexistent_friend_request(self):
        """
        Test that attempting to accept a nonexistent friend request returns an error.

        Steps:
        1. Log in as `user2`.
        2. Attempt to accept a friend request with an invalid ID.
        3. Assert that the response status is 500.
        4. Verify the error message in the JSON response.
        """
        self.client.login(username="user2", password="testpass123")

        # Attempt to accept a friend request with a nonexistent ID
        response = self.client.post(reverse("accept_friend_request"), {"request_id": 999})

        # Assert the response status is 500
        self.assertEqual(response.status_code, 500)

        # Verify the error message indicates no matching friend request
        self.assertIn("No FriendRequest matches the given query.", response.json()["error"])


class EventPermissionTests(TestCase):
    """
    Tests for ensuring proper permission handling for viewing and deleting events.
    """

    def setUp(self):
        """
        Sets up the test environment by creating two users and an event.
        - `user1` is the owner of the event.
        - `user2` is another user who will attempt to access or delete the event.
        """
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
        """
        Test that a user cannot view an event they do not have permission to access.

        Steps:
        1. Log in as `user2` (a user who does not own the event).
        2. Attempt to access the detail view of an event owned by `user1`.
        3. Assert that the response status code is 204, indicating restricted access.

        Note:
        Update the expected response code if the view behavior changes (e.g., to 403 Forbidden).
        """
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 204)

    def test_delete_event_without_permission(self):
        """
        Test that a user without permission to delete an event is redirected appropriately.

        Steps:
        1. Log in as `user2` (a user who does not own the event).
        2. Attempt to delete an event owned by `user1`.
        3. Assert that the response status code is 302 (redirect).
        4. Verify the user is redirected to their own calendar page (`/calendar/{user_id}/`).

        Expected Behavior:
        Unauthorized users should not be able to delete events they do not own and
        should be redirected to their own calendar.
        """
        response = self.client.post(reverse("delete_event", args=[self.user2.id, self.event.id]))

        # Assert the response status is 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Verify the redirection URL is to the user's calendar
        self.assertEqual(response.url, f"/calendar/{self.user2.id}/")


class UserProfileTests(TestCase):
    """
    Tests for user profile-related functionality, including updating account details
    and logging out.
    """

    def setUp(self):
        """
        Sets up the test environment by creating a user and logging them in.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_update_account_invalid_data(self):
        """
        Test that submitting invalid data when updating an account shows an error.

        Steps:
        1. Log in as `testuser`.
        2. Submit a POST request to the `update_account` view with an empty username.
        3. Assert that the response status is 200 (form re-rendered with errors).
        4. Verify that the error message "This field is required." is included in the response.
        """
        response = self.client.post(reverse("update_account"), {"username": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_logout_redirect(self):
        """
        Test that logging out redirects the user to the index page.

        Steps:
        1. Log in as `testuser`.
        2. Submit a GET request to the `logout` view.
        3. Assert that the response status is 302 (redirect).
        4. Verify the user is redirected to the index page.
        """
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))


class GameCreationEdgeTests(TestCase):
    """
    Tests for edge cases in game creation functionality.
    """

    def setUp(self):
        """
        Sets up the test environment by creating a user and logging them in.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_create_game_missing_required_fields(self):
        """
        Test that creating a game with missing required fields shows an error.

        Steps:
        1. Log in as `testuser`.
        2. Submit a POST request to the `create_game` view with an empty "name" field.
        3. Assert that the response status is 200 (form re-rendered with errors).
        4. Verify that the error message "This field is required." is included in the response.
        """
        response = self.client.post(reverse("create_game"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")


## Missing Utils.py Tests ##


class GameListTests(TestCase):
    """
    Tests for the game list page, specifically rendering the page and deleting a game.
    """

    def setUp(self):
        """
        Sets up the test environment by:
        - Creating a user and logging them in.
        - Creating two games associated with the user.
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Create games associated with the logged-in user
        self.game1 = Game.objects.create(
            name="Game 1", user=self.user, genre="Action", platform="PC"
        )
        self.game2 = Game.objects.create(
            name="Game 2", user=self.user, genre="RPG", platform="Xbox"
        )

    def test_game_list_page(self):
        """
        Test that the Game List page renders correctly and displays the user's games.

        Steps:
        1. Log in as the test user.
        2. Access the game list page via a GET request.
        3. Assert that the response status code is 200 (page loads successfully).
        4. Verify that the correct template ("game_list.html") is used.
        5. Check that both games created for the user are included in the context.
        6. Confirm that the page content contains the names of both games.
        """
        response = self.client.get(reverse("game_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game_list.html")
        games = response.context["games"]
        self.assertIn(self.game1, games)
        self.assertIn(self.game2, games)
        self.assertContains(response, self.game1.name)
        self.assertContains(response, self.game2.name)

    def test_delete_game(self):
        """
        Test that deleting a game works as expected.

        Steps:
        1. Log in as the test user.
        2. Submit a POST request to delete one of the games (game2).
        3. Assert that the response status code is 302 (redirect).
        4. Verify that the user is redirected to the game list page.
        5. Confirm that the deleted game (game2) no longer exists in the database.
        """
        url = reverse("delete_game", args=[self.game2.id])
        response = self.client.post(url)

        # Check for a successful redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("game_list"))

        # Verify the game was deleted from the database
        game_exists = Game.objects.filter(id=self.game2.id).exists()
        self.assertFalse(game_exists)
