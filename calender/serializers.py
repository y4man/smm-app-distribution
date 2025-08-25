from rest_framework import serializers
from django.conf import settings
from .models import ClientCalendar, ClientCalendarDate
from django.utils.translation import gettext_lazy as _

# Optimized code for serializers

class BaseCalendarSerializer(serializers.ModelSerializer):
    # Base serializer with common fields and methods
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M', read_only=True)
    
    class Meta:
        abstract = True

# class ClientCalendarSerializer(BaseCalendarSerializer):
#     account_manager_details = serializers.SerializerMethodField()
#     client_details = serializers.SerializerMethodField()
#     completion_status = serializers.SerializerMethodField()

#     class Meta:
#         model = ClientCalendar
#         fields = [
#             'id',
#             'client_details',
#             'account_manager_details',
#             'created_at',
#             'month_name',
#             'completion_status',
#             'strategy_completed',
#             'content_completed',
#             'creatives_completed',
#             'mm_content_completed',
#             'acc_creative_completed',
#             'mm_creative_completed',
#             'acc_content_completed',
#             'smo_completed'
#         ]
#         read_only_fields = ['created_at']

#     def get_account_manager_details(self, obj):
#         # Consolidated account manager information
#         if not obj.client or not obj.client.account_manager:
#             return None
            
#         manager = obj.client.account_manager
#         return {
#             'id': manager.id,
#             'full_name': f"{manager.first_name} {manager.last_name}".strip(),
#             'username': manager.username,
#             'email': manager.email
#         }

#     def get_client_details(self, obj):
#         # Consolidated client information
#         if not obj.client:
#             return None
            
#         return {
#             'id': obj.client.id,
#             'business_name': obj.client.business_name,
#             'industry': obj.client.industry
#         }

#     def get_completion_status(self, obj):
#         # Calculate overall completion percentage
#         completed_fields = [
#             obj.strategy_completed,
#             obj.content_completed,
#             obj.creatives_completed,
#             obj.smo_completed
#         ]
#         completed_count = sum(1 for field in completed_fields if field)
#         return {
#             'percentage': int((completed_count / len(completed_fields)) * 100),
#             'completed': completed_count,
#             'total': len(completed_fields)
#         }

class ClientCalendarDateSerializer(BaseCalendarSerializer):
    creatives = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text=_("List of creative file paths or URLs")
    )
    approval_status = serializers.SerializerMethodField()

    class Meta:
        model = ClientCalendarDate
        fields = '__all__'
        extra_kwargs = {
            'internal_status': {'write_only': True},
            'client_approval': {'write_only': True}
        }

    def get_approval_status(self, obj):
        # Combine internal and client approval status
        return {
            'internal': obj.internal_status,
            'client': obj.client_approval
        }

    def to_internal_value(self, data):
        # Normalize creative URLs to storage paths
        data = super().to_internal_value(data)
        if 'creatives' in data:
            data['creatives'] = [
                self._normalize_creative_path(url) 
                for url in data['creatives'] 
                if url
            ]
        return data

    def to_representation(self, instance):
        # Convert storage paths to full URLs
        ret = super().to_representation(instance)
        if 'creatives' in ret:
            ret['creatives'] = [
                self._expand_creative_path(path) 
                for path in ret['creatives']
                if path
            ]
        return ret

    def _normalize_creative_path(self, url):
        # Extract just the path portion from a URL
        if url.startswith(settings.SUPABASE_URL):
            return url.split(settings.SUPABASE_BUCKET + '/')[-1]
        if url.startswith(settings.MEDIA_URL):
            return url[len(settings.MEDIA_URL):]
        return url.lstrip('/')

    def _expand_creative_path(self, path):
        """Convert storage path to full URL"""
        if path.startswith(('http://', 'https://')):
            return path
        return (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/"
            f"{settings.SUPABASE_BUCKET}/{path.lstrip('/')}"
        )

class FilteredClientCalendarDateSerializer(ClientCalendarDateSerializer):
    """Lightweight serializer for list views"""
    creative_count = serializers.SerializerMethodField()

    class Meta(ClientCalendarDateSerializer.Meta):
        fields = [
            'id',
            'date',
            'post_count',
            'type',
            'category',
            'creative_count',
            'approval_status',
            'comments'
        ]

    def get_creative_count(self, obj):
        return len(obj.creatives) if obj.creatives else 0



# Previous Code

