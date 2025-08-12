from rest_framework import serializers
from . import models


class PostAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PostAttribute
        fields = ['id', 'name', 'attribute_type', 'is_active']

    def validate_name(self, value):
        """
        Check for duplicate names.
        """
        # Ensure the name is unique, ignoring the instance itself during updates
        if models.PostAttribute.objects.filter(name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("An attribute with this name already exists.")
        return value
    