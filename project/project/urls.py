"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include



#Map a URL to a view, and 'include' allows referencing other URL configuration modules
urlpatterns = [
    # Maps the URL 'admin/' to Django's built-in admin interface
    path('admin/', admin.site.urls),
    # Maps the URL 'proxy/3000/' to the URL configurations defined in 'home.urls'
    path('proxy/3000/', include('home.urls')),
    path('', include('home.urls')),
    #path('/calendar', CalendarView.as_view(), name = 'calendar' ),

]
