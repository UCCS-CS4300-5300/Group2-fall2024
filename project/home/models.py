from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

# Create your models here.
class Event(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    
    @property
    def get_html_url(self):
        # Return the event_detail link for the event
        url = reverse('event_detail', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'


User = get_user_model()