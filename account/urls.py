from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views


urlpatterns = [
    
    # "auth/" included in the beginning of each url

    # ✅ Refresh JWT token 
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),        

    # ✅ Verify JWT token
    path('token/verify', TokenVerifyView.as_view(), name='token_verify'),

    # ✅ User login (TESTED)
    path('login', views.LoginView.as_view(), name='login'), 

    # ✅ User logout (TESTED)
    path('logout', views.LogoutView.as_view(), name='logout'),  

    # ✅ Set password with token
    path('set-password/<uidb64>/<token>', views.SetPasswordView.as_view(), name='set-password'),  

    # ✅ Forgot password (TESTED)
    path('password/forgot', views.ForgotPasswordView.as_view(), name='forgot-password'), 

    # ✅ Reset password with token
    path('password/reset-confirm/<uidb64>/<token>', views.ResetPasswordConfirmView.as_view(), name='password-reset-confirm'),  
    
]


