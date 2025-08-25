from django.urls import path
from . import views

urlpatterns = [
 # ========================= MEETING MANAGEMENT ROUTES =========================
    path('', views.MeetingListCreateView.as_view(), name='meeting-list-create'),  # List or create meetings
    path('<int:pk>', views.MeetingRetrieveUpdateDeleteView.as_view(), name='meeting-rud'),  # Update, delete meeting
]