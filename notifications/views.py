from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


# Create your views here.
class MarkNotificationAsReadView(APIView):
    def post(self, request, *args, **kwargs):
        notification_id = kwargs.get('id')
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({"success": True, "message": "Notification marked as read."})
    
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Fetch notifications for the logged-in user
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        # Serialize the notifications
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Mark all notifications as read for the logged-in user.
        """
        # Update all unread notifications for the user to is_read=True
        updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response(
            {"message": f"{updated_count} notifications marked as read."},
            status=status.HTTP_200_OK
        )
       