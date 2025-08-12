from django.db import models
from account.models import CustomUser


# USERS 

class UserOTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="otp")
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}: {self.otp}"