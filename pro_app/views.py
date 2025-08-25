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
from pytz import timezone as pytz_timezone
from supabase import create_client, Client as SupabaseClient
from pro_app.storage import save_file_to_supabase
from account.models import CustomUser


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
            agency = CustomUser.objects.get(id=acc_mngr_id, role='account_manager')
            return Response({
                "account_manager_id": agency.id,
                "first_name": agency.first_name,
                "last_name": agency.last_name,
                "email": agency.email,
                "role": agency.role
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"message": "No valid agency found for the provided agency slug."}, status=status.HTTP_400_BAD_REQUEST)
