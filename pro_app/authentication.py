from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import CustomUser

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the access token from the cookies
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None  # No authentication information was provided

        try:
            # Decode the access token
            token = AccessToken(access_token)
            user_id = token['user_id']

            # Retrieve the user associated with the token
            user = CustomUser.objects.get(id=user_id)

            if not user.is_active:
                raise AuthenticationFailed('User is inactive')

            # If successful, return a tuple of (user, token)
            return (user, None)
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')

