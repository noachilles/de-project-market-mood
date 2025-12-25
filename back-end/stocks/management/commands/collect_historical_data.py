"""
FinanceDataReader를 사용하여 삼성전자(005930)의 최근 3개월치 일봉 데이터를 수집하고
StockPrice 모델에 저장하는 Django Management Command
"""
try:
    import FinanceDataReader as fdr
except ImportError:
    raise ImportError(
        "FinanceDataReader 패키지를 설치해주세요:\n"
        "  docker-compose exec backend pip install FinanceDataReader\n"
        "또는 requirements.txt에 FinanceDataReader가 포함되어 있는지 확인하세요."
    )
import pandas as pd
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import Stock, StockPrice
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'FinanceDataReader를 사용하여 삼성전자(005930)의 최근 3개월치 일봉 데이터를 수집하고 StockPrice 모델에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stock-code',
            type=str,
            default='005930',
            help='수집할 종목 코드 (기본값: 005930 - 삼성전자)',
        )
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='수집할 기간(개월) (기본값: 3개월)',
        )

    def handle(self, *args, **options):
        stock_code = options['stock_code']
        months = options['months']
        
        self.stdout.write(self.style.NOTICE(f'[{stock_code}] 종목의 최근 {months}개월치 일봉 데이터 수집을 시작합니다...'))
        
        try:
            # 1. 종목이 DB에 존재하는지 확인, 없으면 생성
            stock, created = Stock.objects.get_or_create(
                stock_code=stock_code,
                defaults={
                    'stock_name': '삼성전자' if stock_code == '005930' else f'종목_{stock_code}',
                    'market_type': 'KOSPI'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'종목 정보를 생성했습니다: {stock.stock_name}({stock.stock_code})'))
            
            # 2. FinanceDataReader로 데이터 수집 (3개월치)
            # FinanceDataReader는 timezone-naive datetime을 기대하므로 naive datetime 사용
            end_date = datetime.now()  # timezone-naive
            start_date = end_date - timedelta(days=30 * months)  # 개월 수에 따라 일수 계산
            
            self.stdout.write(self.style.NOTICE(f'데이터 수집 기간: {start_date.strftime("%Y-%m-%d")} ~ {end_date.strftime("%Y-%m-%d")}'))
            self.stdout.write(self.style.NOTICE(f'📊 저장 위치: StockPrice 모델 (stocks_stockprice 테이블)'))
            
            # FinanceDataReader로 일봉 데이터 수집 (timezone-naive datetime 전달)
            df = fdr.DataReader(stock_code, start_date, end_date)
            
            if df.empty:
                self.stdout.write(self.style.ERROR('수집된 데이터가 없습니다.'))
                return
            
            # 4. 데이터 검증 (volume 포함 확인)
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.stdout.write(self.style.ERROR(f'필수 컬럼이 누락되었습니다: {missing_columns}'))
                return
            
            # 5. 데이터 저장 (StockPrice 모델 사용)
            saved_count = 0
            skipped_count = 0
            error_count = 0
            
            for date, row in df.iterrows():
                try:
                    # 날짜를 datetime으로 변환 (인덱스가 날짜인 경우)
                    if isinstance(date, str):
                        trade_date = datetime.strptime(date, '%Y-%m-%d')
                    else:
                        trade_date = date.to_pydatetime() if hasattr(date, 'to_pydatetime') else date
                    
                    # timezone aware로 변환
                    if timezone.is_naive(trade_date):
                        trade_date = timezone.make_aware(trade_date)
                    
                    # 데이터 추출 (volume 포함)
                    open_price = float(row['Open']) if pd.notna(row['Open']) else None
                    high_price = float(row['High']) if pd.notna(row['High']) else None
                    low_price = float(row['Low']) if pd.notna(row['Low']) else None
                    close_price = float(row['Close']) if pd.notna(row['Close']) else None
                    volume = int(row['Volume']) if pd.notna(row['Volume']) else None
                    
                    # volume 데이터 누락 체크
                    if volume is None:
                        self.stdout.write(self.style.WARNING(f'⚠️  {trade_date.strftime("%Y-%m-%d")}의 volume 데이터가 누락되었습니다.'))
                    
                    # StockPrice 모델에 저장 (update_or_create로 UPSERT)
                    StockPrice.objects.update_or_create(
                        stock=stock,
                        time=trade_date,
                        defaults={
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume,
                        }
                    )
                    saved_count += 1
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'❌ {date} 데이터 저장 실패: {str(e)}'))
                    logger.error(f'Error saving data for {date}: {str(e)}', exc_info=True)
            
            # 6. 결과 출력
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ 데이터 수집 완료!\n'
                f'   - 저장된 레코드: {saved_count}개\n'
                f'   - 건너뛴 레코드: {skipped_count}개\n'
                f'   - 오류 발생: {error_count}개\n'
                f'   - 총 수집 데이터: {len(df)}개'
            ))
            
            # 7. 저장된 데이터 검증 (StockPrice 모델 사용)
            prices = StockPrice.objects.filter(stock=stock).order_by('time')
            if prices.exists():
                stats = {
                    'count': prices.count(),
                    'min_date': prices.first().time,
                    'max_date': prices.last().time,
                    'missing_volume': prices.filter(volume__isnull=True).count(),
                }
                self.stdout.write(self.style.SUCCESS(
                    f'\n📊 저장된 데이터 통계:\n'
                    f'   - 총 레코드 수: {stats["count"]}개\n'
                    f'   - 최초 날짜: {stats["min_date"]}\n'
                    f'   - 최신 날짜: {stats["max_date"]}\n'
                    f'   - Volume 누락: {stats["missing_volume"]}개'
                ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 데이터 수집 중 오류 발생: {str(e)}'))
            logger.error(f'Error in collect_historical_data: {str(e)}', exc_info=True)
            raise

