from django.db import models
from django.conf import settings

# Create your models here.
# TEAM 
class Team(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_teams')

    def __str__(self):
        return self.name

# TEAM MEMBERS 
class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    
    def __str__(self):
        return f"{self.user.username} in {self.team.name} as {self.user.get_role_display()}"

    class Meta:
        unique_together = ('team', 'user')  # Ensures that a user can only be in a team once