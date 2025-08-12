from .models import Strategy
from rest_framework import serializers


class StrategySerializer(serializers.ModelSerializer):
     class Meta:
        model = Strategy
        fields = ['id', 'client', 'created_by', 'strategies', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
