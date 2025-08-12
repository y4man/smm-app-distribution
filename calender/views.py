# Django imports
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.files.storage import default_storage
from urllib.parse import urlparse, unquote
import os
import tempfile

# DRF imports
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

# Local imports
from . import models
from . import serializers
from pro_app.permissions import IsMarketingDirector

# Other utilities
import logging
from datetime import datetime


# Create your views here.
class ClientCalendarListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ClientCalendarSerializer

    def get_queryset(self):
        client_id = self.kwargs.get('id')
        return models.ClientCalendar.objects.filter(client_id=client_id)

    def post(self, request, *args, **kwargs):
         # Check if the user is a marketing manager
        if request.user.role != 'marketing_manager':
            return Response({"error": "Only marketing managers can create calendars."}, status=status.HTTP_403_FORBIDDEN)

        client_id = self.kwargs.get('id')
        client = get_object_or_404(models.Clients, id=client_id)
        month_name = request.data.get('month_name')

        calendar = models.ClientCalendar.objects.create(client=client, month_name=month_name)
        serializer = self.get_serializer(calendar)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ClientCalendarRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ClientCalendarSerializer

    def get_queryset(self):
        client_id = self.kwargs.get('client_id')
        return models.ClientCalendar.objects.filter(client_id=client_id)

    def delete(self, request, *args, **kwargs):
        # Restrict deletion to marketing managers
        if request.user.role != 'marketing_manager':
            return Response({"error": "Only marketing managers can delete calendars."}, status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        # Restrict updates to certain roles
        if request.user.role not in ['marketing_manager', 'account_manager', 'content_writer', 'graphics_designer']:
            return Response({"error": "You are not authorized to update this calendar."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch the calendar instance
        calendar = self.get_object()

        # Perform partial updates without overriding existing values
        serializer = self.get_serializer(calendar, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientCalendarDateListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ClientCalendarDateSerializer
    def get_queryset(self):
        calendar_id = self.kwargs.get('calendar_id')
        return models.ClientCalendarDate.objects.filter(calendar_id=calendar_id)
    def post(self, request, *args, **kwargs):
        # Check if the user is a marketing manager
        if request.user.role != 'marketing_manager':
            return Response({"error": "Only marketing managers can create row for next dates."}, status=status.HTTP_403_FORBIDDEN)
        calendar_id = self.kwargs.get('calendar_id')
        calendar = get_object_or_404(models.ClientCalendar, id=calendar_id)
        data = request.data.copy()  # Get a mutable copy of request data
        # Add the calendar reference to the payload
        data['calendar'] = calendar.id
        # Use the serializer to validate and save the data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientCalendarDateRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ClientCalendarDateSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        calendar_id = self.kwargs.get('calendar_id')
        return models.ClientCalendarDate.objects.filter(calendar_id=calendar_id)

    # WITH SUPABASE 
    # def put(self, request, *args, **kwargs):
    #     calendar_date = self.get_object()
    #     user_role = request.user.role

    #     # Role-based field restrictions
    #     if user_role in [
    #         'marketing_manager', 'marketing_assistant',
    #         'content_writer', 'graphics_designer', 'marketing_director'
    #     ]:
    #         for fld in ['client_approval', 'comments']:
    #             if fld in request.data:
    #                 return Response(
    #                     {"error": f"{user_role} is not allowed to update {fld}."},
    #                     status=status.HTTP_403_FORBIDDEN
    #                 )

    #     # Filter allowed data
    #     allowed = self.get_allowed_fields_by_role(user_role)
    #     filtered_data = {k: v for k, v in request.data.items() if k in allowed}

    #     # graphics_designer: handle creatives upload
    #     if user_role == 'graphics_designer':
    #         # ─── Single-index replacement ──────────────────────────────────────
    #         if 'creative_index' in request.data and 'creatives' in request.FILES:
    #             new_file = request.FILES['creatives']

    #             # 1) Validate type
    #             ctype = new_file.content_type
    #             if not (ctype.startswith('image/') or ctype.startswith('video/')):
    #                 return Response(
    #                     {"error": f"Invalid file type {ctype}. Only images/videos allowed."},
    #                     status=status.HTTP_400_BAD_REQUEST
    #                 )

    #             # 2) Parse index
    #             try:
    #                 index = int(request.data['creative_index'])
    #             except ValueError:
    #                 return Response(
    #                     {"error": "Invalid creative_index format."},
    #                     status=status.HTTP_400_BAD_REQUEST
    #                 )

    #             # 3) Remove old file
    #             old_url = calendar_date.creatives[index]
    #             parsed = urlparse(old_url)
    #             key_old = unquote(parsed.path.lstrip('/'))
    #             try:
    #                 storage.remove([key_old])
    #             except Exception:
    #                 pass

    #             # 4) Stream upload new file
    #             tmp_path = None
    #             try:
    #                 with tempfile.NamedTemporaryFile(delete=False) as tmp:
    #                     for chunk in new_file.chunks():
    #                         tmp.write(chunk)
    #                     tmp_path = tmp.name

    #                 key = f"creatives/{new_file.name}"
    #                 try:
    #                     storage.upload(
    #                         file=tmp_path,
    #                         path=key,
    #                         file_options={
    #                             "content-type": ctype,
    #                             "cache-control": "3600",
    #                             "upsert": False
    #                         }
    #                     )
    #                 except StorageApiError as exc:
    #                     raw = exc.args[0] if exc.args else {}
    #                     if isinstance(raw, dict) and raw.get('statusCode') == 409:
    #                         storage.update(
    #                             file=tmp_path,
    #                             path=key,
    #                             file_options={"content-type": ctype}
    #                         )
    #                     else:
    #                         msg = raw.get('message', str(exc)) if isinstance(raw, dict) else str(exc)
    #                         return Response(
    #                             {"creatives": [msg]},
    #                             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #                         )
    #             finally:
    #                 if tmp_path and os.path.exists(tmp_path):
    #                     os.unlink(tmp_path)

    #             # 5) Save new URL
    #             new_url = (
    #                 f"{settings.SUPABASE_URL}/storage/v1/object/public/"
    #                 f"{settings.SUPABASE_BUCKET}/{key}"
    #             )
    #             calendar_date.creatives[index] = new_url
    #             calendar_date.save()
    #             serializer = self.get_serializer(calendar_date, context={'request': request})
    #             return Response(serializer.data, status=status.HTTP_200_OK)

    #         # ─── Full-list replacement ────────────────────────────────────────
    #         files = request.FILES.getlist('creatives')
    #         if files:
    #             # delete old
    #             for old_url in calendar_date.creatives or []:
    #                 parsed = urlparse(old_url)
    #                 key_old = unquote(parsed.path.lstrip('/'))
    #                 try:
    #                     storage.remove([key_old])
    #                 except Exception:
    #                     pass

    #             new_urls = []
    #             for f in files:
    #                 # validate type
    #                 ctype = f.content_type
    #                 if not (ctype.startswith('image/') or ctype.startswith('video/')):
    #                     return Response(
    #                         {"error": f"Invalid file type {ctype}. Only images/videos allowed."},
    #                         status=status.HTTP_400_BAD_REQUEST
    #                     )

    #                 tmp_path = None
    #                 try:
    #                     with tempfile.NamedTemporaryFile(delete=False) as tmp:
    #                         for chunk in f.chunks():
    #                             tmp.write(chunk)
    #                         tmp_path = tmp.name

    #                     key = f"creatives/{f.name}"
    #                     try:
    #                         storage.upload(
    #                             file=tmp_path,
    #                             path=key,
    #                             file_options={
    #                                 "content-type": ctype,
    #                                 "cache-control": "3600",
    #                                 "upsert": False
    #                             }
    #                         )
    #                     except StorageApiError as exc:
    #                         raw = exc.args[0] if exc.args else {}
    #                         if isinstance(raw, dict) and raw.get('statusCode') == 409:
    #                             storage.update(
    #                                 file=tmp_path,
    #                                 path=key,
    #                                 file_options={"content-type": ctype}
    #                             )
    #                         else:
    #                             msg = raw.get('message', str(exc)) if isinstance(raw, dict) else str(exc)
    #                             return Response(
    #                                 {"creatives": [msg]},
    #                                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #                             )
    #                 finally:
    #                     if tmp_path and os.path.exists(tmp_path):
    #                         os.unlink(tmp_path)

    #                 new_urls.append(
    #                     f"{settings.SUPABASE_URL}/storage/v1/object/public/"
    #                     f"{settings.SUPABASE_BUCKET}/{key}"
    #                 )

    #             filtered_data['creatives'] = new_urls

           
    #     # no permitted fields?
    #     if not filtered_data and not request.FILES:
    #         return Response(
    #             {"error": f"{user_role} is not allowed to update the provided fields."},
    #             status=status.HTTP_403_FORBIDDEN
    #         )

    #     # Normal partial update
    #     serializer = serializers.ClientCalendarDateSerializer(
    #         calendar_date,
    #         data=filtered_data,
    #         partial=True,
    #         context={'request': request}
    #     )
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # WITHOUT SUPABASE JUST CREATIVES urls
    def put(self, request, *args, **kwargs):
        calendar_date = self.get_object()
        user_role = request.user.role

        # Role-based field restrictions
        if user_role in [
            'marketing_manager', 'marketing_assistant',
            'content_writer', 'graphics_designer', 'marketing_director'
        ]:
            for fld in ['client_approval', 'comments']:
                if fld in request.data:
                    return Response(
                        {"error": f"{user_role} is not allowed to update {fld}."},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Filter allowed data
        allowed = self.get_allowed_fields_by_role(user_role)
        filtered_data = {k: v for k, v in request.data.items() if k in allowed}

        # graphics_designer: replace creatives list
        if user_role == 'graphics_designer' and 'creatives' in request.data:
            # Expecting a JSON array of URLs from frontend
            filtered_data['creatives'] = request.data['creatives']

        # no permitted fields?
        if not filtered_data:
            return Response(
                {"error": f"{user_role} is not allowed to update the provided fields."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Perform partial update
        serializer = self.get_serializer(
            calendar_date,
            data=filtered_data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    def delete(self, request, *args, **kwargs):
        if request.user.role != 'marketing_manager':
            return Response(
                {"error": "Only marketing managers can delete calendar dates."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def get_allowed_fields_by_role(self, role):
        if role in ['account_manager', 'user']:
            return ['client_approval', 'comments']
        elif role == 'marketing_manager':
            return [
                'post_count', 'type', 'category', 'cta',
                'strategy', 'resource', 'internal_status',
                'collaboration'
            ]
        elif role == 'content_writer':
            return ['tagline', 'caption', 'hashtags', 'e_hooks', 'creatives_text']
        elif role == 'graphics_designer':
            return ['creatives']
        return []

#CALENDER DATA FOR CLIENT
class ClientCalendarByMonthView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, client_business_name, account_manager_username, month_name, *args, **kwargs):
        # Ensure the client exists by business name
        client = get_object_or_404(models.Clients, business_name=client_business_name)
        # Check if the account manager with the specified username is associated with the client
        print(account_manager_username)
        if not models.CustomUser.objects.filter(username=account_manager_username, clients=client).exists():
            return Response(
                {"error": "This account manager is not associated with the specified client."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Retrieve the calendars for the specific client and month_name
        calendars = models.ClientCalendar.objects.filter(client=client, month_name__icontains=month_name)
        # If no calendars are found for the client in the given month, return a 404 response
        if not calendars.exists():
            return Response(
                {"error": f"No calendar found for client {client.business_name} in the month {month_name}."},
                status=status.HTTP_404_NOT_FOUND
            )
        # Get all the calendar dates related to the found calendars
        calendar_dates = models.ClientCalendarDate.objects.filter(calendar__in=calendars)
        # Serialize the result
        serializer = serializers.FilteredClientCalendarDateSerializer(calendar_dates, many=True)
        # Return the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)
