# Python standard library
import os
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Django core
from django.conf import settings
from django.shortcuts import render
from django.utils.timezone import now
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

# Django REST framework
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Third-party
from storage3.exceptions import StorageApiError

# App-specific
from account.serializers import UserSerializer
from account import models
from pro_app import storage
from pro_app.permissions import IsMarketingDirector
from . import serializers

# Create your views here.
class ListUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]  # Change to `AllowAny` if needed
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """
        Exclude users with the role 'marketing_director'.
        """
        return models.CustomUser.objects.exclude(role='marketing_director')
      
class UsersView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]  # Set appropriate permissions
    serializer_class = UserSerializer
    queryset = models.CustomUser.objects.all()
    lookup_field = 'id'

class UserListByRoleView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    serializer_class = serializers.UserRoleSerializer

    def get_queryset(self):
        # Get the 'role' parameter from the request's query params
        role = self.request.query_params.get('role')
        if role:
            return models.CustomUser.objects.filter(role=role, is_active=True)
        else:
            return models.CustomUser.objects.none()  # Return an empty queryset if no role is provided

class AdminCreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        role = data.get('role')

        agency_name = data.get('agency_name')
        agency_slug = data.get('agency_slug')

        # Check if the role is 'account_manager' and validate both `agency_name` and `agency_slug`
        if role == 'account_manager' and (not agency_name or not agency_slug):
            return Response({"message": "Both Agency Name and Agency Slug are required for Account Managers."}, status=status.HTTP_400_BAD_REQUEST)

        if models.CustomUser.objects.filter(email=email).exists():
            return Response({"message": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        # Create a user without a password
        user = models.CustomUser.objects.create(email=email, first_name=first_name, last_name=last_name, role=role,agency_name=agency_name, is_active=False)
        user.save()
        
        # Generate token for setting password
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        # Build the password reset URL
        set_password_url = f"{settings.FRONTEND_DOMAIN}/set-password/{uid}/{token}"
        # Manually construct the email
        subject = "Set your password"
        body = f"Hi {first_name}, please set your password using the following link: {set_password_url}"
        message = MIMEMultipart()

        # Do not use hardcoded email.
        message['From'] = 'danish@mysocialmarketingexpert.com'
        message['To'] = email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        try:
            # Connect to the SMTP server using smtplib
            server = smtplib.SMTP('smtp.mailgun.org', 587)
            server.starttls()
            server.login('danish@mysocialmarketingexpert.com', 'Search$fs8@')
            server.sendmail('danish@mysocialmarketingexpert.com', email, message.as_string())
            server.quit()
            return Response({"message": "User created and email sent to set password"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            user.delete()
            return Response({"message": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# PROFILE 
class ProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserSerializer

    def get_object(self):
        return self.request.user

    

class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser,JSONParser )

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        profile_file = self.request.FILES.get('profile')
        user = self.get_object()

        if profile_file:
            # Handle file upload to Supabase
            tmp_path = None
            try:
                # Save upload to temp file
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in profile_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # Generate unique filename
                ext = profile_file.name.split('.')[-1]
                new_filename = f"profile_{user.id}_{now().strftime('%Y%m%d%H%M%S')}.{ext}"
                path_in_bucket = f"profiles/{new_filename}"

                # Remove old file if exists
                old_key = user.profile.name if user.profile else None
                if old_key:
                    try:
                        storage.remove([old_key])
                    except Exception:
                        pass

                # Upload new file
                try:
                    storage.upload(
                        file=tmp_path,
                        path=path_in_bucket,
                        file_options={"content-type": profile_file.content_type}
                    )
                except StorageApiError as exc:
                    msg = str(exc)
                    if exc.args and isinstance(exc.args[0], dict):
                        msg = exc.args[0].get("message", msg)
                    raise serializers.ValidationError({"profile": [msg]})

                # Update user profile path
                user.profile = path_in_bucket
                user.save()

            finally:
                # Clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # Update other fields
        serializer.save()
