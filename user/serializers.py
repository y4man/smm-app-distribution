from rest_framework import serializers
from smm_prod_project import settings
from account.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    teams = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    profile_file = serializers.ImageField(
        write_only=True,
        required=False,
        allow_null=True
    )
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "role",
            "agency_name", "agency_slug", "acc_mngr_id", "role_display", 
            "is_active", "date_joined", "teams", "profile", "profile_file", "password",
        ]
        # Note: profile_file is now included in fields list
        # Removed the duplicate "profile" entry

    def get_teams(self, user):
        from team.serializers import TeamSerializer
        return TeamSerializer(
            [m.team for m in user.team_memberships.all()],
            many=True
        ).data

    def get_profile(self, instance):
        if not instance.profile:
            return None
            
        return (
            f"{settings.SUPABASE_URL}"
            f"/storage/v1/object/public/"
            f"{settings.SUPABASE_BUCKET}/"
            f"{instance.profile.name}"
        )

    def validate(self, data):
        if data.get("role") == "account_manager":
            missing = {}
            for fld in ("agency_name", "agency_slug"):
                if not data.get(fld):
                    missing[fld] = "This field is required for account managers."
            if missing:
                raise serializers.ValidationError(missing)
        return data

    def update(self, instance, validated_data):
        # Handle password update
        if "password" in validated_data:
            instance.set_password(validated_data.pop("password"))
            
        # Other fields will be handled by the view's perform_update
        for attr, val in validated_data.items():
            if attr != 'profile_file':  # profile_file is handled in the view
                setattr(instance, attr, val)

        instance.save()
        return instance
 
  
class UserRoleSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    teams = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'role_display', 'teams']

    def get_full_name(self, user):
        # Combine first and last names
        return f"{user.first_name} {user.last_name}".strip()

    def get_teams(self, user):
        # Due to circular dependency
        from team.models import TeamMembership
        memberships = TeamMembership.objects.filter(user=user)
        teams = [membership.team.name for membership in memberships]  # Return only team names
        return teams