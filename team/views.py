from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Assuming you have custom permissions and models
from pro_app.permissions import IsMarketingDirector 
from .models import Team,TeamMembership
from account.models import CustomUser
from . import serializers  

# Create your views here.
class TeamListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    queryset = Team.objects.all()
    serializer_class = serializers.TeamSerializer

    # Allowed roles in a team
    REQUIRED_ROLES = {'marketing_manager', 'marketing_assistant', 'content_writer', 'graphics_designer'}

    def create(self, request, *args, **kwargs):
        # Extract team data from the request
        team_data = request.data.get('team', {})
        
        # Add the current account manager as the creator of the team
        team_data['created_by'] = request.user.id  # Assuming 'created_by' is in the Team model

        # Create the team
        team_serializer = self.get_serializer(data=team_data)
        if team_serializer.is_valid():
            team = team_serializer.save()

            # Add members to the team
            members_data = request.data.get('members', [])
            roles_added = set()
            members_added = []

            for member_data in members_data:
                user_id = member_data.get('user_id')
                user = CustomUser.objects.get(id=user_id)

                # Check if the user's role is in the allowed roles
                if user.role not in self.REQUIRED_ROLES:
                    return Response(
                        {"error": f"Invalid role: {user.role}. Only {', '.join(self.REQUIRED_ROLES)} roles are allowed in the team."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                membership = models.TeamMembership.objects.create(team=team, user=user)
                roles_added.add(user.role)
                members_added.append({
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.get_role_display()
                })

            # Check if the team is complete based on the required roles
            missing_roles = self.REQUIRED_ROLES - roles_added
            team_status = "complete" if not missing_roles else f"incomplete, missing roles: {', '.join(missing_roles)}"

            response_data = {
                'team': team_serializer.data,
                'members': members_added,
                'message': f"Team creation {team_status}."
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(team_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def list(self, request, *args, **kwargs):
        teams = self.get_queryset()
        team_data = []

        for team in teams:
            members_count = team.memberships.count()
            clients_count = team.clients.count()
            
            # Check if the team is complete
            team_roles = set(team.memberships.values_list('user__role', flat=True))
            missing_roles = self.REQUIRED_ROLES - team_roles
            team_status = "complete" if not missing_roles else f"incomplete, missing roles: {', '.join(missing_roles)}"

            team_data.append({
                'team_id': team.id,
                'name': team.name,
                'members_count': members_count,
                'clients_count': clients_count,
                'status': team_status
            })

        return Response(team_data, status=status.HTTP_200_OK)

class TeamRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]
    queryset = Team.objects.all()
    serializer_class = serializers.TeamSerializer

    # Allowed roles in a team
    REQUIRED_ROLES = {'marketing_manager', 'marketing_assistant', 'content_writer', 'graphics_designer'}

    def retrieve(self, request, *args, **kwargs):
        team = self.get_object()
        members = team.memberships.all()
        member_data = []

        for membership in members:
            member_data.append({
                'membership_id': membership.id,  # Include membership ID for member-specific actions
                'user_id': membership.user.id,
                'username': membership.user.username,
                'role': membership.user.get_role_display()
            })

        response_data = {
            'team': self.get_serializer(team).data,
            'members': member_data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Update the team details using request.data
        team_serializer = self.get_serializer(instance, data=request.data['team'], partial=partial)
        if team_serializer.is_valid():
            team = team_serializer.save()

            # Update members if 'members' key is present in the request data
            members_data = request.data.get('members', [])
            if members_data:
                roles_added = set()
                members_added = []

                for member_data in members_data:
                    user_id = member_data.get('user_id')
                    user = CustomUser.objects.get(id=user_id)
                    
                    # Check if the user's role is in the allowed roles
                    if user.role not in self.REQUIRED_ROLES:
                        return Response(
                            {"error": f"Invalid role: {user.role}. Only {', '.join(self.REQUIRED_ROLES)} roles are allowed in the team."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Create or update the membership
                    membership, created = models.TeamMembership.objects.update_or_create(
                        team=team, user=user, defaults={}
                    )
                    roles_added.add(user.role)
                    members_added.append({
                        'membership_id': membership.id,
                        'user_id': user.id,
                        'username': user.username,
                        'role': user.get_role_display()
                    })

                # Check if the team is complete based on the required roles
                missing_roles = self.REQUIRED_ROLES - roles_added
                team_status = "complete" if not missing_roles else f"incomplete, missing roles: {', '.join(missing_roles)}"

                response_data = {
                    'team': team_serializer.data,
                    'members': members_added,
                    'status': team_status
                }
            else:
                response_data = {
                    'team': team_serializer.data,
                    'members': "No members were provided for update."
                }

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(team_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        team.delete()
        return Response({"message": "Team deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    def remove_member(self, request, *args, **kwargs):
        """Remove a specific member from the team."""
        team = self.get_object()
        member_id = request.data.get('membership_id')

        try:
            membership = models.TeamMembership.objects.get(id=member_id, team=team)
            membership.delete()
            return Response({"message": "Member removed successfully."}, status=status.HTTP_200_OK)
        except models.TeamMembership.DoesNotExist:
            return Response({"error": "Member not found in this team."}, status=status.HTTP_404_NOT_FOUND)

    def edit_member(self, request, *args, **kwargs):
        """Edit a specific member's role in the team."""
        team = self.get_object()
        member_id = request.data.get('membership_id')
        new_role = request.data.get('new_role')

        if new_role not in self.REQUIRED_ROLES:
            return Response(
                {"error": f"Invalid role: {new_role}. Only {', '.join(self.REQUIRED_ROLES)} roles are allowed in the team."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = models.TeamMembership.objects.get(id=member_id, team=team)
            user = membership.user
            user.role = new_role
            user.save()
            return Response({
                "message": "Member role updated successfully.",
                "user_id": user.id,
                "username": user.username,
                "new_role": user.get_role_display()
            }, status=status.HTTP_200_OK)
        except models.TeamMembership.DoesNotExist:
            return Response({"error": "Member not found in this team."}, status=status.HTTP_404_NOT_FOUND)


