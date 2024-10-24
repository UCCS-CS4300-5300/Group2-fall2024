from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

# Create your models here.

# Game model
class Game(models.Model):
    PLATFORM_CHOICES = [
        ('PC', 'PC'),
        ('PS', 'PlayStation'),
        ('XBOX', 'Xbox'),
        ('NS', 'Nintendo Switch'),
    ]

    name = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True, null=True)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, blank=True, null=True)
    developer = models.CharField(max_length=100, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

# Event model 
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
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    @property
    def get_html_url(self):
        # Return the event_detail link for the event
        url = reverse('event_detail', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'



User = get_user_model()