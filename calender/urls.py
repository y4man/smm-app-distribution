from django.urls import path
from . import views

urlpatterns = [
    
    # ✅ Retrieves all calendars for a specific client
    path('clients/<int:id>/calendars', views.ClientCalendarListCreateView.as_view(), name='calendar-list-create'),

    # ✅ Returns full details of a specific calendar
    path('clients/<int:client_id>/calendars/<int:pk>', views.ClientCalendarRetrieveUpdateDeleteView.as_view(), name='calendar-rud'),

    # ✅ Returns all dates for a specific calendar
    path('<int:calendar_id>/dates', views.ClientCalendarDateListCreateView.as_view(), name='calendar-date-list-create'),

    # ✅ View a single date entry's details
    path('<int:calendar_id>/dates/<int:pk>', views.ClientCalendarDateRetrieveUpdateDeleteView.as_view(), name='calendar-date-rud'),

    # ✅ Dates for a specific client, month, and validated account manager
    path('client-calendar/<str:client_business_name>/<str:account_manager_username>/<str:month_name>/', views.ClientCalendarByMonthView.as_view(), name='client-calendar-by-month' ),

]