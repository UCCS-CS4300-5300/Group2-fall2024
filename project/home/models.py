"""
models.py

This module contains the database models used in the application. The models define the structure of the application's
data and include methods for interacting with the database.

Models:
    - Game: Represents a game in the system, including details like name, genre, platform, and associated images.
    - Event: Represents an event in the system, including its details, recurrence patterns, and associations with users and games.
    - FriendRequest: Represents a friend request between users, supporting accepted and pending requests.
    - CalendarAccess: Represents a token-based system to share access to a user's calendar.

Features:
    - Supports recurring events (daily, weekly, monthly) with an optional end date.
    - Provides permission-based access to events using the `guardian` library.
    - Manages relationships between users through friend requests.
    - Enables calendar sharing via unique tokens.
"""

from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import reverse
from guardian.shortcuts import assign_perm
import uuid

# Create your models here.

# Game model
class Game(models.Model):
    """
    Represents a game in the system.

    Attributes:
        name (str): Name of the game.
        genre (str): Genre of the game (optional).
        platform (str): Gaming platform (e.g., PC, PlayStation).
        developer (str): Developer of the game (optional).
        release_date (date): Release date of the game (optional).
        color (str): Color code associated with the game (e.g., for UI purposes).
        picture_link (str): URL to the game's image (optional).
        picture_upload (ImageField): Optional uploaded image for the game.
    """
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
    picture_link = models.CharField(max_length=1000, blank=True, null=True)
    
    #adding in this so peopel can upload pictures
    picture_upload = models.ImageField(blank=True, null=True)

    def __str__(self):
        """
        Returns the string representation of the game.
        """
        return self.name

# Event model 
class Event(models.Model):
    """
    Represents an event in the system.

    Attributes:
        title (str): Title of the event.
        description (str): Detailed description of the event.
        start_time (datetime): When the event starts.
        end_time (datetime): When the event ends.
        user (User): The user associated with the event.
        recurrence (str): Recurrence pattern of the event (none, daily, weekly, monthly).
        recurrence_end (date): Optional end date for recurring events.
        priority (int): Priority level of the event (1=Low, 2=Medium, 3=High).
        game (Game): Optional game associated with the event.
    """
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
    ############### This is where recurring choices being implemented #################
    RECURRING_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    recurrence = models.CharField(max_length=20, choices=RECURRING_CHOICES, default='none')
    recurrence_end = models.DateField(blank=True, null=True)  # End date for the recurrence

    class Meta:
        permissions = [("saved_events", "can save events")]
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    @property
    def get_html_url(self):
        """
        Generates the URL for the event's detail page and returns it as an HTML anchor tag.
        """
        # Return the event_detail link for the event
        url = reverse('event_detail', args=(self.id,))
        # Override default url settings, make font black for readability
        return f'<a href="{url}" style="color: #000;">{self.title}</a>'

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to assign view permissions to the user.
        """
        super().save(*args, **kwargs)
        # Grant 'view_event' permission to the assigned user
        assign_perm('view_event', self.user, self)

    def __str__(self):
        """
        Returns the string representation of the event.
        """
        return self.title

User = get_user_model()

class FriendRequest(models.Model):
    """
    Represents a friend request between users.

    Attributes:
        from_user (User): The user who sent the request.
        to_user (User): The user who received the request.
        created_at (datetime): When the friend request was created.
        accepted (bool): Whether the request has been accepted.
    """
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        """
        Returns a string representation of the friend request.
        """
        return f'{self.from_user.username} to {self.to_user.username}'

    @property
    def friends(self):
        """
        Returns a queryset of all accepted friends for the current user.
        """
        # Get users who have accepted friend requests in either direction
        friends = User.objects.filter(
            Q(id__in=FriendRequest.objects.filter(from_user=self.from_user, accepted=True).values_list('to_user', flat=True)) |
            Q(id__in=FriendRequest.objects.filter(to_user=self.from_user, accepted=True).values_list('from_user', flat=True))
        ).exclude(id=self.from_user.id)  # Exclude the current user

        return friends

class CalendarAccess(models.Model):
    """
    Represents a token-based system to share access to a user's calendar.

    Attributes:
        user (User): The user whose calendar is being shared.
        token (UUID): Unique token for identifying the shared calendar.
        created_at (datetime): When the calendar access was created.
    """
    user = models.ForeignKey(User, related_name='calendar_access', on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the calendar access instance.
        """
        return f"Access for {self.user.username} - {self.token}"
