from django.conf import settings
from rest_framework import serializers
from . import models
from supabase import create_client
from account.models import CustomUser
from calender.models import ClientCalendar

# for deleting old profiles
_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
storage = _supabase.storage.from_(settings.SUPABASE_BUCKET)






class AccountManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name']

# USERS 
# class UserSerializer(serializers.ModelSerializer):
#     role_display  = serializers.CharField(source="get_role_display", read_only=True)
#     teams         = serializers.SerializerMethodField()
    
#     # on reads, this returns the full Supabase URL (+ cache-buster)
#     profile       = serializers.SerializerMethodField()
#     # on writes, this accepts a new image to upload
#     profile_file  = serializers.ImageField(
#         write_only=True,
#         required=False,
#         allow_null=True
#     )
    
#     password = serializers.CharField(write_only=True, required=False)

#     class Meta:
#         model  = models.CustomUser
#         fields = [
#             "id", "email", "username", "first_name", "last_name", "role",
#             "agency_name", "agency_slug", "acc_mngr_id", "role_display", "is_active", "date_joined",
#             "teams", "profile", "profile_file", "password",
#         ]

#     def get_teams(self, user):
#         return TeamSerializer(
#             [m.team for m in user.team_memberships.all()],
#             many=True
#         ).data

#     def get_profile(self, instance):
#         """
#         Build the full Supabase URL (with cache-buster).
#         instance.profile is a FieldFile, so we grab .name.
#         """
#         raw = instance.profile
#         if not raw:
#             return None

#         # extract the actual path string
#         key = raw.name  # e.g. "profiles/Capture_pzltGBC.JPG"
#         key = key.lstrip('/')  # just in case

#         # cache-buster suffix
#         suffix = ""
#         try:
#             meta = storage.get_metadata(key)
#             ts   = int(meta["updated_at"].timestamp())
#             suffix = f"?v={ts}"
#         except Exception:
#             pass

#         return (
#             f"{settings.SUPABASE_URL}"
#             f"/storage/v1/object/public/"
#             f"{settings.SUPABASE_BUCKET}/"
#             f"{key}{suffix}"
#         )

#     def validate(self, data):
#         if data.get("role") == "account_manager":
#             missing = {}
#             for fld in ("agency_name", "agency_slug"):
#                 if not data.get(fld):
#                     missing[fld] = "This field is required for account managers."
#             if missing:
#                 raise serializers.ValidationError(missing)
#         return data

#     def update(self, instance, validated_data):
#         if "password" in validated_data:
#             instance.set_password(validated_data.pop("password"))

#         new_file = validated_data.pop("profile_file", None)
#         if new_file:
#             old_key = instance.profile.name if instance.profile else None

#             # Save temp file
#             tmp_path = None
#             try:
#                 with tempfile.NamedTemporaryFile(delete=False) as tmp:
#                     for chunk in new_file.chunks():
#                         tmp.write(chunk)
#                     tmp_path = tmp.name

#                 new_key = f"profiles/{new_file.name}"

#                 # Upload to Supabase
#                 try:
#                     if old_key:
#                         storage.remove([old_key])
#                     storage.upload(
#                         file=tmp_path,
#                         path=new_key,
#                         file_options={"content-type": new_file.content_type}
#                     )
#                 except StorageApiError as exc:
#                     raw = exc.args[0] if exc.args else {}
#                     msg = raw.get("message", str(exc)) if isinstance(raw, dict) else str(exc)
#                     raise serializers.ValidationError({"profile_file": msg})
#             finally:
#                 if tmp_path and os.path.exists(tmp_path):
#                     os.unlink(tmp_path)

#             # Save new key to model (relative path only)
#             instance.profile = new_key

#         for attr, val in validated_data.items():
#             setattr(instance, attr, val)

#         instance.save()
#         return instance

# class UserSerializer(serializers.ModelSerializer):
#     role_display = serializers.CharField(source="get_role_display", read_only=True)
#     teams = serializers.SerializerMethodField()
#     profile = serializers.SerializerMethodField()
#     profile_file = serializers.ImageField(
#         write_only=True,
#         required=False,
#         allow_null=True
#     )
#     password = serializers.CharField(write_only=True, required=False)

#     class Meta:
#         model = models.CustomUser
#         fields = [
#             "id", "email", "username", "first_name", "last_name", "role",
#             "agency_name", "agency_slug", "acc_mngr_id", "role_display", 
#             "is_active", "date_joined", "teams", "profile", "profile_file", "password",
#         ]
#         # Note: profile_file is now included in fields list
#         # Removed the duplicate "profile" entry

#     def get_teams(self, user):
#         return TeamSerializer(
#             [m.team for m in user.team_memberships.all()],
#             many=True
#         ).data

#     def get_profile(self, instance):
#         if not instance.profile:
#             return None
            
#         return (
#             f"{settings.SUPABASE_URL}"
#             f"/storage/v1/object/public/"
#             f"{settings.SUPABASE_BUCKET}/"
#             f"{instance.profile.name}"
#         )

#     def validate(self, data):
#         if data.get("role") == "account_manager":
#             missing = {}
#             for fld in ("agency_name", "agency_slug"):
#                 if not data.get(fld):
#                     missing[fld] = "This field is required for account managers."
#             if missing:
#                 raise serializers.ValidationError(missing)
#         return data

