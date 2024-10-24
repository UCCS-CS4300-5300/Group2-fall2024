from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    @property
    def get_html_url(self):
        # Return the event_detail link for the event
        url = reverse('event_detail', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'


User = get_user_model()