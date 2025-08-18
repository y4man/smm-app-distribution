from django.db import models
from django.conf import settings

# Create your models here.
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_return', 'Task Return'),
        ('task_declined', 'Task Declined'),
        ('thread_notify', 'Thread Notification'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=255, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # changed to foreign key
    client_id = models.ForeignKey('client.Clients', on_delete=models.SET_NULL, null=True, blank=True)
    # Removed the client name because we have added the client_id as foreign key
    # client_name = models.CharField(max_length=255, null=True, blank=True)

    # Task type should be remove (can be included in msg)
    task_type = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Notification for {self.recipient} - {self.message[:50]}"
