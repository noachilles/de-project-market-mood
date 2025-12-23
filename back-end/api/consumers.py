# back-end/api/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StockConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. 프론트엔드가 접속하면 'stock_users' 그룹에 가입시킴
        self.group_name = "stock_users"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"✅ [WebSocket] Client Connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # 2. 연결 끊기면 그룹에서 제거
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❎ [WebSocket] Client Disconnected")

    # 3. 그룹에서 메시지를 받으면(From Bridge) -> 프론트엔드로 전송
    async def stock_message(self, event):
        data = event['message']
        
        # Vue에서 받기 편하게 JSON으로 쏴줌
        await self.send(text_data=json.dumps({
            'type': 'stock_update',
            'data': data
        }))