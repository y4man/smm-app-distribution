from rest_framework import serializers
from django.conf import settings
from .models import CustomTask, Task

class CustomTaskSerializer(serializers.ModelSerializer):
    task_file = serializers.SerializerMethodField()
    assign_to_full_name = serializers.SerializerMethodField()
    assign_to_role = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()  # ✅ Added client name field

    class Meta:
        model = CustomTask
        fields = [
            "id", "task_name", "task_description",
            "assign_to_full_name", "assign_to_role",
            "client_name",  # ✅ Added client name field
            "task_status", "task_file", "task_created_at", "task_updated_at"
        ]
        extra_kwargs = {
            "task_status": {"required": False, "default": False},
            "task_created_at": {"read_only": True},
            "task_updated_at": {"read_only": True},
        }

    def get_task_file(self, obj):
        if not obj.custom_task_file:
            return None
        # obj.custom_task_file is the key (e.g. 'task_files/foo.pdf')
        return (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/"
            f"{settings.SUPABASE_BUCKET}/"
            f"{obj.custom_task_file}"
        )

    def get_assign_to_full_name(self, obj):
        """Return full name of the assigned user."""
        return obj.assign_to_id.get_full_name() if obj.assign_to_id else None

    def get_assign_to_role(self, obj):
        """Return role of the assigned user."""
        return obj.assign_to_id.role if obj.assign_to_id else None

    def get_client_name(self, obj):
        """Return the name of the client associated with the task."""
        return obj.client_id.business_name if obj.client_id else None


class MyTaskSerializer(serializers.ModelSerializer):
    client_business_name = serializers.CharField(source='client.business_name', read_only=True)

    class Meta:
        model = Task
        # model = models.Clients
        fields = ['id', 'client','created_at', 'task_type', 'client_business_name'] 


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()  # Use SerializerMethodField for custom logic
    client_name = serializers.CharField(source='client.business_name', read_only=True)
    class Meta:
        model = Task
        fields = ['id', 'task_type', 'client', 'client_name', 'assigned_to', 'assigned_to_name', 'is_completed', 'created_at']
        read_only_fields = ['created_at']
    def get_assigned_to_name(self, obj):
        """
        Concatenate first and last name of the assigned user.
        """
        if obj.assigned_to:
            first_name = obj.assigned_to.first_name or ''
            last_name = obj.assigned_to.last_name or ''
            return f"{first_name} {last_name}".strip()
        return None  # Return None if assigned_to is not set