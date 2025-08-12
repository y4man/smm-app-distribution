from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import uuid
from django.utils.timezone import now
from client.models import Clients

# MEETINGS 
class Meeting(models.Model):
    MEETING_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    date = models.DateField(default=timezone.now)
    time = models.TimeField()
    meeting_name = models.CharField(max_length=255)
    meeting_link = models.URLField(max_length=500, blank=True, null=True)
    
    # New field: Store time zone information
    timezone = models.CharField(max_length=50, blank=True, null=True)

    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)
    team = models.ForeignKey('team.Team', on_delete=models.CASCADE, related_name='meetings', blank=True, null=True)
    marketing_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'Marketing Manager'}, blank=True, null=True)
    scheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='scheduled_meetings')
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.meeting_name} on {self.date} at {self.time}"

    class Meta:
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'
   
    
class History(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='histories')
    action = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)