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













