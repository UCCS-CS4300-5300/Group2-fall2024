from ..models import *
from django import template
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm

register = template.Library()

"""
@register.filter(name = "find_cook")
def find_cook(user_id):
    #sets cook based off my table of USERS/chefs based on the user id
    cook = Users.objects.get(user=user_id)
    return cook.id
"""


# register the method
@register.filter(name="changeObjPerm")
# method that assigns the permission of a given recipe to a given user
def changeObjPerm(user_id, event_id):
    # gets the recipe based on the method's input
    event = Event.objects.get(id=Event_id)
    # gets the user based on the method's input
    user = User.objects.get(id=user_id)
    # assigns the user the 'saved_recipes'permission to the recipe
    # created in models.py
    assign_perm("saved_events", user, event)
