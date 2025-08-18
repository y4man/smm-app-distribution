from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import models
from client.models import Clients

# Create your models here.
class ClientCalendar(models.Model):
    CONTENT_STATUS_CHOICES = [
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approve', 'Approve'),
        ('changes_required', 'Changes Required')
    ]
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='calendars')
    created_at = models.DateTimeField(default=timezone.now)
    month_name = models.TextField()
    strategy_completed = models.BooleanField(default=False)
    content_completed = models.BooleanField(default=False)
    creatives_completed = models.BooleanField(default=False)
    mm_content_completed = models.CharField(max_length=20, choices=CONTENT_STATUS_CHOICES, default='waiting_for_approval', help_text="Tracks the approval status of the content by marketing manager.")
    acc_creative_completed = models.CharField(max_length=20, choices=CONTENT_STATUS_CHOICES, default='waiting_for_approval', help_text="Tracks the approval status of the creatives by account manager.")
    mm_creative_completed = models.CharField(max_length=20, choices=CONTENT_STATUS_CHOICES, default='waiting_for_approval', help_text="Tracks the approval status of the creatives by marketing manager.")
    acc_content_completed = models.CharField(max_length=20, choices=CONTENT_STATUS_CHOICES, default='waiting_for_approval', help_text="Tracks the approval status of the content by account manager.")
    
    smo_completed = models.BooleanField(default=False, help_text="Indicates if the SMO task is completed for the month.")
    monthly_reports = models.FileField(upload_to='reports/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    
    def __str__(self):
        return f"{self.client} - {self.month_name}"

class ClientCalendarDate(models.Model):
    calendar = models.ForeignKey(ClientCalendar, on_delete=models.CASCADE, related_name='dates')
    created_at = models.DateTimeField(default=timezone.now)
    date = models.DateField()
    post_count = models.IntegerField(default=0)

    # Changed back to CharField to store a single value
    type = models.CharField(max_length=20, blank=True, null=True)  # Single post type
    category = models.CharField(max_length=100, blank=True, null=True)  # Single category
    cta = models.CharField(max_length=255, blank=True, null=True, verbose_name='Call to Action')  # Single CTA
    
    resource = models.TextField(blank=True, null=True, help_text="Strategy description for this post date")
    tagline = models.CharField(max_length=255, blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    hashtags = models.TextField(blank=True, null=True, help_text="Use commas to separate hashtags")
    e_hooks = models.TextField(blank=True, null=True, verbose_name='Engagement Hooks')
    creatives_text = models.TextField(blank=True, null=True, help_text="Describe the creatives text")
    creatives = models.JSONField(default=list, blank=True, help_text="List of supabase URLs for multiple creatives (images/videos).")


    # Internal status stored as a JSON field
    internal_status = models.JSONField(default=dict, blank=True)
    # Client approval stored as a JSON field
    client_approval = models.JSONField(default=dict, blank=True)

    comments = models.TextField(blank=True, null=True)
    collaboration = models.TextField(blank=True, null=True)

    # Validation for internal_status and client_approval fields
    def clean(self):
        allowed_values = ['content_approval', 'creatives_approval']

        # Validate internal_status
        if not isinstance(self.internal_status, dict):
            raise ValidationError("internal_status must be a JSON object.")
        if len(self.internal_status.keys()) > 2:
            raise ValidationError("internal_status can only contain two fields: 'content_approval' and 'creatives_approval'.")
        for key in self.internal_status.keys():
            if key not in allowed_values:
                raise ValidationError(f"Invalid value '{key}' in internal_status. Only 'content_approval' and 'creatives_approval' are allowed.")

        # Validate client_approval
        if not isinstance(self.client_approval, dict):
            raise ValidationError("client_approval must be a JSON object.")
        if len(self.client_approval.keys()) > 2:
            raise ValidationError("client_approval can only contain two fields: 'content_approval' and 'creatives_approval'.")
        for key in self.client_approval.keys():
            if key not in allowed_values:
                raise ValidationError(f"Invalid value '{key}' in client_approval. Only 'content_approval' and 'creatives_approval' are allowed.")

    def __str__(self):
        return f"{self.calendar} - {self.date}"

    class Meta:
        verbose_name = 'Client Calendar Date'
        verbose_name_plural = 'Client Calendar Dates'
