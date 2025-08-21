from django.urls import path
from . import views

urlpatterns = [
    
    # ✅ List all messages in the thread for a specific client
    path('client/<int:client_id>', views.ThreadMessageListCreateView.as_view(), name='thread-message-list-create'),

    # ✅ List and create notes (all authenticated user see the notes of everyone)
    path('', views.ListCreateNoteView.as_view(), name='list_create_note'), 

    # ✅ Detailed view of a single note
    path('<int:pk>', views.RetrieveUpdateDeleteNoteView.as_view(), name='retrieve_update_delete_note'), 

]