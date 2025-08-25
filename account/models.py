from arrow import now
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import os
from pro_app.storage_backends import SupabaseStorage



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with the given email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        
        if not password:
            raise ValueError("The Password filed must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

def profile_image_upload(instance, filename):
    """Ensure unique filenames to prevent browser caching."""
    ext = filename.split('.')[-1]  # Extract file extension
    new_filename = f"profile_{instance.id}_{now().strftime('%Y%m%d%H%M%S')}.{ext}"  # Unique timestamp filename
    return os.path.join("profiles/", new_filename)



class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(
        db_index= True,
    max_length=20,
    choices=[
        ('user', 'User'),  # Add this if you want 'user' as a role
        ('marketing_director', 'Marketing Director'),
        ('marketing_manager', 'Marketing Manager'),
        ('marketing_assistant', 'Marketing Assistant'),
        ('graphics_designer', 'Graphics Designer'),
        ('content_writer', 'Content Writer'),
        ('account_manager', 'Account Manager'),
        ('accountant', 'Accountant'),
    ],
    default='user'
)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    agency_name = models.CharField(max_length=255, blank=True, null=True)
    # new field for agency slug
    # we can use models.slugField
    agency_slug = models.CharField(max_length=255, blank=True, null=True)
    # new field for agency logo
    # should be a foreign key (changed to foreign key)
    acc_mngr_id = models.IntegerField(null=True, blank=True) 
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)


    profile = models.FileField(upload_to='profiles/', storage=SupabaseStorage(), null=True, blank=True)
    
    # Adding the relationship to Plans
    # due to circular dependency
    # plans = models.ManyToManyField('plan.Plans', related_name="assigned_account_managers", blank=True)
    USERNAME_FIELD = 'username'  # This allows logging in using the username
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:  # If username is not set
            base_username = self.email.split('@')[0]  # Generate base username from email
            new_username = base_username
            counter = 1
            # Ensure the username is unique
            while CustomUser.objects.filter(username=new_username).exists():
                new_username = f"{base_username}{counter}"
                counter += 1
            self.username = new_username
        super().save(*args, **kwargs)  # Call the real save() method

    def get_full_name(self):
        """Return the first_name and last_name, concatenated."""
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.username} - {self.role}"
        # return self.username
    

