from rest_framework import serializers
from .models import Plans
from account.models import CustomUser
from client.models import ClientsPlan

# Optimized code

class PlanSerializer(serializers.ModelSerializer):
    account_managers = serializers.SerializerMethodField()

    class Meta:
        model = Plans
        fields = '__all__'

    def validate_standard_attributes(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Standard attributes must be a dictionary.")
        return value

    def validate_advanced_attributes(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Advanced attributes must be a dictionary.")
        return value

    def get_account_managers(self, obj):
        account_managers = obj.account_managers.all()
        return [
            {"id": manager.id, "name": f"{manager.first_name} {manager.last_name}".strip()}
            for manager in account_managers
        ]


class PlanAssignSerializer(serializers.ModelSerializer):
    account_managers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.filter(role='account_manager')  # filtered for safety
    )

    class Meta:
        model = Plans
        fields = ['plan_name', 'account_managers']


class ClientPlanSerializer(serializers.ModelSerializer):
    addon_attributes = serializers.JSONField(source='attributes')

    class Meta:
        model = ClientsPlan
        fields = [
            'client', 'plan_type', 'addon_attributes',
            'platforms', 'grand_total', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'client': {'read_only': True}
        }

# Previous code
# class PlanSerializer(serializers.ModelSerializer):
#     account_managers = serializers.SerializerMethodField()

#     class Meta:
#         model = Plans
#         fields = '__all__'

#     def validate_standard_attributes(self, value):
#         if not isinstance(value, dict):
#             raise serializers.ValidationError("Standard attributes must be a dictionary.")
#         return value

#     def validate_advanced_attributes(self, value):
#         if not isinstance(value, dict):
#             raise serializers.ValidationError("Advanced attributes must be a dictionary.")
#         return value
    
#     def get_account_managers(self, obj):
#         # Return a list of dictionaries, each containing an account manager's ID and full name
#         return [
#             {"id": manager.id, "name": f"{manager.first_name} {manager.last_name}"}
#             for manager in obj.account_managers.all()
#         ]

# class PlanAssignSerializer(serializers.ModelSerializer):
#     account_managers = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=CustomUser.objects.all()
#     )

#     class Meta:
#         model = Plans
#         fields = ['plan_name', 'account_managers']


# class ClientPlanSerializer(serializers.ModelSerializer):
#     addon_attributes = serializers.JSONField(source='attributes') 
#     class Meta:
#         model = ClientsPlan
#         fields = ['client', 'plan_type', 'addon_attributes', 'platforms', 'grand_total', 'created_at', 'updated_at']
#         extra_kwargs = {
#             "client": {'read_only': True},
#         }
