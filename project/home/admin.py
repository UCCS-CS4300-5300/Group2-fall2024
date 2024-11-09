from django.contrib import admin
from home.models import Event, Game, FriendRequest

# Register your models here.
admin.site.register(Event)
admin.site.register(Game)
admin.site.register(FriendRequest)