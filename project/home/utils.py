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
        recurring_events_list = []  # Temporary list to hold recurring events for this day

        # Validate the day
        max_day = monthrange(self.year, self.month)[1]  # Get the max days in the month
        if day < 1 or day > max_day:  # Check if the day is valid
            return Event.objects.none()

        # Create the current date for the given day in the current calendar
        current_date = datetime(self.year, self.month, day).date()

        for event in events:
            if event.recurrence != 'none':
                start_date = event.start_time.date()
                recurrence_end = event.recurrence_end or current_date

                # Ensure the event's recurrence period includes the current date
                if start_date <= current_date <= recurrence_end:
                    if event.recurrence == 'daily':
                        # Daily events appear every day within the range
                        recurring_events_list.append(event)

                    elif event.recurrence == 'weekly':
                        # Explicitly calculate the recurrence dates for weekly events
                        weekly_occurrence = start_date
                        while weekly_occurrence <= recurrence_end:
                            if weekly_occurrence == current_date:
                                recurring_events_list.append(event)
                                break
                            weekly_occurrence += timedelta(weeks=1)

                    elif event.recurrence == 'monthly':
                        # Explicitly calculate the recurrence dates for monthly events
                        monthly_occurrence = start_date
                        while monthly_occurrence <= recurrence_end:
                            if monthly_occurrence == current_date:
                                recurring_events_list.append(event)
                                break
                            # Move to the next month while keeping the day the same
                            if monthly_occurrence.month == 12:
                                monthly_occurrence = monthly_occurrence.replace(year=monthly_occurrence.year + 1, month=1)
                            else:
                                monthly_occurrence = monthly_occurrence.replace(month=monthly_occurrence.month + 1)

        # Convert list to QuerySet with `in_bulk` to ensure no duplicates
        recurring_events_ids = [event.id for event in recurring_events_list]
        recurring_events = Event.objects.filter(id__in=recurring_events_ids)

        return recurring_events
    # Formats a week as a tr 
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    # Formats a month as a table
    def formatmonth(self, events, withyear=True):
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

#shows only 1 week without messing up the rest of the month
class CalendarWeek(Calendar):
    def formatmonth(self, withyear=True, user_id=None):
        user = User.objects.get(id=user_id)

        # Fetch all events for the user as a QuerySet
        events = Event.objects.filter(user=user_id, start_time__month=self.month, start_time__year=self.year)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
            break
        cal += f'</table>\n'
        return cal
