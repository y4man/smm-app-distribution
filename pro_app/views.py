from .imports import (  
    APIView, Response, Request, status, generics, AllowAny, settings, TokenObtainPairView, RefreshToken, TokenRefreshView,
    send_mail, get_connection, default_token_generator, datetime, timedelta, JsonResponse,
    urlsafe_base64_decode, urlsafe_base64_encode, force_bytes, reverse, get_object_or_404, 
    smtplib, MIMEText, MIMEMultipart, authenticate, IsAuthenticated, get_user_model, RefreshToken, MultiPartParser, FormParser
    ,create_task, update_client_workflow, mark_task_as_completed, get_next_step_and_user, update_client_status, make_aware,Q
,PermissionDenied, MIMEText, MIMEMultipart, MIMEBase, encoders, tempfile, os,ValidationError, now, urlencode, HttpResponse, random, string,
# custom permissions 
IsMarketingDirector, IsMarketingManager, IsAccountManager, IsAccountant, IsMarketingTeam, IsMarketingDirectorOrAccountManager, create_task, check_proposal_status, send_task_notification, NoReverseMatch
)
from . import models
from . import serializers
from pytz import timezone as pytz_timezone

from supabase import create_client, Client as SupabaseClient
from storage3.exceptions import StorageApiError
from pro_app.storage import save_file_to_supabase
from calender.models import ClientCalendar, ClientCalendarDate
from task.serializers import CustomTaskSerializer

# set up once at top
_supabase: SupabaseClient = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY,
)
storage = _supabase.storage.from_(settings.SUPABASE_BUCKET)

