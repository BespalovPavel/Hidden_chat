import asyncio
import os
import logging
from typing import Dict
from fastapi import WebSocket
import redis.asyncio as redis

logger = logging.getLogger(__name__)

from backend.application.schemas import Message

class ConnectionManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

        self.room_subscription_events: Dict[str, asyncio.Event] = {}


    async def connect(self, websocet: WebSocket, room_id: str, user_id: str):
        await websocet.accept()

        history = await self.get_messages(room_id)

        for message in history:
            await websocet.send_text(message)

        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

            event = asyncio.Event()
            self.room_subscription_events[room_id] = event


            await self._start_listening_room(room_id)

            try:
                await asyncio.wait_for(event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for Redis subscription in room {room_id}")
            finally:
                if room_id in self.room_subscription_events:
                    del self.room_subscription_events[room_id]

        if user_id in self.active_connections[room_id]:
            try:
                await self.active_connections[room_id][user_id].close()
            except:
                pass

        self.active_connections[room_id][user_id] = websocet

    def disconnect(self, room_id:str, user_id: str):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                self._stop_listening_room(room_id)

    async def get_messages(self, room_id: str):
        return await self.redis_client.lrange(f"history:{room_id}", 0, -1)
    
    async def _add_to_history(self, room_id: str, message: Message):
        data = message.model_dump_json()
        key = f"history:{room_id}"

        await self.redis_client.rpush(key, data)
        await self.redis_client.ltrim(key, -50, -1)
        
    async def _start_listening_room(self, room_id: str):
        if room_id not in self.pubsub_tasks:
            self.pubsub_tasks[room_id] = asyncio.create_task(self._redis_listener(room_id))

    def _stop_listening_room(self, room_id: str):
        if room_id in self.pubsub_tasks:
            self.pubsub_tasks[room_id].cancel()
            del self.pubsub_tasks[room_id]


    async def _redis_listener(self, room_id: str):
        redis_sub = redis.from_url(self.redis_url, decode_responses=True)
        pubsub = redis_sub.pubsub()

        await pubsub.subscribe(f"chat:{room_id}")

        if room_id in self.room_subscription_events:
            self.room_subscription_events[room_id].set()

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._broadcast_to_local(message["data"], room_id)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(f"chat:{room_id}")
            await redis_sub.close()

    async def _broadcast_to_local(self, message_json: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_text(message_json)

    async def broadcast_message(self, room_id: str, message: Message):
        await self._add_to_history(room_id, message)

        await self.redis_client.publish(f"chat:{room_id}", message.model_dump_json())


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
manager = ConnectionManager(REDIS_URL)