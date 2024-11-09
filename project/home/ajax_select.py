from ajax_select import register, LookupChannel
from .models import User

@register('user')
class UserLookup(LookupChannel):

    model = User

    def get_query(self, q, request):
       return User.objects.filter(username__icontains=q)

    def format_item_display(self, item):
        #Format the display of each item in the results list.
        return f"<span class='user-search-item'>{item.username}</span>"