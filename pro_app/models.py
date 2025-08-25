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

   
    
class History(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='histories')
    action = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)