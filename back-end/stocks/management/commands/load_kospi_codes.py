import csv
import os
from django.core.management.base import BaseCommand
from stocks.models import Stock

class Command(BaseCommand):
    help = 'kospi_code.csv 파일로부터 종목 코드와 이름을 DB에 로드합니다.'

    def handle(self, *args, **options):
        # 파일 경로 설정 (backend/stocks/kospi_code.csv 위치 기준)
        # 이 스크립트는 backend 폴더에서 실행되므로 아래 경로가 적절합니다.
        csv_path = os.path.join(os.getcwd(), 'stocks', 'kospi_code.csv')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_path}'))
            return

        self.stdout.write(self.style.NOTICE('데이터 로드를 시작합니다...'))

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            # CSV 파일의 첫 줄이 '단축코드', '한글명'인 경우
            reader = csv.DictReader(f)
            
            count = 0
            for row in reader:
                code = row['단축코드']
                name = row['한글명']

                # 모델 필드명에 맞춰 저장 (stock_code, stock_name)
                # update_or_create를 쓰면 이름이 바뀌었을 때 업데이트도 해줍니다.
                stock, created = Stock.objects.update_or_create(
                    stock_code=code,
                    defaults={'stock_name': name}
                )
                if created:
                    count += 1
            
        self.stdout.write(self.style.SUCCESS(f'성공적으로 {count}개의 새로운 종목을 로드했습니다!'))