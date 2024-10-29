from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm

# Create your models here.

# Game model
class Game(models.Model):
    PLATFORM_CHOICES = [
        ('PC', 'PC'),
        ('PS', 'PlayStation'),
        ('XBOX', 'Xbox'),
        ('NS', 'Nintendo Switch'),
    ]
    COLOR_CHOICES = [
        ('#FF5733', 'Red'),
        ('#FFA500', 'Orange'),
        ('#FFFF33', 'Yellow'),
        ('#33FF57', 'Green'),
        ('#3357FF', 'Blue'),
        ('#FF33FF', 'Pink'),
        ('#800080', 'Purple'),
    ]
    name = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True, null=True)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, blank=True, null=True)
    developer = models.CharField(max_length=100, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#FFFFFF')  # Set default color

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
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, default = None)

    class Meta:
        permissions = [("saved_events", "can save events")]
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    @property
    def get_html_url(self):
        # Return the event_detail link for the event
        url = reverse('event_detail', args=(self.id,))
        # Override default url settings, make font black for readability
        return f'<a href="{url}" style="color: #000;">{self.title}</a>'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Grant 'view_event' permission to the assigned user
        assign_perm('view_event', self.user, self)

User = get_user_model()