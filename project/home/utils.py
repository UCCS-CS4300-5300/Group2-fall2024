"""
utils.py
This module provides utility classes and functions to enhance the functionality of the Home application.
Features:
    - **Calendar Class**:
        - Renders HTML calendars for monthly and weekly views.
        - Supports event rendering with recurring events (daily, weekly, monthly).
        - Events are color-coded based on associated games.
    - **Event Recurrence**:
        - Retrieves and formats recurring events for a specific day.
        - Handles edge cases such as invalid dates (e.g., February 30).
    - **Token Generation and Validation**:
        - Generates secure tokens for sharing user calendars.
        - Validates tokens to ensure access security.
Classes:
    - `Calendar`: Renders a monthly HTML calendar with events.
    - `CalendarWeek`: Extends `Calendar` to render a single week.
    
Functions:
    - `generate_user_token(user_id)`: Generates a secure token for user-based operations.
    - `validate_user_token(token)`: Validates and retrieves a user ID from a token.
Notes:
    - Relies on the `Event` model for event-related functionalities.
    - Utilizes Django's `signing` module for secure token handling.
    - Includes robust handling of recurring events and edge cases.
Examples:
    - Generate a calendar:
        ```
        cal = Calendar(2024, 1)
        html_calendar = cal.formatmonth(events)
        ```
    - Generate and validate tokens:
        ```
        token = generate_user_token(user_id)
        user_id = validate_user_token(token)
        ```
"""

from datetime import datetime, timedelta
from .models import Event
from .templatetags.template_tags import *
from django.urls import reverse
from calendar import HTMLCalendar, monthrange
from django.contrib.auth.models import User
from django.core import signing
from django.conf import settings
from django.utils import timezone

class Calendar(HTMLCalendar):
    """
    Calendar class to render a monthly HTML calendar.
    This class formats days, weeks, and months with event data and supports
    recurring events.
    """
    def __init__(self, year=None, month=None):
        """
        Initialize the Calendar instance.
        Args:
            year (int): Year to display in the calendar.
            month (int): Month to display in the calendar.
        """
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # Formats a day as a td
    def formatday(self, day, events):
        """
        Formats a single day cell in the calendar with events.
        Args:
            day (int): Day of the month.
            events (QuerySet): QuerySet of Event objects for the month.
        Returns:
            str: HTML string representing the day's events.
        """
        events_per_day = events.filter(start_time__day=day)

        # Check for recurring events
        recurring_events = self.get_recurring_events(events, day)

        # Combine events and recurring events
        all_events = events_per_day | recurring_events  # Use | for QuerySet union

        # Sort events by priority (higher priority first)
        sorted_events = all_events.order_by('-priority')

        d = ''
        for event in sorted_events:
            # Use the game's color, default to white 
            event_color = event.game.color if event.game else '#FFFFFF'
            # Color code the event based on the game
            d += f'<li style="background-color: {event_color}; padding: 5px; border-radius: 5px; margin-bottom: 5px; font-weight: bold;">{event.get_html_url}</li>'

        # Always show the day cell, even if there are no events
        if day != 0:  # Ensure we do not display a day cell for day 0
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return '<td></td>'

    ##################### Recurring Events ############################
   
    def get_recurring_events(self, events, day):
        """
        Retrieves recurring events for a specific day.
        Args:
            events (QuerySet): QuerySet of Event objects.
            day (int): Day of the month.
        Returns:
            QuerySet: QuerySet of recurring Event objects for the given day.
        """
        recurring_events_list = []  # Temporary list to hold recurring events for this day

        # Validate the day
        max_day = monthrange(self.year, self.month)[1]  # Get the max days in the month
        if day < 1 or day > max_day:  # Check if the day is valid
            return Event.objects.none()

        # Create the current date for the given day in the current calendar
        current_date = datetime(self.year, self.month, day).date()

        for event in events:
            if event.recurrence != 'none':
                # Ensure start_date is initialized
                start_date = event.start_time.date()
                recurrence_end = event.recurrence_end or current_date

                # Ensure the event's recurrence period includes the current date
                if start_date <= current_date <= recurrence_end:
                    if event.recurrence == 'daily':
                        # Daily events appear every day within the range
                        recurring_events_list.append(event)

                    elif event.recurrence == 'weekly':
                        # Check if the current date matches the weekly recurrence
                        delta_days = (current_date - start_date).days
                        if delta_days % 7 == 0:
                            # print(f"Adding weekly event: {event.title} on {current_date}")
                            recurring_events_list.append(event)

                    elif event.recurrence == 'monthly':
                        # Check if the current date matches the monthly recurrence
                        month_diff = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
                        if month_diff >= 0:
                            # print(f"Adding monthly event: {event.title} on {current_date}")
                            # Handle months where the start_date.day might not exist
                            try:
                                if current_date.day == start_date.day:
                                    recurring_events_list.append(event)
                            except ValueError:
                                pass  # Skip invalid days (e.g., February 30)


        # Convert list to QuerySet with `in_bulk` to ensure no duplicates
        recurring_events_ids = [event.id for event in recurring_events_list]
        return Event.objects.filter(id__in=recurring_events_ids)
    # Formats a week as a tr 
    def formatweek(self, theweek, events):
        """
        Formats a single week as a row in the calendar.
        Args:
            theweek (list): List of (day, weekday) tuples for the week.
            events (QuerySet): QuerySet of Event objects.
        Returns:
            str: HTML string representing the week.
        """
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    # Formats a month as a table
    def formatmonth(self, events, withyear=True):
        """
        Formats the entire month as an HTML table.
        Args:
            events (QuerySet): QuerySet of Event objects for the month.
            withyear (bool): Whether to display the year in the month name.
        Returns:
            str: HTML string representing the month.
        """
        # Start creating the HTML table for the month
        self.events = events  # Store events to access within `formatday`
        month_html = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        month_html += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        month_html += f'{self.formatweekheader()}\n'

        # Iterate over weeks in the month
        for week in self.monthdays2calendar(self.year, self.month):
            month_html += '<tr>'
            for day, weekday in week:
                month_html += self.formatday(day, events)
            month_html += '</tr>'

        month_html += '</table>'
        return month_html

def generate_user_token(user_id):
    """
    Generates a secure token for a user.
    Args:
        user_id (int): ID of the user.
    Returns:
        str: A signed token containing the user ID.
    """
    # Sign the user_id to generate a secure token
    return signing.dumps({'user_id': user_id})

def validate_user_token(token):
    """
    Validates a user token and retrieves the user ID.
    Args:
        token (str): The signed token.
    Returns:
        int or None: The user ID if valid, or None if invalid.
    """
    try:
        # Unsign the token to retrieve the user_id
        data = signing.loads(token)
        return data.get('user_id')
    except signing.BadSignature:
        # Return None or raise an error if the token is invalid or expired
        return None