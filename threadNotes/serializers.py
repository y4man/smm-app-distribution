from rest_framework import serializers
from .models import ClientMessageThread, Notes


class ClientMessageThreadSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    sender_info = serializers.SerializerMethodField()
    class Meta:
        model = ClientMessageThread
        fields = ['id', 'client', 'sender', 'message', 'created_at', 'sender_info', 'role_display']
        read_only_fields = ['client', 'sender']  # Set client and sender as read-only
    def get_sender_info(self, obj):
        """
        Returns detailed sender information, including full URL for the profile picture.
        """
        request = self.context.get("request")  # Get request context for absolute URI
        sender = obj.sender
        
        if sender:
            profile_url = sender.profile.url if sender.profile else None
            full_profile_url = request.build_absolute_uri(profile_url) if request and profile_url else None

            return {
                "id": sender.id,
                "first_name": sender.first_name,
                "last_name": sender.last_name,
                "role": sender.get_role_display(),
                "profile": full_profile_url  # ✅ Return complete URL for profile image
            }
        return None 

class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = ['id', 'note_title', 'message', 'note_flag', 'sender', 'created_at', 'updated_at']
        read_only_fields = ['sender', 'created_at', 'updated_at']

