import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StockConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Vue가 연결되면 'stock_users' 그룹에 가입
        self.group_name = "stock_users"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"✅ [WebSocket] Client Connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Bridge가 보내준 데이터를 받아서 Vue에게 전달
    async def stock_message(self, event):
        # event['message']에 실시간 주식 데이터가 들어있음
        await self.send(text_data=json.dumps({
            'type': 'stock_update',
            'data': event['message']
        }))