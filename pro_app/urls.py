from django.urls import path, include

from . import views

urlpatterns = [
   
    # ALL HISTORIES 
    path('histories', views.AllHistoriesView.as_view(), name='all-histories'),
    
    # USER SIGNUP 
    path('account-manager/agency-slug/', views.AccountManagerAgencyView.as_view(), name='get-account-manager'),

]




