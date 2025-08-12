from django.db import models

class Roles(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    USER = 'USER', 'User'
    ACCOUNT_MANAGER = 'ACCOUNT_MANAGER', 'Account Manager'
    MARKETING_MANAGER = 'MARKETING_MANAGER', 'Marketing Manager'
    CONTENT_WRITER = 'CONTENT_WRITER', 'Content Writer'
    GRAPHICS_DESIGNER = 'GRAPHICS_DESIGNER', 'Graphics Designer'
    # Add any other roles you need

# If you have specific permissions related to each role, you can define them here
ROLE_PERMISSIONS = {
    'ADMIN': ['can_add_user', 'can_delete_user', 'can_edit_user', 'can_view_reports'],
    'USER': ['can_view_profile'],
    'ACCOUNT_MANAGER': ['can_add_clients', 'can_view_clients', 'can_edit_clients'],
    'MARKETING_MANAGER': ['can_create_campaigns', 'can_edit_campaigns'],
    'CONTENT_WRITER': ['can_create_content', 'can_edit_content'],
    'GRAPHICS_DESIGNER': ['can_design_assets'],
}
