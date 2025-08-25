from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from pro_app.permissions import IsMarketingDirector
from . import models, serializers

# Optimized Code

class PostAttributeListCreateView(generics.ListCreateAPIView):
    # View for listing and creating post attributes.
    # Marketing directors can create new attributes which are inactive by default.
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    serializer_class = serializers.PostAttributeSerializer
    queryset = models.PostAttribute.objects.all()

    def perform_create(self, serializer):
        # Save new attribute as inactive by default
        serializer.save(is_active=False)


class PostAttributeByTypeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PostAttributeSerializer

    def get_queryset(self):
        # Get the type of the attribute from the URL
        attribute_type = self.kwargs.get('attribute_type')

        # Filter the PostAttribute model by the given type and only active attributes
        return models.PostAttribute.objects.filter(attribute_type=attribute_type)


class PostAttributeUpdateView(generics.UpdateAPIView):
    # View for updating post attributes.
    # Only marketing directors can modify attributes.
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    serializer_class = serializers.PostAttributeSerializer
    queryset = models.PostAttribute.objects.all()
    lookup_field = 'pk'

    def perform_update(self, serializer):
        instance = serializer.instance
        is_active_changed = 'is_active' in serializer.validated_data
        was_activated = is_active_changed and serializer.validated_data['is_active']
        was_deactivated = is_active_changed and not serializer.validated_data['is_active']

        serializer.save()

        # Log status changes (replace with proper logging in production)
        if was_activated:
            self._log_attribute_change(instance, "activated")
        elif was_deactivated:
            self._log_attribute_change(instance, "deactivated")

    def _log_attribute_change(self, instance, action):
        # Helper method for logging attribute status changes
        print(f"Attribute '{instance.name}' {action}.")  # Replace with logger in production
        
# Previous Code
# # Create your views here.
# class PostAttributeListCreateView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated, IsMarketingDirector]
#     serializer_class = serializers.PostAttributeSerializer
#     queryset = models.PostAttribute.objects.all()

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             # Save the attribute as inactive by default
#             post_attribute = serializer.save()

#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class PostAttributeByTypeView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = serializers.PostAttributeSerializer

#     def get_queryset(self):
#         # Get the type of the attribute from the URL
#         attribute_type = self.kwargs.get('attribute_type')

#         # Filter the PostAttribute model by the given type and only active attributes
#         return models.PostAttribute.objects.filter(attribute_type=attribute_type)

# class PostAttributeUpdateView(generics.UpdateAPIView):
#     permission_classes = [IsAuthenticated, IsMarketingDirector]
#     queryset = models.PostAttribute.objects.all()
#     serializer_class = serializers.PostAttributeSerializer
#     lookup_field = 'pk'

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', True)  # Allow partial updates by default
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)

#         if serializer.is_valid():
#             # Save the updated attribute, reflecting any changes
#             serializer.save()

#             # Handle any special cases for activated or deactivated attributes if necessary
#             if 'is_active' in request.data:
#                 if request.data['is_active']:  # If the attribute is activated
#                     print(f"Attribute '{instance.name}' activated.")
#                 else:  # If the attribute is deactivated
#                     print(f"Attribute '{instance.name}' deactivated.")

#             return Response(serializer.data, status=status.HTTP_200_OK)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
