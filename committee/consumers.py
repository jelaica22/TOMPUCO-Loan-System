# committee/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from main.models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            # Create a unique group for this user
            self.room_group_name = f'notifications_{self.user.id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

            # Send initial unread count
            unread_count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'initial',
                'unread_count': unread_count
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    unread_count = await self.get_unread_count()
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'count_update',
                            'unread_count': unread_count
                        }
                    )

        except Exception as e:
            print(f"WebSocket error: {e}")

    async def new_notification(self, event):
        """Send new notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification'],
            'unread_count': event['unread_count']
        }))

    async def count_update(self, event):
        """Send count update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'count_update',
            'unread_count': event['unread_count']
        }))

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False