from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views


urlpatterns = [
    
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),        

    path('auth/token/verify', TokenVerifyView.as_view(), name='token_verify'),

    path('auth/login', views.LoginView.as_view(), name='login'), 

    path('auth/logout', views.LogoutView.as_view(), name='logout'),  

    path('auth/set-password/<uidb64>/<token>', views.SetPasswordView.as_view(), name='set-password'),  

    path('auth/password/forgot', views.ForgotPasswordView.as_view(), name='forgot-password'), 

    path('auth/password/reset-confirm/<uidb64>/<token>', views.ResetPasswordConfirmView.as_view(), name='password-reset-confirm'),  
    
]


