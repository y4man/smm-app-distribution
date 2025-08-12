from django.urls import path
from team import views

# Testing Required

urlpatterns = [

    # Rechecking Required....

    path('', views.TeamListCreateView.as_view(), name='create-list-teams'),
    # Retrieve, update, or delete a team
    path('get/<int:pk>', views.TeamRetrieveUpdateDeleteView.as_view(), name='team-rud'),  

]