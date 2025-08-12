from django.db import models
from django.conf import settings

# Create your models here.
class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('assign_team', 'Assign Team to Client'),
        ('create_proposal', 'Create Proposal'),
        ('approve_proposal', 'Approve Proposal'),
        ('schedule_brief_meeting', 'Schedule Brief Meeting'),
        ('create_strategy', 'Create Strategy'),
        ('content_writing', 'Content Writing'),
        ('approve_content_by_marketing_manager', 'Approve Content by Marketing Manager'),
        ('approve_content_by_account_manager', 'Approve Content by Account Manager'),
        ('creatives_design', 'Creatives Designing'),
        ('approve_creatives_by_marketing_manager', 'Approve Creatives by Marketing Manager'),
        ('approve_creatives_by_account_manager', 'Approve Creatives by Account Manager'),
        ('schedule_onboarding_meeting', 'Schedule Onboarding Meeting'),
        ('onboarding_meeting', 'Onboarding Meeting'),
        ('smo_scheduling', 'SMO & Scheduling'),
        ('invoice_submission', 'Invoice Submission'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('monthly_report', 'Monthly Reporting'),
    ]

    client = models.ForeignKey('client.Clients', on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_type} for {self.client.business_name} - Assigned to: {self.assigned_to.username}"
    

class CustomTask(models.Model):
    task_name = models.TextField()
    task_description = models.TextField()
    
    # Change related_name to avoid conflict
    assign_to_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_assigned_tasks')

    task_status = models.BooleanField(default=False)  # Fix default value (use False instead of 'none')
    task_created_at = models.DateTimeField(auto_now_add=True)
    task_updated_at = models.DateTimeField(auto_now=True)

    client_id = models.ForeignKey('client.Clients', on_delete=models.CASCADE, related_name='client_tasks')
    
    # New field: File upload
    custom_task_file = models.FileField(upload_to='task_files/', null=True, blank=True)
    

    def __str__(self):
        return f"{self.task_name} - Assigned to {self.assign_to_id.username}"


