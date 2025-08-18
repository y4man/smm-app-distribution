from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

# Create your models here.
class Plans(models.Model):
    plan_name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Plan Pricing fields (merged from PlanPricing)
    pricing_attributes = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for attributes like reel:100, post:200, etc.")
    pricing_platforms = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for platforms like facebook:200, instagram:150, etc.")

    # Standard Plan fields
    standard_attributes = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for attributes like reel:100, post:200, etc.")
    standard_plan_inclusion = models.TextField(blank=True, null=True, help_text="Details of what's included in the standard plan")
    standard_netprice = models.IntegerField(help_text="Net price for the standard plan")

    # Advanced Plan fields
    advanced_attributes = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for attributes like reel:100, post:200, etc.")
    advanced_plan_inclusion = models.TextField(blank=True, null=True, help_text="Details of what's included in the advanced plan")
    advanced_netprice = models.IntegerField(help_text="Net price for the advanced plan")

    # Additional fields

    # Relationship with account managers (many-to-many)
    account_managers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="assigned_plans", blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.plan_name

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"


