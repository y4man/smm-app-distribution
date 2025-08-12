from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_full_name = serializers.CharField(source="recipient.get_full_name", read_only=True)
    recipient_role = serializers.CharField(source="recipient.role", read_only=True)
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True, default=None)
    sender_id = serializers.IntegerField(source="sender.id", read_only=True, default=None)

    class Meta:
        model = Notification
        fields = [
            'id', 'client_id', 'client_name', 'task_type', 'recipient', 'recipient_full_name', 'recipient_role',
            'sender_id', 'sender_name', 'message', 'notification_type', 'is_read', 'created_at',
        ]

