from channels.generic.websocket import AsyncWebsocketConsumer
import json

# AI generated consumer to use as a template
class CoreWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        self.group_name = "core_group"

        # Add the connection to a group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        # Remove the connection from the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        message = data.get("message", "")

        # Broadcast the message to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket clients
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))