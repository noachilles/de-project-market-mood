"""
historical_prices 테이블의 날짜를 기반으로 더미 뉴스 데이터를 생성하여
Elasticsearch에 인덱싱하고 StockDailyReport를 생성하는 Django Management Command
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta, date as date_type
from stocks.models import Stock, StockDailyReport
import os
import json
import random

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None


class Command(BaseCommand):
    help = 'historical_prices 테이블의 날짜를 기반으로 더미 뉴스 데이터를 Elasticsearch에 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stock-code',
            type=str,
            default='005930',
            help='종목 코드 (기본값: 005930 - 삼성전자)',
        )
        parser.add_argument(
            '--news-per-day',
            type=int,
            default=2,
            help='하루당 생성할 뉴스 개수 (기본값: 2)',
        )

    def handle(self, *args, **options):
        stock_code = options['stock_code']
        news_per_day = options['news_per_day']
        
        if not Elasticsearch:
            self.stdout.write(self.style.ERROR('❌ elasticsearch 패키지가 설치되지 않았습니다.'))
            self.stdout.write(self.style.WARNING('   pip install elasticsearch 실행 후 다시 시도하세요.'))
            return
        
        # 종목명 매핑
        stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
        }
        stock_name = stock_names.get(stock_code, f'종목_{stock_code}')
        
        self.stdout.write(self.style.NOTICE(f'[{stock_code}] {stock_name}의 더미 뉴스 데이터 생성을 시작합니다...'))
        
        try:
            # 1. StockPrice 모델에서 최근 3개월치 날짜만 조회
            from stocks.models import Stock, StockPrice
            
            try:
                stock = Stock.objects.get(stock_code=stock_code)
            except Stock.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ 종목 {stock_code}를 찾을 수 없습니다.'))
                return
            
            three_months_ago = timezone.now() - timedelta(days=90)
            prices = StockPrice.objects.filter(
                stock=stock,
                time__gte=three_months_ago
            ).order_by('time').values_list('time', flat=True).distinct()
            
            # 날짜만 추출 (중복 제거)
            dates = list(set([p.date() for p in prices]))
            dates.sort()
            
            rows = [(date,) for date in dates]
            
            if not rows:
                self.stdout.write(self.style.ERROR('❌ historical_prices 테이블에 데이터가 없습니다.'))
                self.stdout.write(self.style.WARNING('   먼저 collect_historical_data 명령어를 실행하세요.'))
                return
            
            dates = [row[0] for row in rows]
            self.stdout.write(self.style.SUCCESS(f'✅ {len(dates)}일치 데이터를 찾았습니다.'))
            
            # 2. Elasticsearch 클라이언트 연결
            es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
            es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
            es_index = os.getenv("ELASTICSEARCH_NEWS_INDEX", "news")
            
            try:
                es = Elasticsearch([f"http://{es_host}:{es_port}"])
                # 연결 테스트
                if not es.ping():
                    raise Exception("Elasticsearch 연결 실패")
                
                # Read-only 모드 해제 (디스크 공간 부족 시)
                try:
                    es.indices.put_settings(
                        index=es_index,
                        body={
                            "index.blocks.read_only_allow_delete": None
                        }
                    )
                    self.stdout.write(self.style.SUCCESS('✅ Elasticsearch read-only 모드 해제'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  Read-only 모드 해제 실패 (계속 진행): {e}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Elasticsearch 연결 실패: {e}'))
                self.stdout.write(self.style.WARNING(f'   호스트: {es_host}:{es_port}'))
                return
            
            # 3. 인덱스 존재 확인 및 생성
            if not es.indices.exists(index=es_index):
                self.stdout.write(self.style.NOTICE(f'인덱스 {es_index}가 없습니다. 생성합니다...'))
                # 간단한 매핑으로 인덱스 생성
                es.indices.create(index=es_index, body={
                    "mappings": {
                        "properties": {
                            "news_id": {"type": "keyword"},
                            "title": {"type": "text"},
                            "content_summary": {"type": "text"},
                            "stock_codes": {"type": "keyword"},
                            "published_at": {"type": "date"},
                            "sentiment_score": {"type": "float"},
                        }
                    }
                })
                self.stdout.write(self.style.SUCCESS(f'✅ 인덱스 {es_index} 생성 완료'))
            
            # 4. StockDailyReport용 AI 요약 템플릿 (두 줄 요약)
            ai_summary_templates = [
                "{stock_name}은(는) 반도체 업황 개선과 신제품 출시로 주가 상승세를 이어가고 있다. 투자자들은 하반기 실적 개선을 기대하며 매수세가 지속되고 있다.",
                "{stock_name}의 글로벌 시장 진출 확대와 기술 혁신으로 경쟁력이 강화되고 있다. 증권가에서는 목표가 상향 조정과 함께 긍정적 전망을 내놓고 있다.",
                "{stock_name} 주가는 변동성을 보이며 조정 국면에 접어들었다. 그러나 장기 투자 관점에서 매수 기회로 평가하는 목소리가 나오고 있다.",
                "{stock_name}의 ESG 경영 강화와 배당 정책 변경으로 주주 만족도가 상승하고 있다. 기관투자자들의 관심이 높아지며 기업 가치가 제고되고 있다.",
                "{stock_name}은(는) AI 관련 사업 확대로 새로운 성장 동력을 확보했다. 글로벌 경기 회복세에 따른 수출 증가로 실적 개선이 예상된다.",
            ]
            
            # 5. 개별 뉴스 기사 템플릿
            news_templates = [
                "{stock_name} 주가 상승세 지속, 투자자들 관심 집중",
                "{stock_name} 실적 발표 앞두고 기대감 높아져",
                "{stock_name} 신제품 출시로 시장 반응 긍정적",
                "{stock_name} 글로벌 시장 진출 확대 계획 발표",
                "{stock_name} 기술 혁신으로 경쟁력 강화",
                "{stock_name} 주가 변동성 증가, 투자 주의 필요",
                "{stock_name} 실적 전망 긍정적, 목표가 상향 조정",
                "{stock_name} 배당 정책 변경으로 주주 만족도 상승",
                "{stock_name} M&A 관련 소식에 시장 관심 집중",
                "{stock_name} ESG 경영 강화로 기업 가치 제고",
                "{stock_name} 반도체 업황 개선에 따른 수혜 기대",
                "{stock_name} AI 관련 사업 확대로 성장 동력 확보",
                "{stock_name} 글로벌 경기 회복세에 따른 수출 증가",
                "{stock_name} 신규 사업 진출로 다각화 전략 추진",
                "{stock_name} 주가 조정 국면, 매수 기회로 평가",
            ]
            
            # 6. Stock 객체 가져오기
            try:
                stock = Stock.objects.get(stock_code=stock_code)
            except Stock.DoesNotExist:
                stock = Stock.objects.create(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    market_type='KOSPI'
                )
                self.stdout.write(self.style.SUCCESS(f'✅ 종목 정보 생성: {stock_name}({stock_code})'))
            
            # 7. 각 날짜별로 StockDailyReport 생성 및 더미 뉴스 생성
            created_count = 0
            skipped_count = 0
            report_count = 0
            
            for date in dates:
                # 날짜를 datetime으로 변환
                if isinstance(date, str):
                    trade_date = datetime.strptime(date, '%Y-%m-%d')
                elif isinstance(date, datetime):
                    trade_date = date
                elif isinstance(date, date_type):
                    # datetime.date 객체인 경우 datetime.datetime으로 변환
                    trade_date = datetime.combine(date, datetime.min.time())
                else:
                    # 기타 경우 문자열로 변환 후 파싱
                    try:
                        trade_date = datetime.fromisoformat(str(date))
                    except:
                        trade_date = datetime.strptime(str(date), '%Y-%m-%d')
                
                # timezone aware로 변환
                if timezone.is_naive(trade_date):
                    trade_date = timezone.make_aware(trade_date)
                
                # 날짜 문자열 생성 (YYYYMMDD)
                if isinstance(date, date_type):
                    date_str = date.strftime('%Y%m%d')
                    target_date = date
                elif isinstance(date, datetime):
                    date_str = date.strftime('%Y%m%d')
                    target_date = date.date()
                else:
                    date_str = str(date).replace('-', '')[:8]  # YYYY-MM-DD -> YYYYMMDD
                    target_date = datetime.strptime(date_str, '%Y%m%d').date()
                
                # StockDailyReport 생성 (해당 날짜의 전체 기사 종합 요약)
                ai_summary = random.choice(ai_summary_templates).format(stock_name=stock_name)
                sentiment_avg = round(random.uniform(-0.3, 0.8), 2)  # 평균 감성 점수
                
                daily_report, report_created = StockDailyReport.objects.get_or_create(
                    stock=stock,
                    target_date=target_date,
                    defaults={
                        'ai_summary': ai_summary,
                        'sentiment_avg': sentiment_avg,
                    }
                )
                
                if report_created:
                    report_count += 1
                
                # 하루당 여러 개의 뉴스 생성 (sentiment_avg를 중심으로 분산)
                sentiment_scores = []
                for i in range(news_per_day):
                    # 랜덤 시간 생성 (09:00 ~ 18:00)
                    hour = random.randint(9, 18)
                    minute = random.randint(0, 59)
                    published_at = trade_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # 랜덤 뉴스 템플릿 선택
                    template = random.choice(news_templates)
                    title = template.format(stock_name=stock_name)
                    
                    # StockDailyReport의 sentiment_avg를 중심으로 분산된 감정 점수 생성
                    # 평균 주변 ±0.3 범위로 분산
                    sentiment_score = round(random.uniform(
                        max(-1.0, sentiment_avg - 0.3),
                        min(1.0, sentiment_avg + 0.3)
                    ), 2)
                    sentiment_scores.append(sentiment_score)
                    
                    # 뉴스 ID 생성 (날짜 + 인덱스)
                    news_id = f"{stock_code}_{date_str}_{i}"
                    
                    # 날짜 문자열 생성 (YYYY-MM-DD)
                    date_str_iso = trade_date.strftime('%Y-%m-%d')
                    
                    # original_url 생성 (더미 URL)
                    original_url = f"https://news.example.com/{stock_code}/{date_str_iso}/{news_id}"
                    
                    # Elasticsearch 문서 생성 (StockDailyReport의 ai_summary 참고)
                    doc = {
                        "news_id": news_id,
                        "title": title,
                        "content_summary": f"{ai_summary} {title}",
                        "stock_codes": [stock_code],
                        "published_at": published_at.isoformat(),
                        "sentiment_score": sentiment_score,
                        "original_url": original_url,  # 뉴스 원본 링크
                    }
                    
                    try:
                        # 인덱싱 (ID로 중복 방지)
                        es.index(
                            index=es_index,
                            id=news_id,
                            document=doc,
                            request_timeout=30  # 타임아웃 증가
                        )
                        created_count += 1
                        
                        # 배치 처리: 10개마다 진행 상황 출력
                        if created_count % 10 == 0:
                            self.stdout.write(self.style.NOTICE(f'진행 중... {created_count}개 생성됨'))
                            
                    except Exception as e:
                        skipped_count += 1
                        error_msg = str(e)
                        # Read-only 오류인 경우 특별 처리
                        if 'read-only' in error_msg.lower() or 'TOO_MANY_REQUESTS' in error_msg:
                            self.stdout.write(self.style.WARNING(
                                f'⚠️  Elasticsearch 디스크 공간 부족. 기존 인덱스 삭제 후 재시도하세요:\n'
                                f'   docker-compose exec elasticsearch curl -X DELETE "http://localhost:9200/{es_index}"'
                            ))
                            break  # 더 이상 진행하지 않음
                        elif skipped_count <= 5:  # 처음 5개만 출력
                            self.stdout.write(self.style.WARNING(f'⚠️  {date} 뉴스 생성 실패: {error_msg[:100]}'))
            
            # 8. 결과 출력
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ 더미 뉴스 데이터 생성 완료!\n'
                f'   - 생성된 StockDailyReport: {report_count}개\n'
                f'   - 생성된 뉴스: {created_count}개\n'
                f'   - 건너뛴 뉴스: {skipped_count}개\n'
                f'   - 대상 날짜: {len(dates)}일\n'
                f'   - 인덱스: {es_index}'
            ))
            
            # 7. 검증 쿼리
            try:
                response = es.count(index=es_index, body={
                    "query": {
                        "term": {
                            "stock_codes": stock_code
                        }
                    }
                })
                total_count = response.get("count", 0)
                self.stdout.write(self.style.SUCCESS(f'📊 Elasticsearch에 저장된 총 뉴스 수: {total_count}개'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  검증 쿼리 실패: {str(e)}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 더미 뉴스 생성 중 오류 발생: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

