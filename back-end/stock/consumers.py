# 앱폴더/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StockConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. 그룹 이름 정의
        self.group_name = 'stock_group'

        # 2. 그룹(방)에 입장 (Redis나 In-Memory Layer 사용)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # 3. 연결 수락
        await self.accept()

    async def disconnect(self, close_code):
        # 연결 끊기면 그룹 퇴장
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # 4. Kafka Consumer에서 보낸 메시지를 받아서 브라우저로 전달하는 핸들러
    async def stock_update(self, event):
        message = event['message']

        # 브라우저(HTML)로 JSON 전송
        await self.send(text_data=json.dumps({
            'message': message
        }))