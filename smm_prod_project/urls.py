"""
URL configuration for smm_prod_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Include API paths from pro_app
    path('api/pro_app/', include('pro_app.urls')), 

    # Include API paths from meeting
    path('api/meetings/', include('meeting.urls')), 

    # Include API paths from user
    path('api/users/', include('user.urls')),

    # Include API paths from account
    path('api/', include('account.urls')),  

    # Include API path from client
    path('api/clients/', include('client.urls')),  

    # Include API path from Plan
    path('api/plans/', include('plan.urls')), 

    # Include API path from Calender
    path('api/calendars/', include('calender.urls')), 

    # Include API path from Team
    path('api/teams/', include('team.urls')),

    # Include API path from post
    path('api/post-attributes/', include('post.urls')) ,

    # Include API path from task
    path('api/tasks/', include('task.urls')) ,
    
    # Include API path from strategy
    path('api/strategy/', include('strategy.urls')),  
    
    # Include API path from threadNotes
    path('api/threadsnotes/', include('threadNotes.urls')), 
   
    # Include API path from notification
    path('api/notification/', include('notifications.urls'))  
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)