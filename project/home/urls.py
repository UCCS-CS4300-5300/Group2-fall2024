from django.urls import path
from .views import index, Login, Register
from django.contrib.auth import views as auth

urlpatterns = [
    path('', index, name='index'),
    path('login/',  Login, name ='login'),
    #path('logout/', auth.LogoutView.as_view(template_name ='logout.html'), name ='logout'),
    path('register/', Register, name ='register'),
]