#     def update(self, instance, validated_data):
#         # Handle password update
#         if "password" in validated_data:
#             instance.set_password(validated_data.pop("password"))
            
#         # Other fields will be handled by the view's perform_update
#         for attr, val in validated_data.items():
#             if attr != 'profile_file':  # profile_file is handled in the view
#                 setattr(instance, attr, val)

#         instance.save()
#         return instance
 
 
  
# class UserRoleSerializer(serializers.ModelSerializer):
#     role_display = serializers.CharField(source='get_role_display', read_only=True)
#     teams = serializers.SerializerMethodField()
#     full_name = serializers.SerializerMethodField()

#     class Meta:
#         model = models.CustomUser
#         fields = ['id', 'username', 'full_name', 'role_display', 'teams']

#     def get_full_name(self, user):
#         # Combine first and last names
#         return f"{user.first_name} {user.last_name}".strip()

#     def get_teams(self, user):
#         memberships = models.TeamMembership.objects.filter(user=user)
#         teams = [membership.team.name for membership in memberships]  # Return only team names
#         return teams

# CLIENTS 
# class ClientSerializer(serializers.ModelSerializer):
#     # Get a single plan for the client, if it exists
#     client_plan = serializers.SerializerMethodField()
#     team = serializers.SerializerMethodField()  # Custom field for team with ID and name

#     class Meta:
#         model = models.Clients
#         fields = '__all__'
#         extra_kwargs = {
#             'account_manager': {'required': False},
#         }

#     def get_client_plan(self, obj):
#         # Retrieve the latest or most relevant plan for the client
#         client_plan = obj.client_plans.first()
#         if client_plan:
#             return {
#                 "id": client_plan.id,
#                 "plan_type": client_plan.plan_type,
#                 "attributes": client_plan.attributes,
#                 "platforms": client_plan.platforms,
#                 "add_ons": client_plan.add_ons,
#                 "grand_total": client_plan.grand_total,
#                 "created_at": client_plan.created_at,
#                 "updated_at": client_plan.updated_at
#             }
#         return None

#     def get_team(self, obj):
#         # Include both team ID and name if a team is assigned
#         if obj.team:
#             return {
#                 "id": obj.team.id,
#                 "name": obj.team.name
#             }
#         return None
    
#     #CONDITION FOR DUPLICATE BUSINESS NAMES
#     def validate_business_name(self, value):
#         if models.Clients.objects.filter(business_name__iexact=value).exists():
#             raise serializers.ValidationError("A client with this business name already exists.")
#         return value

# class ClientWebDevDataSerializer(serializers.ModelSerializer):
#     client = serializers.PrimaryKeyRelatedField(read_only=True)  # Make client read-only, as it will be set in the view
#     class Meta:
#         model = models.ClientWebDevData
#         fields = '__all__'

#     def validate(self, data):
#         # Conditional field validation
#         if data['website_type'] == 'ecommerce' and not data.get('num_of_products'):
#             raise serializers.ValidationError("Number of products is required for eCommerce websites.")
#         if data['domain'] == 'yes' and not data.get('domain_info'):
#             raise serializers.ValidationError("Domain information is required if domain is 'yes'.")
#         if data['hosting'] == 'yes' and not data.get('hosting_info'):
#             raise serializers.ValidationError("Hosting information is required if hosting is 'yes'.")
#         return data

#AFTER MERGE




# CALENDER 

# class ClientCalendarDateSerializer(serializers.ModelSerializer):
#     # proposal_pdf = serializers.FileField(required=False)
#     calendar = serializers.PrimaryKeyRelatedField(queryset=models.ClientCalendar.objects.all())

#     class Meta:
#         model = models.ClientCalendarDate
#         fields = '__all__'


# TEAM 


# MEETINGS 
class MeetingSerializer(serializers.ModelSerializer):
    # Read-only fields for existing data
    scheduled_by_id = serializers.IntegerField(source='scheduled_by.id', read_only=True)
    client_name = serializers.CharField(source='client.business_name', read_only=True)  
    client = serializers.PrimaryKeyRelatedField(queryset=models.Clients.objects.all())

    # Custom field to return an array with required data
    details = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
        fields = [
            'id', 'date', 'time', 'meeting_name', 'meeting_link', 'timezone', 'client', 'client_name', 'team', 
            'is_completed', 'scheduled_by_id', 'details'
        ]

    def get_details(self, obj):
        return [
            obj.team.name if obj.team else None,
            obj.scheduled_by.role if obj.scheduled_by else None,
            obj.marketing_manager.role if obj.marketing_manager else None
        ]

class SpecificMeetingSerializer(serializers.ModelSerializer):
    # Read-only fields for existing data
    client_name = serializers.CharField(source='client.business_name', read_only=True)
    
    # Custom field to return an array with required data
    details = serializers.SerializerMethodField()

    class Meta:
        model = models.Meeting
        fields = [
            'id', 'date', 'time', 'meeting_name', 'meeting_link', 'timezone', 'client', 'client_name',
            'is_completed', 'scheduled_by_id', 'details'
        ]

    def get_details(self, obj):
        details_list = [
            obj.scheduled_by.role if obj.scheduled_by else None,
            obj.team.name if obj.team else "No team assigned with this client",
            obj.marketing_manager.role if obj.marketing_manager else None
        ]
        # Remove any None values from the list
        return [detail for detail in details_list if detail is not None]














