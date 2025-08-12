from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

# Import your custom modules
from .models import Plans
from account.models import CustomUser
from client.models import Clients
from .serializers import PlanSerializer,PlanAssignSerializer
from pro_app.permissions import IsMarketingDirector
from user.serializers import UserSerializer


# Create your views here.
class PlanView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    queryset = Plans.objects.all()
    serializer_class = PlanSerializer

    # List all plans or create a new plan
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)  # Retrieve a specific plan by ID
        return self.list(request, *args, **kwargs)  # List all plans

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            # Create the new plan
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update a plan
    def put(self, request, *args, **kwargs):
        # Retrieve the plan to be updated
        plan = self.get_object()
        data = request.data

        # Merge the pricing_attributes field
        if 'pricing_attributes' in data:
            current_pricing_attributes = plan.pricing_attributes or {}
            current_pricing_attributes.update(data.get('pricing_attributes', {}))
            data['pricing_attributes'] = current_pricing_attributes

        # Merge the standard_attributes field
        if 'standard_attributes' in data:
            current_standard_attributes = plan.standard_attributes or {}
            current_standard_attributes.update(data.get('standard_attributes', {}))
            data['standard_attributes'] = current_standard_attributes

        # Merge the advanced_attributes field
        if 'advanced_attributes' in data:
            current_advanced_attributes = plan.advanced_attributes or {}
            current_advanced_attributes.update(data.get('advanced_attributes', {}))
            data['advanced_attributes'] = current_advanced_attributes

        # Merge the pricing_platforms field
        if 'pricing_platforms' in data:
            current_pricing_platforms = plan.pricing_platforms or {}
            current_pricing_platforms.update(data.get('pricing_platforms', {}))
            data['pricing_platforms'] = current_pricing_platforms

        # Pass the merged data to the serializer for validation
        serializer = self.get_serializer(plan, data=data, partial=True)  # Allow partial updates

        if serializer.is_valid():
            # Save the updated plan
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Handle the deletion of a plan
    def delete(self, request, *args, **kwargs):
        plan = get_object_or_404(Plans, pk=kwargs['pk'])
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
      
class PlanAssignView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    queryset = Plans.objects.all()
    serializer_class = PlanAssignSerializer

    def update(self, request, *args, **kwargs):
        plan = self.get_object()
        serializer = self.get_serializer(plan, data=request.data, partial=True)
        
        if serializer.is_valid():
            account_manager_id = serializer.validated_data.get('account_manager_id')

            # Check if the account manager already has an assigned plan
            if account_manager_id:
                existing_plan = models.Plans.objects.filter(assigned_account_managers=account_manager_id).exclude(id=plan.id).first()
                
                if existing_plan:
                    return Response(
                        {"detail": "This account manager is already assigned to another plan."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Save the updated plan with assigned account managers
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UnassignedAccountManagerSearchView(APIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]

    def post(self, request, *args, **kwargs):
        # Get data from the request body
        agency_name = request.data.get('agency_name', None)
        first_name = request.data.get('first_name', None)
        last_name = request.data.get('last_name', None)
        role = request.data.get('role', 'account_manager')  # Default to 'account_manager' if role is not provided

        # Build the query based on provided parameters
        query = Q(role=role)
        
        if agency_name:
            query &= Q(agency_name__icontains=agency_name)
        
        if first_name:
            query &= Q(first_name__icontains=first_name)

        if last_name:
            query &= Q(last_name__icontains=last_name)

        # Exclude account managers (or users with any specified role) already assigned to any plan
        query &= Q(assigned_plans__isnull=True)

        # Search for users that match the criteria and are not assigned to any plan
        account_managers = CustomUser.objects.filter(query)

        # Serialize the results
        serializer = UserSerializer(account_managers, many=True)
        
        # Return the response with the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)

class AssignedAccountManagerSearchView(APIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]

    def get(self, request, *args, **kwargs):
        # Get query parameters for searching
        plan_id = request.query_params.get('plan_id', None)  # Plan ID to search for assigned account managers

        if not plan_id:
            return Response({"error": "Plan ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the plan instance
        plan = get_object_or_404(Plans, id=plan_id)

        # Retrieve all account managers assigned to the specific plan using the related name "assigned_plans"
        assigned_account_managers = CustomUser.objects.filter(assigned_plans=plan)

        # Serialize the results
        serializer = UserSerializer(assigned_account_managers, many=True)
        
        # Return the response with the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)

class AssignedPlansForAccountManagerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id, *args, **kwargs):
        # Retrieve the client instance based on the client_id from the URL
        client = get_object_or_404(Clients, id=client_id)

        # Retrieve the Account Manager related to the client
        account_manager = client.account_manager  # Assuming a ForeignKey relation exists in Client model

        # Validate if Account Manager is found
        if not account_manager:
            return Response({"error": "No Account Manager associated with this Client ID."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve assigned plans for the Account Manager
        assigned_plans = account_manager.assigned_plans.all()

        # Debugging: Log the plans to verify
        print(f"Assigned Plans for Client {client_id} (Account Manager {account_manager.id}): {[plan.plan_name for plan in assigned_plans]}")

        # Serialize the assigned plans
        serializer = PlanSerializer(assigned_plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RemoveAccountManagerFromPlanView(APIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]

    def post(self, request, *args, **kwargs):
        # Get the plan ID and account manager ID from the request data
        plan_id = request.data.get('plan_id')
        account_manager_id = request.data.get('account_manager_id')

        # Ensure both plan ID and account manager ID are provided
        if not plan_id or not account_manager_id:
            return Response({"error": "Both plan_id and account_manager_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the plan and account manager instances
        plan = get_object_or_404(Plans, id=plan_id)
        account_manager = get_object_or_404(CustomUser, id=account_manager_id, role='account_manager')

        # Check if the account manager is assigned to the plan
        if account_manager in plan.account_managers.all():
            # Remove the account manager from the plan
            plan.account_managers.remove(account_manager)
            return Response({"message": f"Account Manager '{account_manager.username}' removed from Plan '{plan.plan_name}'."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": f"Account Manager '{account_manager.username}' is not assigned to Plan '{plan.plan_name}'."}, status=status.HTTP_400_BAD_REQUEST)
