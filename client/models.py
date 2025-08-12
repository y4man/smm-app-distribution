from django.apps import apps
from django.db import models
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .constant import TASK_TYPE_CHOICES


# Create your models here.
class Clients(models.Model):
    # Foreign Keys 
    team = models.ForeignKey('team.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    account_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_clients')
    # Business Info
    business_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    business_details = models.TextField(blank=True)
    brand_key_points = models.TextField(blank=True)
    business_address = models.CharField(max_length=255)
    brand_guidelines_link = models.URLField(blank=True)
    business_whatsapp_number = models.CharField(max_length=20, blank=True)
    goals_objectives = models.TextField(blank=True)
    business_email_address = models.EmailField()
    target_region = models.CharField(max_length=255, blank=True)
    # brand_guidelines_notes = models.TextField(blank=True)
    BUSINESS_OFFERINGS_CHOICES = [
        ('services', 'Services'),
        ('products', 'Products'),
        ('services_products', 'Services Products'),
        ('other', 'Other'),
    ]
    business_offerings = models.CharField(
        max_length=20,
        choices=BUSINESS_OFFERINGS_CHOICES,
        default='services'
    )
    # Social Media and Web Info
    ugc_drive_link = models.URLField(blank=True)
    business_website = models.URLField(blank=True)
    # Social Handles
    social_handles = models.JSONField(
        blank=True,
        default=dict,  # Use a dictionary to store platform and URL pairs
        help_text="Stores social handles as key-value pairs, e.g., {'facebook': 'https://facebook.com', 'instagram': 'https://instagram.com'}"
    )
    additional_notes = models.TextField(blank=True)
    # Proposal Information
    proposal_pdf = models.FileField(upload_to='proposals/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    PROPOSAL_APPROVAL_CHOICES = [
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('changes_required', 'Changes Required'),
    ]
    proposal_approval_status = models.CharField(max_length=20, choices=PROPOSAL_APPROVAL_CHOICES, null=True, blank=True)
    # Web Development Data
    # WEBSITE_TYPE_CHOICES = [
    #     ('ecommerce', 'Ecommerce'),
    #     ('services', 'Offer Services'),
    # ]
    MEMBERSHIP_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    YES_NO_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    # Client WebDevData Fields
    # website_type = models.CharField(max_length=20, choices=WEBSITE_TYPE_CHOICES, default='none')
    num_of_products = models.IntegerField(null=True, blank=True)  # Only for ecommerce
    membership = models.CharField(max_length=4, choices=MEMBERSHIP_CHOICES, default='none')
    website_structure = models.TextField(blank=True, null=True)
    design_preference = models.TextField(blank=True, null=True)
    domain = models.CharField(max_length=4, choices=YES_NO_CHOICES, default='none')
    domain_info = models.CharField(max_length=255, blank=True, null=True)  # Only if domain is yes
    hosting = models.CharField(max_length=4, choices=YES_NO_CHOICES, default='none')
    hosting_info = models.CharField(max_length=255, blank=True, null=True)  # Only if hosting is yes
    # graphic_assets = models.CharField(max_length=4, choices=YES_NO_CHOICES, default='none')
    # is_regular_update = models.CharField(max_length=4, choices=YES_NO_CHOICES, default='none')
    is_self_update = models.CharField(max_length=4, choices=YES_NO_CHOICES, default='none')
    # additional_webdev_notes = models.TextField(blank=True, null=True)
    # Client Type
    CLIENT_TYPE_CHOICES = [
        ('social_media', 'Social Media'),
        ('web_development', 'Web Development'),
        ('both', 'Both'),
    ]
    client_type = models.CharField(
        max_length=20,
        choices=CLIENT_TYPE_CHOICES,
        default='both',
        help_text="Indicates the type of service(s) selected by the client."
    )
    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)
    def clean(self):
        """
        Custom validation for the `social_handles` field to ensure no empty values.
        """
        if self.social_handles:
            for platform, url in self.social_handles.items():
                if not url:
                    raise ValidationError({
                        'social_handles': f"The URL for platform '{platform}' cannot be empty."
                    })
    def __str__(self):
        return self.business_name
    
class ClientsPlan(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='client_plans')
    
    # Plan type field (e.g., Standard, Advanced)
    plan_type = models.CharField(max_length=255, blank=True, null=True)
    
    # Attributes of the plan (e.g., number of posts, reels, etc.)
    attributes = models.JSONField(default=dict, blank=True, help_text="Attributes of the plan")
    
    # Platforms on which the plan will be implemented (e.g., Facebook, Instagram)
    platforms = models.JSONField(default=dict, blank=True, help_text="Platforms like Facebook, Instagram")
    
    # Add-ons or extra features associated with the plan
    # add_ons = models.JSONField(default=dict, blank=True, help_text="Additional add-ons for the plan")
    
    # Grand total price for the plan
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Timestamps for when the plan was created and last updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client.business_name} - {self.plan_type} Plan"
    
class ClientInvoices(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='clients_invoices')
    billing_from = models.TextField(null=True, blank=True)
    billing_to = models.TextField(null=True, blank=True)
    invoice = models.FileField(upload_to='invoices/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    INVOICE_STATUS_CHOICES=[
        ('paid', 'PAID'),
        ('unpaid', 'UNPAID'),
        ('changes_required', 'CHANGES REQUIRED'),
        ('wait_for_approval', 'WAITING FOR APPROVAL')
    ]
    submission_status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='wait_for_approval', null=True, blank=True)
    payment_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ClientWorkflowState(models.Model):
    client = models.OneToOneField('Clients', on_delete=models.CASCADE)
    current_step = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow for {self.client.business_name} - Current Step: {self.current_step}"




# Created due to error in view file (ClientWebDevDataDetailView)
class ClientWebDevData(models.Model):
    client = models.OneToOneField('Clients', on_delete=models.CASCADE, related_name='webdev_data')

    WEBSITE_TYPE_CHOICES = [
        ('ecommerce', 'Ecommerce'),
        ('services', 'Services'),
        ('portfolio', 'Portfolio'),
        ('other', 'Other')
    ]

    YES_NO_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No')
    ]

    MEMBERSHIP_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    website_type = models.CharField(max_length=20, choices=WEBSITE_TYPE_CHOICES, default='services')
    num_of_products = models.IntegerField(null=True, blank=True)  # for ecommerce websites
    membership = models.CharField(max_length=3, choices=MEMBERSHIP_CHOICES, default='no')
    website_structure = models.TextField(blank=True, null=True)
    design_preference = models.TextField(blank=True, null=True)
    domain = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')
    domain_info = models.CharField(max_length=255, blank=True, null=True)
    hosting = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')
    hosting_info = models.CharField(max_length=255, blank=True, null=True)
    is_self_update = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')
    additional_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class ClientStatus(models.Model):
    client = models.OneToOneField('client.Clients', on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='In Progress')

    def __str__(self):
        return f"Status for {self.client.business_name}: {self.status}"