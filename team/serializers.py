from rest_framework import serializers
from client.models import Clients
from user.serializers import UserSerializer
from . import models
from client.models import Clients




class TeamSerializer(serializers.ModelSerializer):
    # Add fields for member and client counts
    members_count = serializers.SerializerMethodField()
    clients_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = ['id', 'name', 'created_by', 'members_count', 'clients_count']

    # Serializer method to get the number of members in the team
    def get_members_count(self, obj):
        return obj.memberships.count()

    # Serializer method to get the number of clients associated with the team
    def get_clients_count(self, obj):
        return Clients.objects.filter(team=obj).count()


class TeamMembershipSerializer(serializers.ModelSerializer):
    # Due to circular import
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = models.TeamMembership
        fields = ['id', 'team', 'user', 'user_id']

