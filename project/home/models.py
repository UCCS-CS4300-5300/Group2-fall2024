from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, default = None)

    class Meta:
        permissions = [("saved_events", "can save events")]

    @property
    def get_html_url(self):
        url = reverse('event_edit', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'


User = get_user_model()