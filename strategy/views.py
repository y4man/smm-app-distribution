from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Strategy
from .serializers import StrategySerializer
from client.models import Clients

# Create your views here.
class StrategyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id, *args, **kwargs):
        """
        Retrieve all strategies or a specific strategy for a client.
        """
        strategy = get_object_or_404(Strategy, client_id=client_id)
        name = request.query_params.get('name')  # Optional query parameter to retrieve a specific object

        if name:
            # Return a specific strategy object
            strategies = strategy.strategies
            if name in strategies:
                return Response({name: strategies[name]}, status=status.HTTP_200_OK)
            return Response({"error": f"Strategy '{name}' not found."}, status=status.HTTP_404_NOT_FOUND)

        # Return all strategies
        serializer = StrategySerializer(strategy)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, client_id, *args, **kwargs):
        """
        Create or update strategies for a specific client.
        """
        client = get_object_or_404(Clients, id=client_id)
        data = request.data  # Expect a dictionary of strategies
        created_by = request.user

        # Ensure the strategies field is properly initialized
        strategy_instance, created = Strategy.objects.get_or_create(client=client, defaults={
            "created_by": created_by,
            "strategies": {}
        })

        # Update the strategies with the new data
        strategies = strategy_instance.strategies
        for name, value in data.items():
            strategies[name] = value

        # Save the updated strategies
        strategy_instance.strategies = strategies
        strategy_instance.save()

        # Build the response
        response_data = {
            "id": strategy_instance.id,
            "client_id": strategy_instance.client.id,
            "created_by": strategy_instance.created_by.id if strategy_instance.created_by else None,
            "strategies": strategies,
            "created_at": strategy_instance.created_at,
            "updated_at": strategy_instance.updated_at,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def patch(self, request, client_id, *args, **kwargs):
        """
        Remove a specific strategy object by its title.
        """
        client = get_object_or_404(Clients, id=client_id)
        strategy_instance = get_object_or_404(Strategy, client=client)

        # Extract the title from the request
        title = request.data.get('title')
        if not title:
            return Response({"error": "A title must be provided to remove a strategy."}, status=status.HTTP_400_BAD_REQUEST)

        strategies = strategy_instance.strategies

        # Check if the title exists in strategies
        if title not in strategies:
            return Response({"error": f"Strategy with title '{title}' not found."}, status=status.HTTP_404_NOT_FOUND)

        # Remove the strategy
        del strategies[title]

        # Save the updated strategies
        strategy_instance.strategies = strategies
        strategy_instance.save()

        return Response({"message": f"Strategy '{title}' removed successfully.", "strategies": strategies}, status=status.HTTP_200_OK)
