from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied

from pro_app.utils import send_task_notification
from .serializers import ClientMessageThreadSerializer, ClientMessageThread
from django.shortcuts import get_object_or_404
from client.models import Clients
from account.models import CustomUser
from .models import Notes
from .serializers import NotesSerializer

# Create your views here.
class ThreadMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClientMessageThreadSerializer
    
    def _check_permissions(self, client):
        """Helper method to check if the user can access the thread."""
        is_team_member = client.team.memberships.filter(user=self.request.user).exists()
        is_account_manager = client.account_manager == self.request.user
        is_marketing_director = self.request.user.role == 'marketing_director'  # ✅ Direct role check

        if not (is_team_member or is_account_manager or is_marketing_director):
            raise PermissionDenied("You do not have permission to access this thread.")

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        client = get_object_or_404(Clients, id=client_id)
        
        if not client.team:
            raise PermissionDenied("This client is not assigned to any team.")
        
        self._check_permissions(client)  # Reuse permission logic
        return ClientMessageThread.objects.filter(client=client)

    def perform_create(self, serializer):
        client_id = self.kwargs['client_id']
        client = get_object_or_404(Clients, id=client_id)
        
        if not client.team:
            raise PermissionDenied("This client is not assigned to any team.")
        
        self._check_permissions(client)  # Same permission check
        message = serializer.save(client=client, sender=self.request.user)
        
        # Notify relevant users (team members + account manager, excluding sender)
        team_members = client.team.memberships.exclude(user=self.request.user).values_list('user', flat=True)
        account_manager = client.account_manager
        recipients = set(list(team_members) + ([account_manager.id] if account_manager and account_manager != self.request.user else []))
        
        for recipient_id in recipients:
            recipient = get_object_or_404(CustomUser, id=recipient_id)
            send_task_notification(
                recipient=recipient,
                sender=self.request.user,
                message=f"New message in the thread for client '{client.business_name}'.",
                notification_type="thread_notify"
            )


class ListCreateNoteView(generics.ListCreateAPIView):
    queryset = Notes.objects.all()
    serializer_class = NotesSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
               
class RetrieveUpdateDeleteNoteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notes.objects.all()
    serializer_class = NotesSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        pk = self.kwargs.get("pk")
        if not pk:
            raise AssertionError("Expected `pk` in the URL.")
        return super().get_object()
  