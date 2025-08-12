from django.shortcuts import render
from pro_app.permissions import IsMarketingDirector
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from . import models, serializers
from rest_framework.response import Response




# Create your views here.
class PostAttributeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    serializer_class = serializers.PostAttributeSerializer
    queryset = models.PostAttribute.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the attribute as inactive by default
            post_attribute = serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostAttributeByTypeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PostAttributeSerializer

    def get_queryset(self):
        # Get the type of the attribute from the URL
        attribute_type = self.kwargs.get('attribute_type')

        # Filter the PostAttribute model by the given type and only active attributes
        return models.PostAttribute.objects.filter(attribute_type=attribute_type)

class PostAttributeUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    queryset = models.PostAttribute.objects.all()
    serializer_class = serializers.PostAttributeSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Allow partial updates by default
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            # Save the updated attribute, reflecting any changes
            serializer.save()

            # Handle any special cases for activated or deactivated attributes if necessary
            if 'is_active' in request.data:
                if request.data['is_active']:  # If the attribute is activated
                    print(f"Attribute '{instance.name}' activated.")
                else:  # If the attribute is deactivated
                    print(f"Attribute '{instance.name}' deactivated.")

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
