from rest_framework import serializers
from django.conf import settings
from .models import ClientCalendar, ClientCalendarDate



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


class ClientCalendarDateSerializer(serializers.ModelSerializer):
    # explicitly declare to get control over (de)serialization
    creatives = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of Supabase URL paths (no prefix) in the DB"
    )

    class Meta:
        model = ClientCalendarDate
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Called on input.  `data['creatives']` is a list of full URLs,
        so we strip off settings.MEDIA_URL before validation/save.
        """
        data = super().to_internal_value(data)
        urls = data.get('creatives', None)
        if urls is not None:
            prefix = settings.MEDIA_URL
            stripped = []
            for url in urls:
                if url.startswith(prefix):
                    stripped.append(url[len(prefix):])
                else:
                    # if it wasn’t a full URL we trust the client gave us a path
                    stripped.append(url)
            data['creatives'] = stripped
        return data

    def to_representation(self, instance):
        """
        Called on output.  `instance.creatives` is a list of paths;
        we re-prefix them so clients get full URLs again.
        """
        ret = super().to_representation(instance)
        paths = ret.get('creatives', [])
        full_urls = [settings.MEDIA_URL + p for p in paths]
        ret['creatives'] = full_urls
        return ret



class FilteredClientCalendarDateSerializer(serializers.ModelSerializer):
    creatives = serializers.SerializerMethodField()

    class Meta:
        model = ClientCalendarDate
        fields = [
            'id',
            'calendar', 'created_at', 'date', 'post_count', 'type', 'category',
            'cta', 'resource', 'tagline', 'caption', 'hashtags', 'creatives',
            'e_hooks', 'internal_status', 'client_approval', 'comments'
        ]

    def get_creatives(self, obj):
        if not obj.creatives or not isinstance(obj.creatives, list):
            return []
        
        # Process each creative URL in the list
        processed_creatives = []
        for creative_url in obj.creatives:
            if not creative_url:
                continue
                
            # If the URL is already a full URL, return it as-is
            if creative_url.startswith(('http://', 'https://')):
                processed_creatives.append(creative_url)
                continue
                
            # If it's just a path, construct the full Supabase URL
            processed_creatives.append(
                f"{settings.SUPABASE_URL}"
                f"/storage/v1/object/public/"
                f"{settings.SUPABASE_BUCKET}/"
                f"{creative_url.lstrip('/')}"  # Remove leading slash if present
            )
        
        return processed_creatives
        

