# tasks.py
import os
from django.utils import timezone
from datetime import datetime, timedelta
from django_q.tasks import async_task
from .models import Event  # Import your Event model
from project.sendgrid_client import send_email  # Import the SendGrid email client

def send_event_reminders():
    """
    Fetches all events scheduled for today and sends reminder emails to their associated users.
    
    This function:
    - Retrieves the current date and calculates the start and end of the day.
    - Filters events that fall within this time range.
    - Sends reminder emails to users for each event using asynchronous tasks.
    """
    # Get the current time
    now = timezone.now()

    # Get the start and end of the day in the current timezone
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Use start_time instead of starttime
    events_today = Event.objects.filter(start_time__range=(start_of_day, end_of_day))

    for event in events_today:
        # user_email = event.user.email  # Assuming each event is linked to a user
        user_email = event.user.email
        subject = 'Reminder: Event Today'
        content = f'<p>You have an event: <strong>{event.title}</strong> scheduled for today.</p>'
        
        # Send the email using SendGrid API

        async_task('home.tasks.send_email_task', subject, user_email, content)

def send_email_task(subject, to_email, content):
    """
    Sends an email using the SendGrid email client.

    Args:
        subject (str): Subject line of the email.
        to_email (str): Recipient's email address.
        content (str): Body content of the email in HTML format.

    Returns:
        None. Prints success or failure messages to the console.
    """
    print("Current SendGrid API Key:", os.environ.get('SENDGRID_API_KEY'))  # Debugging line
    status, body, headers = send_email(subject, to_email, content)
    
    if status == 202:
        print(f"Email successfully sent to {to_email}.")
    else:
        print(f"Failed to send email to {to_email}: {body}")



# Note:
# - The `SENDGRID_API_KEY` must be set in the environment and available to both `qcluster` and `runserver`.
# - This script assumes the `Event` model has a `user` attribute with an associated email.