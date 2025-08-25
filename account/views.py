from django.shortcuts import render
# Django core
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

# Django REST framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.exceptions import ValidationError 

# JWT (Simple JWT)
from rest_framework_simplejwt.tokens import RefreshToken

# HTTP responses
from django.http import JsonResponse

# Email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Token generator
from django.contrib.auth.tokens import default_token_generator

# Local Imports
from . import models



# Create your views here.
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow this view to be accessible to everyone
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # username and password validation (MA)
        if not username or not password:
            raise ValidationError("Both username and password are required..")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        # added user object validation..
        if not user:
            return Response(
            {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
                )

        # User Status Checks(MA)
        if not user.is_active:
            return JsonResponse({
                "Error" :"Account is inactive"
            }, status = status.HTTP_403_FORBIDDEN)
        
        if user is not None:
            user.last_login = timezone.now()
            user.save()
            
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            response = JsonResponse({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'role_display': user.get_role_display(),
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            })
            return response
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        

class SetPasswordView(APIView):

    # change to IsAuthenticated
    permission_classes = [IsAuthenticated]  # Allow any user to access this view without authentication

    def post(self, request, uidb64, token, *args, **kwargs):
        password = request.data.get('password')
        if len(password) < 8:
            return Response({
                "ERROR":"Password must be 8 "
            })

        try:
            # Decode the user id from the uidb64
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(models.CustomUser, pk=user_id)
        except (TypeError, ValueError, OverflowError, models.CustomUser.DoesNotExist):
            return Response({"error": "Invalid UID or user does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid token or token has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(password)
        user.is_active = True  # Activate user after password is set
        user.save()

        return Response({"message": "Password has been set successfully"}, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    # change to Allowany
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email exists in the system
        try:
            user = models.CustomUser.objects.get(email=email)
            username = user.username
        except models.CustomUser.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate a token and uidb64 to send in the email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the password reset URL
        reset_url = f"{settings.FRONTEND_DOMAIN}/set-password/{uid}/{token}"

        # Construct the email
        subject = "Reset Your Password"
        body = f"Hi {username},\n\nPlease reset your password using the following link:\n{reset_url}\n\nBest Regards,\nYour Team"

        message = MIMEMultipart()
        message['From'] = settings.EMAIL_HOST_USER
        message['To'] = email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        try:
            # Connect to SMTP server using Titan Email
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(settings.EMAIL_HOST_USER, email, message.as_string())
            server.quit()

            return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # added not new_password
        if new_password != confirm_password or not new_password or not confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the user id from the uidb64
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(models.CustomUser, pk=user_id)
        except (TypeError, ValueError, OverflowError, models.CustomUser.DoesNotExist):
            return Response({"error": "Invalid UID or user does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid token or token has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)