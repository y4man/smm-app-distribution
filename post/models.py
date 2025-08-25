from django.db import models

# Create your models here.
class PostAttribute(models.Model):
    ATTRIBUTE_TYPE_CHOICES = [
        ('post_type', 'Post Type'),
        ('post_cta', 'Post CTA'),
        ('post_category', 'Post Category'),
    ]
    created_by = models.ForeignKey('account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    attribute_type = models.CharField(max_length=50, choices=ATTRIBUTE_TYPE_CHOICES)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.attribute_type})"
    
