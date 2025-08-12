from django.urls import path, include

from . import views

urlpatterns = [
   
    # ========================= MEETING MANAGEMENT ROUTES =========================
    path('meetings', views.MeetingListCreateView.as_view(), name='meeting-list-create'),  # List or create meetings
    path('meetings/<int:pk>', views.MeetingRetrieveUpdateDeleteView.as_view(), name='meeting-rud'),  # Update, delete meeting

    # Client Monthly Reports

    
   
    # ALL HISTORIES 
    path('histories', views.AllHistoriesView.as_view(), name='all-histories'),
    
    # USER SIGNUP 
    
    # path('clients/set-password/<str:uid>/<str:token>', views.ClientSetPasswordView.as_view(), name='client-set-password'),

    path('account-manager/agency-slug/', views.AccountManagerAgencyView.as_view(), name='get-account-manager'),

]




