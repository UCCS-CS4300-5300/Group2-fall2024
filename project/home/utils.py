# home/utils.py 

# home/utils.py 

from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Event

from .templatetags.template_tags import *
from django.urls import reverse

from django.core import signing
from django.conf import settings
from django.utils import timezone

class Calendar(HTMLCalendar):
	def __init__(self, year=None, month=None):
		self.year = year
		self.month = month
		super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
	def formatday(self, day, events):

		events_per_day = events.filter(start_time__day=day)
		

		d=''
		for event in events_per_day:
			# Use the game's color, default to white 
			event_color = event.game.color if event.game else '#FFFFFF'
			# Color code the event based on the game
			d += f'<li style="background-color: {event_color}; padding: 5px; border-radius: 5px; margin-bottom: 5px; font-weight: bold;">{event.get_html_url}</li>'

		if day != 0:
			return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
		return '<td></td>'

	# formats a week as a tr 
	def formatweek(self, theweek, events):
		week = ''
		for d, weekday in theweek:
			week += self.formatday(d, events)
		return f'<tr> {week} </tr>'

	# formats a month as a table
	# filter events by year and month
	def formatmonth(self, withyear=True, user_id=None):
		
		user = User.objects.get(id = user_id)
		
		events = Event.objects.filter(user = user_id)
		events = Event.objects.filter(user = user_id, start_time__year=self.year, start_time__month=self.month)

		cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
		cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
		cal += f'{self.formatweekheader()}\n'
		for week in self.monthdays2calendar(self.year, self.month):
			cal += f'{self.formatweek(week, events)}\n'
		cal += f'</table>\n'
		return cal

def generate_user_token(user_id):
    # Sign the user_id to generate a secure token
    return signing.dumps({'user_id': user_id})

def validate_user_token(token):
    try:
        # Unsign the token to retrieve the user_id
        data = signing.loads(token)
        return data.get('user_id')
    except signing.BadSignature:
        # Return None or raise an error if the token is invalid or expired
        return None