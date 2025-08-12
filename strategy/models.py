from django.db import models
from django.conf import settings
from django.utils import timezone


#strategy
class Strategy(models.Model):
    client = models.ForeignKey('client.Clients', on_delete=models.CASCADE, related_name='client_strategies')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    strategies = models.JSONField(default=dict, help_text="A JSON object to store strategies.")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ClientStrategy for {self.client.business_name}"
