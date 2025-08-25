from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from pytz import timezone as pytz_timezone
from datetime import datetime, timedelta
from . import models, serializers

# Optimized Code
class MeetingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.MeetingSerializer
    
    def get_queryset(self):
        return models.Meeting.objects.select_related(
            'client', 'team', 'scheduled_by', 'marketing_manager'
        ).order_by('-date', '-time')

    def perform_create(self, serializer):
        if self.request.user.role != 'account_manager':
            raise PermissionDenied("Only account managers can schedule meetings.")

        client = serializer.validated_data.get('client')
        if not client:
            raise ValidationError({"error": "Client is required."})

        assignee_type = self.request.data.get('assignee_type')
        assignee = self._validate_assignee(client, assignee_type)
        
        # Time handling
        date = serializer.validated_data['date']
        time = serializer.validated_data['time']
        timezone_str = serializer.validated_data['timezone']
        
        utc_datetime = self._convert_to_utc(date, time, timezone_str)
        date_utc, time_utc = self._resolve_time_conflict(utc_datetime.date(), utc_datetime.time())

        serializer.save(
            scheduled_by=self.request.user,
            date=date_utc,
            time=time_utc,
            timezone=timezone_str,
            **assignee
        )

    def _validate_assignee(self, client, assignee_type):
        if not client.team:
            raise ValidationError({"error": "No team assigned to this client."})
            
        if assignee_type == 'team':
            return {'team': client.team}
        elif assignee_type == 'marketing_manager':
            manager = client.team.memberships.filter(
                user__role='marketing_manager'
            ).first()
            if not manager:
                raise ValidationError({"error": "No marketing manager found for this team."})
            return {'marketing_manager': manager.user}
        else:
            raise ValidationError({"error": "Invalid assignee type. Must be 'team' or 'marketing_manager'."})

    def _convert_to_utc(self, date, time, timezone_str):
        user_timezone = pytz_timezone(timezone_str)
        return user_timezone.localize(datetime.combine(date, time)).astimezone(pytz_timezone('UTC'))

    def _resolve_time_conflict(self, date, time):
        conflict = models.Meeting.objects.filter(date=date, time=time).exists()
        if conflict:
            new_time = (datetime.combine(date, time) + timedelta(minutes=20)).time()
            return date, new_time
        return date, time

class MeetingRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.SpecificMeetingSerializer
    
    def get_queryset(self):
        return models.Meeting.objects.select_related(
            'client', 'team', 'scheduled_by', 'marketing_manager'
        )

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs.get("pk"))

    def retrieve(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(meeting)
        
        # Time conversion
        meeting_tz = pytz_timezone(meeting.timezone)
        meeting_utc = pytz_timezone('UTC').localize(
            datetime.combine(meeting.date, meeting.time)
        )
        local_time = meeting_utc.astimezone(meeting_tz)
        
        response_data = serializer.data
        response_data.update({
            'date': local_time.strftime('%Y-%m-%d'),
            'time': local_time.strftime('%H:%M:%S'),
            'details': [
                detail for detail in [
                    meeting.team.name if meeting.team else None,
                    meeting.scheduled_by.role if meeting.scheduled_by else None,
                    meeting.marketing_manager.role if meeting.marketing_manager else None
                ] if detail is not None
            ]
        })
        return Response(response_data)

    def update(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(meeting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Handle time updates
        if 'date' in serializer.validated_data or 'time' in serializer.validated_data:
            date = serializer.validated_data.get('date', meeting.date)
            time = serializer.validated_data.get('time', meeting.time)
            timezone_str = serializer.validated_data.get('timezone', meeting.timezone)
            
            utc_datetime = self._convert_to_utc(date, time, timezone_str)
            date_utc, time_utc = self._resolve_update_conflict(
                utc_datetime.date(), 
                utc_datetime.time(),
                meeting.pk
            )
            
            meeting.date = date_utc
            meeting.time = time_utc
            if 'timezone' in serializer.validated_data:
                meeting.timezone = serializer.validated_data['timezone']
        
        # Update other fields
        for field in ['meeting_name', 'meeting_link', 'is_completed']:
            if field in serializer.validated_data:
                setattr(meeting, field, serializer.validated_data[field])
        
        meeting.save()
        return Response(serializer.data)

    def _convert_to_utc(self, date, time, timezone_str):
        user_timezone = pytz_timezone(timezone_str)
        return user_timezone.localize(datetime.combine(date, time)).astimezone(pytz_timezone('UTC'))

    def _resolve_update_conflict(self, date, time, meeting_id):
        conflict = models.Meeting.objects.filter(
            date=date, 
            time=time
        ).exclude(pk=meeting_id).exists()
        
        if conflict:
            new_time = (datetime.combine(date, time) + timedelta(minutes=20)).time()
            return date, new_time
        return date, time
    
    # Previous code
    # from django.shortcuts import render
# from . import models
# from . import serializers
# from pytz import timezone as pytz_timezone
# from supabase import create_client, Client as SupabaseClient
# from storage3.exceptions import StorageApiError
# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.exceptions import PermissionDenied, ValidationError
# from django.shortcuts import get_object_or_404
# from datetime import datetime, timedelta
# # Create your views here.
# # MEETING 
# class MeetingListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = models.Meeting.objects.all()
#     serializer_class = serializers.MeetingSerializer

#     def perform_create(self, serializer):
#         # Ensure only Account Managers can schedule meetings
#         if self.request.user.role != 'account_manager':
#             raise PermissionDenied("Only account managers can schedule meetings.")

#         client_id = serializer.validated_data.get('client').id if serializer.validated_data.get('client') else None
#         assignee_type = self.request.data.get('assignee_type')  # Expected to be "team" or "marketing_manager"

#         # Check if client is provided
#         if not client_id:
#             raise ValidationError({"error": "Client is required."})

#         client = get_object_or_404(models.Clients, id=client_id)

#         # Filter based on the assignee type
#         if assignee_type == 'team':
#             if not client.team:
#                 raise ValidationError({"error": "No team is assigned to this client."})
#             team = client.team
#             serializer.save(scheduled_by=self.request.user, team=team)

#         elif assignee_type == 'marketing_manager':
#             if not client.team:
#                 raise ValidationError({"error": "No team is assigned to this client."})
#             marketing_manager = client.team.memberships.filter(user__role='marketing_manager').first()
#             if not marketing_manager:
#                 raise ValidationError({"error": "No marketing manager found for the client's assigned team."})
#             serializer.save(scheduled_by=self.request.user, marketing_manager=marketing_manager.user)

#         else:
#             raise ValidationError({"error": "Invalid assignee type. Must be 'team' or 'marketing_manager'."})

#         # Handle timezone conversion and UTC storage
#         date = serializer.validated_data.get('date')
#         time = serializer.validated_data.get('time')
#         user_timezone_str = serializer.validated_data.get('timezone')

#         user_timezone = pytz_timezone(user_timezone_str)
#         local_datetime = user_timezone.localize(datetime.combine(date, time))
#         utc_datetime = local_datetime.astimezone(pytz_timezone('UTC'))

#         # Extract the date and time in UTC
#         date_utc = utc_datetime.date()
#         time_utc = utc_datetime.time()

#         # Check for existing meetings at the same time
#         existing_meeting = models.Meeting.objects.filter(date=date_utc, time=time_utc).first()

#         if existing_meeting:
#             new_datetime = datetime.combine(date_utc, existing_meeting.time) + timedelta(minutes=20)
#             date_utc = new_datetime.date()
#             time_utc = new_datetime.time()

#         # Save the meeting, including the updated date and time in UTC
#         serializer.save(scheduled_by=self.request.user, date=date_utc, time=time_utc, timezone=user_timezone_str)

#     def create(self, request, *args, **kwargs):
#         if request.user.role != 'account_manager':
#             return Response({"error": "Only account managers can schedule meetings"}, status=status.HTTP_403_FORBIDDEN)

#         return super().create(request, *args, **kwargs)

# class MeetingRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated, IsAccountManager]
#     queryset = models.Meeting.objects.all()
#     serializer_class = serializers.SpecificMeetingSerializer  

#     def get_object(self):
#         meeting_id = self.kwargs.get("pk")
#         return get_object_or_404(models.Meeting, pk=meeting_id)

#     def convert_to_local_timezone(self, date, time, timezone_str):
#         """Helper method to convert UTC to the specified timezone."""
#         meeting_timezone = pytz_timezone(timezone_str)
#         meeting_datetime_utc = datetime.combine(date, time)
#         meeting_datetime_utc = pytz_timezone('UTC').localize(meeting_datetime_utc)
#         return meeting_datetime_utc.astimezone(meeting_timezone)

#     def get(self, request, *args, **kwargs):
#         meeting = self.get_object()
#         serializer = self.get_serializer(meeting)

#         # Convert the meeting time from UTC to the original timezone
#         meeting_datetime_local = self.convert_to_local_timezone(meeting.date, meeting.time, meeting.timezone)

#         # Modify serializer data to return the date and time in the original time zone
#         response_data = serializer.data
#         response_data['date'] = meeting_datetime_local.strftime('%Y-%m-%d')
#         response_data['time'] = meeting_datetime_local.strftime('%H:%M:%S')

#         # Customizing the 'details' field based on the data
#         response_data['details'] = [
#             meeting.team.name if meeting.team else "No team assigned with this client",
#             meeting.scheduled_by.role if meeting.scheduled_by else None,
#             meeting.marketing_manager.role if meeting.marketing_manager else None
#         ]
        
#         # Filter out any 'None' values from the 'details' list
#         response_data['details'] = [item for item in response_data['details'] if item is not None]

#         return Response(response_data)

#     def update(self, request, *args, **kwargs):
#         meeting = self.get_object()  # Fetch the existing meeting instance

#         # Allow partial updates by passing 'partial=True' to the serializer
#         serializer = self.get_serializer(meeting, data=request.data, partial=True)

#         if serializer.is_valid():
#             # Get the existing date and time or use the provided values from the request
#             new_date = serializer.validated_data.get('date', meeting.date)
#             new_time = serializer.validated_data.get('time', meeting.time)

#             # Handle potential time conflicts if any (this logic needs to be implemented based on your needs)
#             new_datetime, rescheduled_message = self.handle_time_conflicts(new_date, new_time, meeting.pk)

#             # Update only the fields that were provided in the request, leaving other fields unchanged
#             if 'date' in serializer.validated_data:
#                 meeting.date = new_datetime.date()
#             if 'time' in serializer.validated_data:
#                 meeting.time = new_datetime.time()

#             if 'meeting_name' in serializer.validated_data:
#                 meeting.meeting_name = serializer.validated_data['meeting_name']
#             if 'meeting_link' in serializer.validated_data:
#                 meeting.meeting_link = serializer.validated_data['meeting_link']
#             if 'timezone' in serializer.validated_data:
#                 meeting.timezone = serializer.validated_data['timezone']
#             if 'is_completed' in serializer.validated_data:
#                 meeting.is_completed = serializer.validated_data['is_completed']

#             # Save the updated meeting instance
#             meeting.save()

#             # Prepare the response data
#             response_data = {'meeting': serializer.data}
#             if rescheduled_message:
#                 response_data['message'] = rescheduled_message

#             return Response(response_data, status=status.HTTP_200_OK)

#         # If validation fails, return the errors
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def handle_time_conflicts(self, date, time, meeting_id):
#         """Helper method to handle time conflicts and reschedule if needed."""
#         existing_meeting = models.Meeting.objects.filter(date=date, time=time).exclude(pk=meeting_id).first()
        
#         if existing_meeting:
#             # Adjust the time to 20 minutes after the existing meeting
#             new_datetime = datetime.combine(existing_meeting.date, existing_meeting.time) + timedelta(minutes=20)
#             rescheduled_message = f"Meeting has been rescheduled to {new_datetime.strftime('%Y-%m-%d %H:%M')}."
#         else:
#             new_datetime = datetime.combine(date, time)
#             rescheduled_message = None

#         return new_datetime, rescheduled_message

#     def delete(self, request, *args, **kwargs):
#         meeting = self.get_object()
#         meeting.delete()
#         return Response({"message": "Meeting deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
