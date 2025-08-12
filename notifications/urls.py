from django.urls import path
from . import views


urlpatterns = [

    # List all notifications for the logged-in user
    path('', views.NotificationListView.as_view(), name='notifications'),

    # allows the client to mark a specific notification as read.
    path('mark-read/<int:id>', views.MarkNotificationAsReadView.as_view(), name='notifications_mark_as_read'),
]