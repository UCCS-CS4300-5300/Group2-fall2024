from django.contrib import admin
from home.models import *

# Register your models here.
admin.site.register(Event)
admin.site.register(Game)
admin.site.register(FriendRequest)
admin.site.register(CalendarAccess)