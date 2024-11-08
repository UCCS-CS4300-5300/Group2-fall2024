# home/utils.py 

from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Event
from guardian.shortcuts import get_objects_for_user
from .templatetags.template_tags import *
from django.urls import reverse
from calendar import HTMLCalendar, monthrange
from django.contrib.auth.models import User

class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # Formats a day as a td
    def formatday(self, day, events):
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
        recurring_events = Event.objects.none()  # Start with an empty QuerySet

        # Validate the day
        max_day = monthrange(self.year, self.month)[1]  # Get the max days in the month
        if day < 1 or day > max_day:  # Check if the day is valid
            return recurring_events
        
        # Create the current date
        current_date = datetime(self.year, self.month, day)

        for event in events:
            if event.recurrence != 'none':
                start_date = event.start_time.date()
                recurrence_end = event.recurrence_end or datetime.now().date()

                # Check if the event is in the range
                if start_date <= current_date.date() <= recurrence_end:
                    if event.recurrence == 'daily':
                        # Daily events occur every day within the range
                        recurring_events |= Event.objects.filter(
                            start_time__date__gte=start_date,
                            start_time__date__lte=recurrence_end
                        ).filter(
                            recurrence='daily',
                            start_time__month=self.month,
                            start_time__year=self.year
                        )
                    elif event.recurrence == 'weekly' and current_date.weekday() == event.start_time.weekday():
                        # Weekly events should match the weekday
                        recurring_events |= Event.objects.filter(
                            start_time__date__gte=start_date,
                            start_time__date__lte=recurrence_end
                        ).filter(
                            recurrence='weekly',
                            start_time__month=self.month,
                            start_time__year=self.year
                        )
                    elif event.recurrence == 'monthly' and current_date.day == event.start_time.day:
                        # Monthly events should match the day of the month
                        recurring_events |= Event.objects.filter(
                            start_time__date__gte=start_date,
                            start_time__date__lte=recurrence_end
                        ).filter(
                            recurrence='monthly',
                            start_time__month=self.month,
                            start_time__year=self.year
                        )

        return recurring_events

    # Formats a week as a tr 
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    # Formats a month as a table
    def formatmonth(self, withyear=True, user_id=None):
        user = User.objects.get(id=user_id)

        # Fetch all events for the user as a QuerySet
        events = Event.objects.filter(user=user_id, start_time__month=self.month, start_time__year=self.year)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        cal += f'</table>\n'
        return cal