# from rest_framework import serializers
# from django.conf import settings
# from .models import ClientCalendar, ClientCalendarDate

class ClientCalendarSerializer(serializers.ModelSerializer):
    calendar_id = serializers.ReadOnlyField(source='id')  # Add calendar ID
    account_manager_id = serializers.SerializerMethodField()  # Add account manager ID
    account_manager_name = serializers.SerializerMethodField()  # Add account manager name
    account_manager_username = serializers.SerializerMethodField()  # Add account manager name
    client_business_name = serializers.SerializerMethodField()  # Add client's business name
    class Meta:
        model = ClientCalendar
        fields = [
            'calendar_id',  # New field for calendar ID
            'account_manager_id',  # New field for account manager ID
            'account_manager_name',  # New field for account manager name
            'account_manager_username',
            'client_business_name',  # New field for client's business name
            'client',
            'created_at',
            'month_name',
            'strategy_completed',
            'content_completed',
            'creatives_completed',
            'mm_content_completed',
            'acc_creative_completed',
            'mm_creative_completed',
            'acc_content_completed'
        ]
    def get_account_manager_id(self, obj):
        # Retrieve the account manager ID from the related client
        return obj.client.account_manager.id if obj.client and obj.client.account_manager else None
    def get_account_manager_name(self, obj):
        # Retrieve the account manager's first and last name
        if obj.client and obj.client.account_manager:
            account_manager = obj.client.account_manager
            return f"{account_manager.first_name} {account_manager.last_name}"
        return None
    def get_account_manager_username(self, obj):
        #Retrieve the account manager's username
        if obj.client and  obj.client.account_manager:
            account_manager = obj.client.account_manager
            return f"{account_manager.username}"
    def get_client_business_name(self, obj):
        # Retrieve the client's business name
        return obj.client.business_name if obj.client else None


# class ClientCalendarDateSerializer(serializers.ModelSerializer):
#     # explicitly declare to get control over (de)serialization
#     creatives = serializers.ListField(
#         child=serializers.CharField(),
#         required=False,
#         help_text="List of Supabase URL paths (no prefix) in the DB"
#     )

#     class Meta:
#         model = ClientCalendarDate
#         fields = '__all__'

#     def to_internal_value(self, data):
#         """
#         Called on input.  `data['creatives']` is a list of full URLs,
#         so we strip off settings.MEDIA_URL before validation/save.
#         """
#         data = super().to_internal_value(data)
#         urls = data.get('creatives', None)
#         if urls is not None:
#             prefix = settings.MEDIA_URL
#             stripped = []
#             for url in urls:
#                 if url.startswith(prefix):
#                     stripped.append(url[len(prefix):])
#                 else:
#                     # if it wasn’t a full URL we trust the client gave us a path
#                     stripped.append(url)
#             data['creatives'] = stripped
#         return data

#     def to_representation(self, instance):
#         """
#         Called on output.  `instance.creatives` is a list of paths;
#         we re-prefix them so clients get full URLs again.
#         """
#         ret = super().to_representation(instance)
#         paths = ret.get('creatives', [])
#         full_urls = [settings.MEDIA_URL + p for p in paths]
#         ret['creatives'] = full_urls
#         return ret



# class FilteredClientCalendarDateSerializer(serializers.ModelSerializer):
#     creatives = serializers.SerializerMethodField()

#     class Meta:
#         model = ClientCalendarDate
#         fields = [
#             'id',
#             'calendar', 'created_at', 'date', 'post_count', 'type', 'category',
#             'cta', 'resource', 'tagline', 'caption', 'hashtags', 'creatives',
#             'e_hooks', 'internal_status', 'client_approval', 'comments'
#         ]

#     def get_creatives(self, obj):
#         if not obj.creatives or not isinstance(obj.creatives, list):
#             return []
        
#         # Process each creative URL in the list
#         processed_creatives = []
#         for creative_url in obj.creatives:
#             if not creative_url:
#                 continue
                
#             # If the URL is already a full URL, return it as-is
#             if creative_url.startswith(('http://', 'https://')):
#                 processed_creatives.append(creative_url)
#                 continue
                
#             # If it's just a path, construct the full Supabase URL
#             processed_creatives.append(
#                 f"{settings.SUPABASE_URL}"
#                 f"/storage/v1/object/public/"
#                 f"{settings.SUPABASE_BUCKET}/"
#                 f"{creative_url.lstrip('/')}"  # Remove leading slash if present
#             )
        
#         return processed_creatives
        

