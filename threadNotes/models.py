from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class ClientMessageThread(models.Model):
    client = models.ForeignKey('client.Clients', on_delete=models.CASCADE, related_name='message_threads')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Client Message Thread'
        verbose_name_plural = 'Client Message Threads'
        ordering = ['-created_at']

    def sender_info(self):
        # Retrieve the required details from the sender
        if self.sender:
            return {
                "id": self.sender.id,
                "name": f"{self.sender.first_name} {self.sender.last_name}",
                "role": self.sender.get_role_display(),
                "profile_image": self.sender.profile.url if self.sender.profile else None,  # Adjusted for profile image
            }
        return None

    def __str__(self):
        return f"Message by {self.sender} in thread for client {self.client.business_name}"

#notes
class Notes(models.Model):
    """A model to represent notes/messages related to a team."""
    note_title = models.CharField(max_length=255, help_text="The title of the note.")  # New field for note title
    message = models.TextField(help_text="The message or content of the note.")
    # team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='notes', help_text="The team this note is related to.")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notes', help_text="The user who created the note.")
    note_flag = models.BooleanField(default=False, help_text="Flag to indicate if the note is pinned or unpinned.")  # New field for pin/unpin flag
    created_at = models.DateTimeField(default=timezone.now, help_text="The timestamp when the note was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="The timestamp when the note was last updated.")

    def __str__(self):
        return f"Note '{self.note_title}' by {self.sender} for Team {self.team} - Created on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ['-created_at']
   