import redis
import json
import os
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Redis 채널 데이터를 Django Channels로 중계합니다.'

    def handle(self, *args, **options):
        redis_host = os.environ.get('REDIS_HOST', 'redis')
        # 주의: docker-compose의 redis 서비스명 확인
        r = redis.Redis(host=redis_host, port=6379, db=0)
        
        pubsub = r.pubsub()
        pubsub.subscribe('stock_updates') # 팀원 코드에서 publish한 채널명
        
        print("🌉 Bridge Started: Listening to 'stock_updates'...")
        channel_layer = get_channel_layer()

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    # 'stock_users' 그룹에게 전송
                    async_to_sync(channel_layer.group_send)(
                        "stock_users",
                        {
                            "type": "stock_message", # consumers.py의 메소드명
                            "message": data
                        }
                    )
                except Exception as e:
                    print(f"Bridge Error: {e}")