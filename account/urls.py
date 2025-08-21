from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views


urlpatterns = [
    
   
    # ✅ Refresh JWT token 
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),        

    # ✅ Verify JWT token
    path('auth/token/verify', TokenVerifyView.as_view(), name='token_verify'),

    # ✅ User login (TESTED)
    path('auth/login', views.LoginView.as_view(), name='login'), 

    # ✅ User logout (TESTED)
    path('auth/logout', views.LogoutView.as_view(), name='logout'),  

    # ✅ Set password with token
    path('auth/set-password/<uidb64>/<token>', views.SetPasswordView.as_view(), name='set-password'),  

    # ✅ Forgot password (TESTED)
    path('auth/password/forgot', views.ForgotPasswordView.as_view(), name='forgot-password'), 

    # ✅ Reset password with token
    path('auth/password/reset-confirm/<uidb64>/<token>', views.ResetPasswordConfirmView.as_view(), name='password-reset-confirm'),  
    
]


