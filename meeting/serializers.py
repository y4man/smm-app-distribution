
from rest_framework import serializers
from . import models

# Optimized Code
class BaseMeetingSerializer(serializers.ModelSerializer):
    # Base serializer with common fields and methods
    client_name = serializers.CharField(
        source='client.business_name', 
        read_only=True
    )
    scheduled_by_id = serializers.IntegerField(
        source='scheduled_by.id',
        read_only=True
    )
    details = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
        fields = [
            'id', 'date', 'time', 'meeting_name', 'meeting_link', 
            'timezone', 'client', 'client_name', 'is_completed',
            'scheduled_by_id', 'details'
        ]

    def get_details(self, obj):
        # Optimized details generation with single attribute check
        details = []
        if obj.team_id:  # Check ID instead of full relation
            details.append(obj.team.name)
        if obj.scheduled_by_id:
            details.append(obj.scheduled_by.role)
        if obj.marketing_manager_id:
            details.append(obj.marketing_manager.role)
        return details or ["No details available"]

class MeetingSerializer(BaseMeetingSerializer):
    # Serializer for list/create operations with team field
    client = serializers.PrimaryKeyRelatedField(
        queryset=models.Clients.objects.only('id', 'business_name', 'team'),
        help_text="ID of the client associated with the meeting"
    )
    team = serializers.StringRelatedField()

    class Meta(BaseMeetingSerializer.Meta):
        fields = BaseMeetingSerializer.Meta.fields + ['team']

class SpecificMeetingSerializer(BaseMeetingSerializer):
    # Detailed serializer for retrieve/update operations
    scheduled_by = serializers.StringRelatedField(
        source='scheduled_by.email',
        help_text="Email of the user who scheduled the meeting"
    )
    local_time = serializers.SerializerMethodField()
    local_date = serializers.SerializerMethodField()

    class Meta(BaseMeetingSerializer.Meta):
        fields = BaseMeetingSerializer.Meta.fields + [
            'scheduled_by', 'local_time', 'local_date'
        ]

    def get_local_time(self, obj):
        # Optimized time formatting
        return obj.time.strftime('%H:%M:%S')

    def get_local_date(self, obj):
        # Optimized date formatting
        return obj.date.strftime('%Y-%m-%d')
    
# Previous code
# # MEETINGS 
# class MeetingSerializer(serializers.ModelSerializer):
#     # Read-only fields for existing data
#     scheduled_by_id = serializers.IntegerField(source='scheduled_by.id', read_only=True)
#     client_name = serializers.CharField(source='client.business_name', read_only=True)  
#     client = serializers.PrimaryKeyRelatedField(queryset=models.Clients.objects.all())

#     # Custom field to return an array with required data
#     details = serializers.SerializerMethodField()

#     class Meta:
#         model = models.Meeting
#         fields = [
#             'id', 'date', 'time', 'meeting_name', 'meeting_link', 'timezone', 'client', 'client_name', 'team', 
#             'is_completed', 'scheduled_by_id', 'details'
#         ]

#     def get_details(self, obj):
#         return [
#             obj.team.name if obj.team else None,
#             obj.scheduled_by.role if obj.scheduled_by else None,
#             obj.marketing_manager.role if obj.marketing_manager else None
#         ]

# class SpecificMeetingSerializer(serializers.ModelSerializer):
#     # Read-only fields for existing data
#     client_name = serializers.CharField(source='client.business_name', read_only=True)
    
#     # Custom field to return an array with required data
#     details = serializers.SerializerMethodField()

#     class Meta:
#         model = models.Meeting
#         fields = [
#             'id', 'date', 'time', 'meeting_name', 'meeting_link', 'timezone', 'client', 'client_name',
#             'is_completed', 'scheduled_by_id', 'details'
#         ]

#     def get_details(self, obj):
#         details_list = [
#             obj.scheduled_by.role if obj.scheduled_by else None,
#             obj.team.name if obj.team else "No team assigned with this client",
#             obj.marketing_manager.role if obj.marketing_manager else None
#         ]
#         # Remove any None values from the list
#         return [detail for detail in details_list if detail is not None]