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

from datetime import datetime, timedelta, date
from .models import Event
from .templatetags.template_tags import *
from django.urls import reverse
from calendar import HTMLCalendar, monthrange
from django.contrib.auth.models import User
from django.core import signing
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, F

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
        # print(f"DEBUG: Generating HTML for day={day}")
        # print(f"DEBUG: Events passed to formatday={events}")
        events_per_day = events.filter(start_time__day=day)
        # print(f"DEBUG: Events for {day}: {list(events_per_day.values('title', 'start_time'))}")

        # Check for recurring events
        recurring_events = self.get_recurring_events(events, day)

        # Combine events and recurring events
        all_events = events_per_day | recurring_events  # Use | for QuerySet union
        all_events = all_events.filter(Q(recurrence_end__isnull=True) | Q(start_time__lte=F('recurrence_end')))
        # print(f"DEBUG: Filtered events for {day}: {list(all_events.values('title', 'start_time'))}")
        # print(f"DEBUG: All events for {day}: {list(all_events.values('title', 'start_time'))}")


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
        recurring_events_list = []

        max_day = monthrange(self.year, self.month)[1]
        if day < 1 or day > max_day:
            return Event.objects.none()

        current_date = datetime(self.year, self.month, day).date()

        for event in events:
            if event.recurrence != 'none':
                start_date = event.start_time.date()
                recurrence_end = event.recurrence_end or current_date

                # Ensure recurrence_end is properly validated
                if isinstance(recurrence_end, datetime):
                    recurrence_end = recurrence_end.date()

                # Debug: Check event details
                # print(f"DEBUG: Checking event {event.title}")
                # print(f"DEBUG: Event start_date={start_date}, recurrence_end={recurrence_end}, current_date={current_date}")

                # Check if the event falls within the recurrence range
                if not (start_date <= current_date <= recurrence_end):
                    # print(f"DEBUG: Skipping event {event.title}, out of range.")
                    continue

                if event.recurrence == 'daily':
                    recurring_events_list.append(event)

                elif event.recurrence == 'weekly':
                    delta_days = (current_date - start_date).days
                    if delta_days % 7 == 0:
                        recurring_events_list.append(event)

                elif event.recurrence == 'monthly':
                    # Calculate the difference in months between the current date and the start date
                    month_diff = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
                    
                    # Ensure the event recurs on the correct day and avoid invalid dates
                    try:
                        if month_diff >= 0 and current_date.day == start_date.day:
                            recurring_events_list.append(event)
                    except ValueError:
                        pass  # Skip invalid days (e.g., February 30 for an event starting on January 30)

        # Filter to remove any events that fall outside their recurrence_end
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