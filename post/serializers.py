from rest_framework import serializers
from django.db.models import Q
from . import models

# Optimized Serializer Code

class PostAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PostAttribute
        fields = ['id', 'name', 'attribute_type', 'is_active','created_by']
        extra_kwargs = {
            'name': {
                'trim_whitespace': True,
                'allow_blank': False,
                'max_length': 255  # Assuming reasonable max length
            },
            'is_active': {'default': False}  # Default to inactive
        }

    def validate(self, attrs):
        # Comprehensive validation including case-insensitive name uniqueness
        # and attribute type validation if needed.
        
        attrs = super().validate(attrs)
        self._validate_unique_name(attrs.get('name'))
        return attrs

    def _validate_unique_name(self, name):
        # Validates name uniqueness in a case-insensitive manner.
        # Optimized to use a single query that excludes current instance.
        if not name:  # Handled by field-level validation
            return

        query = Q(name__iexact=name)
        if self.instance and self.instance.pk:
            query &= ~Q(pk=self.instance.pk)

        if models.PostAttribute.objects.filter(query).exists():
            raise serializers.ValidationError(
                {'name': 'An attribute with this name already exists.'},
                code='unique'
            )

# Previous Serializer Code (for reference)

# from rest_framework import serializers
# from . import models


# class PostAttributeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.PostAttribute
#         fields = ['id', 'name', 'attribute_type', 'is_active']

#     def validate_name(self, value):
#         """
#         Check for duplicate names.
#         """
#         # Ensure the name is unique, ignoring the instance itself during updates
#         if models.PostAttribute.objects.filter(name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
#             raise serializers.ValidationError("An attribute with this name already exists.")
#         return value
    