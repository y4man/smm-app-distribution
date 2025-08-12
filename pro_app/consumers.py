from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
User = get_user_model()


# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Assign a unique group name for the WebSocket connection
#         self.group_name = "notifications"

#         # Add the connection to the WebSocket group
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()
#         print(f"WebSocket connected: {self.channel_name}")

#     async def disconnect(self, close_code):
#         # Remove the connection from the WebSocket group
#         print(f"WebSocket disconnected with close code: {close_code}")
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         print(f"WebSocket disconnected: {self.channel_name}")

#     async def receive(self, text_data):
#         try:
#             if not text_data.strip():
#                 print("Received empty text_data")
#                 return  # Do nothing for empty messages

#             # Check if the message is a STOMP frame (starts with a known STOMP command)
#             if text_data.startswith(("CONNECT", "SUBSCRIBE", "UNSUBSCRIBE", "SEND", "DISCONNECT")):
#                 print(f"Received STOMP frame: {text_data}")
#                 return  # Ignore STOMP protocol frames

#             # Parse the JSON message
#             data = json.loads(text_data)
#             print(f"Received data: {data}")

#             # Send the parsed data to the WebSocket group
#             await self.channel_layer.group_send(
#                 self.group_name,
#                 {
#                     "type": "send_notification",
#                     "notification": data,  # Use the data as the notification payload
#                 },
#             )
#         except json.JSONDecodeError as e:
#             print(f"JSON decoding error: {e}. Received text_data: {text_data}")


#     async def send_notification(self, event):
#         """Handle sending notifications to WebSocket."""
#         notification = event.get("notification")  # Extract the notification data
#         if notification:
#             await self.send(text_data=json.dumps(notification))
#             print(f"Notification sent to WebSocket: {notification}")
#         else:
#             print("No notification data found in event.")


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get the user ID from query parameters
            query_string = self.scope['query_string'].decode()
            query_params = dict(param.split('=') for param in query_string.split('&') if param)
            user_id = query_params.get('user_id')
            if user_id:
                user = await self.get_user_by_id(user_id)
                if user:
                    self.user = user
                    self.group_name = f"notifications_{self.user.id}"
                    # Add the user to their unique WebSocket group
                    await self.channel_layer.group_add(self.group_name, self.channel_name)
                    await self.accept()
                    print(f"WebSocket connected: {self.channel_name} for user {self.user.username}")
                else:
                    print(f"User with ID {user_id} not found")
                    await self.close()
            else:
                print("No user ID provided")
                await self.close()
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"WebSocket disconnected: {self.channel_name}")
    async def send_notification(self, event):
        """Handle sending notifications to WebSocket."""
        notification = event.get("notification")
        if notification:
            await self.send(text_data=json.dumps(notification))
            print(f"Notification sent to WebSocket: {notification}")
        else:
            print("No notification data found in event.")

