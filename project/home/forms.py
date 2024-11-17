"""
forms.py

This module contains custom form classes used throughout the application. The forms are designed for user registration,
authentication, password management, event creation and management, and game creation. They extend Django's built-in 
form classes and provide custom validation logic to ensure the integrity of submitted data.

Classes:
    - CustomUserCreationForm: A custom user registration form with extended validation for unique usernames and emails.
    - EventForm: A form for creating or updating events, including support for recurring events.
    - GameForm: A form for creating or updating games with optional fields for genre, platform, and other metadata.
    - UsersForm: A form for updating basic user information, such as username, first and last name, and email.
    - CustomPasswordChangeForm: A custom password change form with validation to ensure the new passwords match.

Usage:
    These forms can be used in views to handle user input for registration, login, event management, and other 
    features, ensuring validation and consistent data entry across the application.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError  
from django.forms.forms import Form  
from django.forms import ModelForm, DateInput
from django.forms.fields import EmailField  
from .models import Event, Game



class CustomUserCreationForm(UserCreationForm):
    """
    A custom user registration form extending the built-in UserCreationForm.

    Fields:
        username (str): Username of the user.
        email (str): Email address of the user.
        password1 (str): Password entered by the user.
        password2 (str): Confirmation of the password entered.

    Methods:
        username_clean(): Ensures the username is unique.
        clean_email(): Validates email uniqueness.
        clean_password2(): Ensures password1 and password2 match.
        save(): Creates a new user instance.
    """
    username = forms.CharField(label='username', min_length=5, max_length=150)  
    email = forms.EmailField(label='email')  
    password1 = forms.CharField(label='password', widget=forms.PasswordInput)  
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)  
  
    def username_clean(self):  
        username = self.cleaned_data['username'].lower()  
        new = User.objects.filter(username = username)  
        if new.count():  
            raise ValidationError("User Already Exist")  
        return username  
  
    def clean_email(self):  
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
                raise ValidationError("Email already exists.")
        return email
  
    def clean_password2(self):  
        password1 = self.cleaned_data['password1']  
        password2 = self.cleaned_data['password2']  
  
        if password1 and password2 and password1 != password2:  
            raise ValidationError("Password don't match")  
        return password2  
  
    def save(self, commit = True):  
        """
        Creates and saves a new user instance.
        """
        user = User.objects.create_user(  
            self.cleaned_data['username'],  
            self.cleaned_data['email'],  
            self.cleaned_data['password1']  
        )  
        return user

class EventForm(ModelForm):
    """
    A form for creating or updating events.

    Fields:
        start_time (datetime-local): Start time of the event.
        end_time (datetime-local): End time of the event.
        recurrence (str): Recurrence pattern (e.g., daily, weekly).
        recurrence_end (date): Optional end date for recurrence.

    Methods:
        clean(): Validates that end_time is after start_time.
    """
    class Meta:
        model = Event
        #datetime-local is a HTML5 input type, to make date time show on fields
        widgets = {
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'recurrence': forms.Select(),
            'recurrence_end': DateInput(attrs={'type': 'date'}),
        }
        fields = '__all__'
        exclude = ['user']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and configure input formats for datetime fields.
        """
        self.user = kwargs.pop('user', None)
        super(EventForm, self).__init__(*args, **kwargs)

        # Filter the game queryset to only include the user's games
        if self.user:
            self.fields['game'].queryset = Game.objects.filter(user=self.user)
            
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)
    
    def clean(self):
        """
        Validates the form data, ensuring the end time is after the start time
        and recurrence_end is valid for recurring events.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        recurrence = cleaned_data.get("recurrence")
        recurrence_end = cleaned_data.get("recurrence_end")

        # Ensure end_time is after start_time
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "End time must be after start time.")

        # Ensure recurrence_end is provided if recurrence is not 'none'
        if recurrence != 'none' and not recurrence_end:
            self.add_error("recurrence_end", "Recurrence end date is required for recurring events.")

        # Ensure recurrence_end is after start_time
        if recurrence_end and start_time and recurrence_end < start_time.date():
            self.add_error("recurrence_end", "Recurrence end date cannot be before the start date.")

        if start_time and end_time:
            overlapping_events = Event.objects.filter(
                user=self.user,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk)

            if overlapping_events.exists():
                self.add_error(None, "This time slot is already booked.")
            

        return cleaned_data

class GameForm(forms.ModelForm):
    """
    A form for creating or updating games.

    Fields:
        release_date (date): Release date of the game.
        genre (str): Genre of the game (optional).
        platform (str): Gaming platform (optional).
        developer (str): Developer of the game (optional).
        color (str): Color code for the game.
        picture_link (str): URL of the game's image (optional).
    """
    class Meta:
        model = Game
        fields = '__all__'
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Optional'}),
            'genre': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'platform': forms.Select(attrs={'placeholder': 'Optional'}),
            'developer': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'color': forms.Select(attrs={'placeholder': 'Optional'}),
            'picture_link': forms.TextInput(attrs={'placeholder': 'Optional'}),
        }
        
class UsersForm(ModelForm):
    """
    A form for updating user information.

    Fields:
        username (str): Username of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        email (str): Email address of the user.
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    A custom form for changing the user's password.

    Fields:
        old_password (str): The user's current password.
        new_password1 (str): The new password entered by the user.
        new_password2 (str): Confirmation of the new password.

    Methods:
        clean_new_password2(): Ensures the new passwords match.
    """
    old_password = forms.CharField(label='Old Password', widget=forms.PasswordInput)
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')

    def clean_new_password2(self):
        """
        Validates that the two new password fields match.
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2