# AUTH 
class CustomTokenObtainPairView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(username=username, password=password) 

        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Set token expiration
            access_token.set_exp(
                lifetime=timedelta(minutes=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].seconds // 60))

            # Create the response
            response = Response({
                'message': 'Login successful',
            }, status=status.HTTP_200_OK)

            # Set the access token in the cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],  # Cookie name from settings
                value=str(access_token),  # Token value
                expires=access_token.payload['exp'],  # Expiration time
                httponly=True,  # Prevent client-side JavaScript access
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],  # Should be True in production with HTTPS
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],  # To prevent CSRF attacks
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']  # Path scope for the cookie
            )

            return response
        else:
            return Response({"detail": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token not found."}, status=401)

        request.data['refresh'] = refresh_token
        return super().post(request, *args, **kwargs)

#CALENDER

# class ClientCalendarDateRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = serializers.ClientCalendarDateSerializer
#     parser_classes = (MultiPartParser, FormParser)

#     def get_queryset(self):
#         calendar_id = self.kwargs.get('calendar_id')
#         return models.ClientCalendarDate.objects.filter(calendar_id=calendar_id)

#     def put(self, request, *args, **kwargs):
#         calendar_date = self.get_object()
#         user_role = request.user.role

#         # Role-based field restrictions
#         if user_role in ['marketing_manager','marketing_assistant','content_writer','graphics_designer','marketing_director']:
#             for fld in ['client_approval','comments']:
#                 if fld in request.data:
#                     return Response({"error": f"{user_role} is not allowed to update {fld}."}, status=status.HTTP_403_FORBIDDEN)

#         # Filter allowed data
#         allowed = self.get_allowed_fields_by_role(user_role)
#         filtered_data = {k: v for k,v in request.data.items() if k in allowed}

#         if user_role == 'graphics_designer':
#             # single-index update
#             if 'creative_index' in request.data and 'creatives' in request.FILES:
#                 try:
#                     index = int(request.data['creative_index'])
#                 except ValueError:
#                     return Response({"error": "Invalid index format."}, status=status.HTTP_400_BAD_REQUEST)

#                 new_file = request.FILES['creatives']
#                 if not isinstance(calendar_date.creatives, list) or not (0 <= index < len(calendar_date.creatives)):
#                     return Response({"error": "Invalid creative index."}, status=status.HTTP_400_BAD_REQUEST)

#                 # delete old
#                 old_url = calendar_date.creatives[index]
#                 parsed = urlparse(old_url)
#                 key = unquote(parsed.path.lstrip('/'))
#                 try:
#                     storage.remove([key])
#                 except Exception:
#                     pass

#                 # upload new
#                 tmp_path = None
#                 try:
#                     with tempfile.NamedTemporaryFile(delete=False) as tmp:
#                         for chunk in new_file.chunks(): tmp.write(chunk)
#                         tmp_path = tmp.name
#                     path_in_bucket = f"creatives/{new_file.name}"
#                     try:
#                         storage.upload(file=tmp_path, path=path_in_bucket, file_options={"content-type": new_file.content_type})
#                     except StorageApiError as exc:
#                         raw = exc.args[0] if exc.args else {}
#                         if isinstance(raw, dict) and raw.get('statusCode') == 409:
#                             storage.update(file=tmp_path, path=path_in_bucket, file_options={"content-type": new_file.content_type})
#                         else:
#                             msg = raw.get('message', str(exc)) if isinstance(raw, dict) else str(exc)
#                             return Response({"creatives": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                 finally:
#                     if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)

#                 # set new URL
#                 new_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{path_in_bucket}"
#                 calendar_date.creatives[index] = new_url
#                 calendar_date.save()
#                 serializer = self.get_serializer(calendar_date, context={'request': request})
#                 return Response(serializer.data, status=status.HTTP_200_OK)

#             # full-list replacement
#             if request.FILES.getlist('creatives'):
#                 # delete old
#                 for old_url in calendar_date.creatives or []:
#                     parsed = urlparse(old_url)
#                     key = unquote(parsed.path.lstrip('/'))
#                     try:
#                         storage.remove([key])
#                     except Exception:
#                         pass

#                 new_urls = []
#                 for f in request.FILES.getlist('creatives'):
#                     tmp_path = None
#                     try:
#                         with tempfile.NamedTemporaryFile(delete=False) as tmp:
#                             for chunk in f.chunks(): tmp.write(chunk)
#                             tmp_path = tmp.name
#                         bucket_path = f"creatives/{f.name}"
#                         try:
#                             storage.upload(file=tmp_path, path=bucket_path, file_options={"content-type": f.content_type})
#                         except StorageApiError as exc:
#                             raw = exc.args[0] if exc.args else {}
#                             if isinstance(raw, dict) and raw.get('statusCode') == 409:
#                                 storage.update(file=tmp_path, path=bucket_path, file_options={"content-type": f.content_type})
#                             else:
#                                 msg = raw.get('message', str(exc)) if isinstance(raw, dict) else str(exc)
#                                 return Response({"creatives": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                     finally:
#                         if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)

#                     new_urls.append(f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{bucket_path}")

#                 filtered_data['creatives'] = new_urls

#         if not filtered_data and not request.FILES:
#             return Response({"error": f"{user_role} is not allowed to update the provided fields."}, status=status.HTTP_403_FORBIDDEN)

#         serializer = serializers.ClientCalendarDateSerializer(calendar_date, data=filtered_data, partial=True, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
#     def delete(self, request, *args, **kwargs):
#         """Restricts deletion to only marketing managers."""
#         if request.user.role != 'marketing_manager':
#             return Response(
#                 {"error": "Only marketing managers can delete calendar dates."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#         return super().delete(request, *args, **kwargs)

#     def patch(self, request, *args, **kwargs):
#         # This method allows partial updates with the PATCH HTTP method
#         return self.put(request, *args, **kwargs)

#     def get_allowed_fields_by_role(self, role):
#         """Returns a list of fields the user is allowed to update based on their role."""
#         if role in ['account_manager', 'user']:
#             return ['client_approval', 'comments']

#         elif role == 'marketing_manager':
#             return [
#                 'post_count', 'type', 'category', 'cta', 'strategy', 'resource',
#                 'internal_status', 'collaboration'
#             ]

#         elif role == 'content_writer':
#             return ['tagline', 'caption', 'hashtags', 'e_hooks', 'creatives_text']  # Added 'creatives_text' here

#         elif role == 'graphics_designer':
#             return ['creatives']

#         else:
#             return []



#CLIENT INVOICE
# class ClientInvoicesListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = serializers.ClientInvoicesSerializer
#     parser_classes = [MultiPartParser, FormParser]

#     def get_queryset(self):
#         client_id = self.kwargs.get('client_id')
#         return models.ClientInvoices.objects.filter(client_id=client_id)

#     def post(self, request, *args, **kwargs):
#         client_id = self.kwargs.get('client_id')
#         client    = get_object_or_404(models.Clients, id=client_id)

#         invoice_file = request.FILES.get('invoice')
#         if not invoice_file:
#             return Response({"invoice": ["No file uploaded."]},
#                             status=status.HTTP_400_BAD_REQUEST)

#         # ◆ Save to Wasabi; s3_saved_path is e.g. "invoices/foo.pdf"
#         s3_saved_path = default_storage.save(
#             f"invoices/{invoice_file.name}", invoice_file
#         )

#         # ◆ Create instance with ONLY the path
#         invoice = models.ClientInvoices.objects.create(
#             client            = client,
#             invoice           = s3_saved_path,
#             submission_status = 'wait_for_approval',
#             billing_from      = request.data.get('billing_from'),
#             billing_to        = request.data.get('billing_to'),
#             payment_url       = request.data.get('payment_url'),
#         )

#         # ◆ (Optional) send your email…
#         self._send_invoice_email(request, client, invoice,
#                                  invoice.payment_url)

#         serializer = self.get_serializer(invoice, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

# UTILITY FUNCTION FOR OBJECT STORAGE REPLACED FILES
# def save_file_to_supabase(
#     uploaded_file,
#     folder: str,
#     target_key: str | None = None
# ) -> str:
#     """
#     Deletes target_key if given, then uploads uploaded_file to
#     folder/<uploaded_file.name>, or overwrites target_key in-place.
#     Returns the bucket-path string.
#     """
#     # decide path
#     path_in_bucket = target_key or f"{folder}/{uploaded_file.name}"
#     tmp_path = None

#     try:
#         # dump to a temp file
#         with tempfile.NamedTemporaryFile(delete=False) as tmp:
#             for chunk in uploaded_file.chunks():
#                 tmp.write(chunk)
#             tmp_path = tmp.name

#         # if overwriting an existing key, use update(); else upload()
#         if target_key:
#             try:
#                 storage.update(
#                     file=tmp_path,
#                     path=path_in_bucket,
#                     file_options={"content-type": uploaded_file.content_type},
#                 )
#             except StorageApiError as exc:
#                 raw = exc.args[0] if exc.args else {}
#                 # if key didn’t exist, fall back to upload
#                 if isinstance(raw, dict) and raw.get("statusCode") == 404:
#                     storage.upload(
#                         file=tmp_path,
#                         path=path_in_bucket,
#                         file_options={"content-type": uploaded_file.content_type},
#                     )
#                 else:
#                     raise
#         else:
#             storage.upload(
#                 file=tmp_path,
#                 path=path_in_bucket,
#                 file_options={"content-type": uploaded_file.content_type},
#             )

#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.unlink(tmp_path)

#     return path_in_bucket

# MEETING 
class MeetingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = models.Meeting.objects.all()
    serializer_class = serializers.MeetingSerializer

    def perform_create(self, serializer):
        # Ensure only Account Managers can schedule meetings
        if self.request.user.role != 'account_manager':
            raise PermissionDenied("Only account managers can schedule meetings.")

        client_id = serializer.validated_data.get('client').id if serializer.validated_data.get('client') else None
        assignee_type = self.request.data.get('assignee_type')  # Expected to be "team" or "marketing_manager"

        # Check if client is provided
        if not client_id:
            raise ValidationError({"error": "Client is required."})

        client = get_object_or_404(models.Clients, id=client_id)

        # Filter based on the assignee type
        if assignee_type == 'team':
            if not client.team:
                raise ValidationError({"error": "No team is assigned to this client."})
            team = client.team
            serializer.save(scheduled_by=self.request.user, team=team)

        elif assignee_type == 'marketing_manager':
            if not client.team:
                raise ValidationError({"error": "No team is assigned to this client."})
            marketing_manager = client.team.memberships.filter(user__role='marketing_manager').first()
            if not marketing_manager:
                raise ValidationError({"error": "No marketing manager found for the client's assigned team."})
            serializer.save(scheduled_by=self.request.user, marketing_manager=marketing_manager.user)

        else:
            raise ValidationError({"error": "Invalid assignee type. Must be 'team' or 'marketing_manager'."})

        # Handle timezone conversion and UTC storage
        date = serializer.validated_data.get('date')
        time = serializer.validated_data.get('time')
        user_timezone_str = serializer.validated_data.get('timezone')

        user_timezone = pytz_timezone(user_timezone_str)
        local_datetime = user_timezone.localize(datetime.combine(date, time))
        utc_datetime = local_datetime.astimezone(pytz_timezone('UTC'))

        # Extract the date and time in UTC
        date_utc = utc_datetime.date()
        time_utc = utc_datetime.time()

        # Check for existing meetings at the same time
        existing_meeting = models.Meeting.objects.filter(date=date_utc, time=time_utc).first()

        if existing_meeting:
            new_datetime = datetime.combine(date_utc, existing_meeting.time) + timedelta(minutes=20)
            date_utc = new_datetime.date()
            time_utc = new_datetime.time()

        # Save the meeting, including the updated date and time in UTC
        serializer.save(scheduled_by=self.request.user, date=date_utc, time=time_utc, timezone=user_timezone_str)

    def create(self, request, *args, **kwargs):
        if request.user.role != 'account_manager':
            return Response({"error": "Only account managers can schedule meetings"}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

class MeetingRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAccountManager]
    queryset = models.Meeting.objects.all()
    serializer_class = serializers.SpecificMeetingSerializer  

    def get_object(self):
        meeting_id = self.kwargs.get("pk")
        return get_object_or_404(models.Meeting, pk=meeting_id)

    def convert_to_local_timezone(self, date, time, timezone_str):
        """Helper method to convert UTC to the specified timezone."""
        meeting_timezone = pytz_timezone(timezone_str)
        meeting_datetime_utc = datetime.combine(date, time)
        meeting_datetime_utc = pytz_timezone('UTC').localize(meeting_datetime_utc)
        return meeting_datetime_utc.astimezone(meeting_timezone)

    def get(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(meeting)

        # Convert the meeting time from UTC to the original timezone
        meeting_datetime_local = self.convert_to_local_timezone(meeting.date, meeting.time, meeting.timezone)

        # Modify serializer data to return the date and time in the original time zone
        response_data = serializer.data
        response_data['date'] = meeting_datetime_local.strftime('%Y-%m-%d')
        response_data['time'] = meeting_datetime_local.strftime('%H:%M:%S')

        # Customizing the 'details' field based on the data
        response_data['details'] = [
            meeting.team.name if meeting.team else "No team assigned with this client",
            meeting.scheduled_by.role if meeting.scheduled_by else None,
            meeting.marketing_manager.role if meeting.marketing_manager else None
        ]
        
        # Filter out any 'None' values from the 'details' list
        response_data['details'] = [item for item in response_data['details'] if item is not None]

        return Response(response_data)

    def update(self, request, *args, **kwargs):
        meeting = self.get_object()  # Fetch the existing meeting instance

        # Allow partial updates by passing 'partial=True' to the serializer
        serializer = self.get_serializer(meeting, data=request.data, partial=True)

        if serializer.is_valid():
            # Get the existing date and time or use the provided values from the request
            new_date = serializer.validated_data.get('date', meeting.date)
            new_time = serializer.validated_data.get('time', meeting.time)

            # Handle potential time conflicts if any (this logic needs to be implemented based on your needs)
            new_datetime, rescheduled_message = self.handle_time_conflicts(new_date, new_time, meeting.pk)

            # Update only the fields that were provided in the request, leaving other fields unchanged
            if 'date' in serializer.validated_data:
                meeting.date = new_datetime.date()
            if 'time' in serializer.validated_data:
                meeting.time = new_datetime.time()

            if 'meeting_name' in serializer.validated_data:
                meeting.meeting_name = serializer.validated_data['meeting_name']
            if 'meeting_link' in serializer.validated_data:
                meeting.meeting_link = serializer.validated_data['meeting_link']
            if 'timezone' in serializer.validated_data:
                meeting.timezone = serializer.validated_data['timezone']
            if 'is_completed' in serializer.validated_data:
                meeting.is_completed = serializer.validated_data['is_completed']

            # Save the updated meeting instance
            meeting.save()

            # Prepare the response data
            response_data = {'meeting': serializer.data}
            if rescheduled_message:
                response_data['message'] = rescheduled_message

            return Response(response_data, status=status.HTTP_200_OK)

        # If validation fails, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_time_conflicts(self, date, time, meeting_id):
        """Helper method to handle time conflicts and reschedule if needed."""
        existing_meeting = models.Meeting.objects.filter(date=date, time=time).exclude(pk=meeting_id).first()
        
        if existing_meeting:
            # Adjust the time to 20 minutes after the existing meeting
            new_datetime = datetime.combine(existing_meeting.date, existing_meeting.time) + timedelta(minutes=20)
            rescheduled_message = f"Meeting has been rescheduled to {new_datetime.strftime('%Y-%m-%d %H:%M')}."
        else:
            new_datetime = datetime.combine(date, time)
            rescheduled_message = None

        return new_datetime, rescheduled_message

    def delete(self, request, *args, **kwargs):
        meeting = self.get_object()
        meeting.delete()
        return Response({"message": "Meeting deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

# TASK 



#PLANS



# MERGE CLIENT PLAN VIEWS INTO ONE this view is use for assign plan to client retrieve and updated plan


# class ThreadMessageListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = serializers.ClientMessageThreadSerializer
#     def get_queryset(self):
#         """
#         Retrieves messages for the given client ID from the URL.
#         Ensures the user is authorized to view the thread.
#         """
#         client_id = self.kwargs['client_id']  # Get client_id from the URL
#         client = get_object_or_404(models.Clients, id=client_id)
#         m_d = get_object_or_404(models.CustomUser, role='marketing_director')
#         # Ensure the client has a team
#         if not client.team:
#             raise PermissionDenied("This client is not assigned to any team.")
#         # Check if the user has access to the client's messages
#         if not (
#             client.team.memberships.filter(user=self.request.user).exists() or
#             client.account_manager == self.request.user or m_d == self.request.user
#         ):
#             raise PermissionDenied("You do not have permission to view messages in this thread.")
#         return models.ClientMessageThread.objects.filter(client=client)
    
#     def perform_create(self, serializer):
#         """
#         Handles message creation for a specific client ID obtained from the URL.
#         Ensures the user is authorized to send messages in the thread.
#         Sends a notification to the appropriate recipient(s).
#         """
#         client_id = self.kwargs['client_id']  # Extract client_id from the URL
#         client = get_object_or_404(models.Clients, id=client_id)
#         m_d = get_object_or_404(models.CustomUser, role='marketing_director')
#         # Ensure the client has a team
#         if not client.team:
#             raise PermissionDenied("This client is not assigned to any team.")
#         # Check if the user has permission to send messages
#         if not (
#             client.team.memberships.filter(user=self.request.user).exists() or
#             client.account_manager == self.request.user or m_d == self.request.user
#         ):
#             raise PermissionDenied("You do not have permission to send messages in this thread.")
#         # Save the message with the associated client and sender
#         message = serializer.save(client=client, sender=self.request.user)
#         # Determine recipients of the thread notification
#         team_members = client.team.memberships.exclude(user=self.request.user).values_list('user', flat=True)
#         account_manager = client.account_manager
#         # Prepare a list of unique recipients
#         recipients = set(list(team_members) + ([account_manager.id] if account_manager and account_manager != self.request.user else []))
#         # Send thread notification to each recipient
#         for recipient_id in recipients:
#             recipient = get_object_or_404(models.CustomUser, id=recipient_id)
#             send_task_notification(
#                 recipient=recipient,
#                 sender=self.request.user,
#                 message=f"New message in the thread for client '{client.business_name}'.",
#                 notification_type="thread_notify"
#             )





# List and Create Strategy

       


class AllHistoriesView(APIView):
    """
    Fetches all history logs along with user full names.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]  #Apply authentication check

    def get(self, request):
        try:
            # Fetch all history records ordered by latest first
            history_records = models.History.objects.select_related('user').order_by('-created_at')

            # Serialize history data
            history_data = []
            for record in history_records:
                history_data.append({
                    "id": record.id,
                    "user_id": record.user.id,
                    "user_full_name": f"{record.user.first_name} {record.user.last_name}",
                    "action": record.action,
                    "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")  # Format timestamp
                })

            # Return response with all history logs
            return Response(history_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       


class AccountManagerAgencyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        acc_mngr_id = request.query_params.get('acc_mngr_id')
        try:
            agency = models.CustomUser.objects.get(id=acc_mngr_id, role='account_manager')
            return Response({
                "account_manager_id": agency.id,
                "first_name": agency.first_name,
                "last_name": agency.last_name,
                "email": agency.email,
                "role": agency.role
            }, status=status.HTTP_200_OK)
        except models.CustomUser.DoesNotExist:
            return Response({"message": "No valid agency found for the provided agency slug."}, status=status.HTTP_400_BAD_REQUEST)
