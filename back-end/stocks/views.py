import json
import os
import redis
from datetime import timedelta, datetime, date as date_type
from django.http import JsonResponse
from django.utils import timezone
from stocks.models import Stock, StockPrice

# 모델 임포트 (앱 이름에 맞게 확인 필요)
from .models import StockDailyReport


def _get_redis_client():
    # docker-compose 기준: redis 호스트명은 "redis"
    return redis.Redis(host="redis", port=6379, decode_responses=True)


def current_price(request, code: str):
    r = _get_redis_client()
    val = r.get(f"current_price:{code}")

    if val:
        # Redis에 데이터가 있으면 그대로 반환
        try:
            data = json.loads(val)
        except Exception:
            data = {"raw": val}

        return JsonResponse({
            "code": code,
            "price": data.get("price"),
            "change_rate": data.get("change_rate"),
            "volume": data.get("volume"),
            "timestamp": data.get("timestamp"),
        })
    
    # Redis에 데이터가 없으면 StockPrice 모델에서 마지막 데이터 조회
    try:
        stock = Stock.objects.get(stock_code=code)
        last_price = StockPrice.objects.filter(stock=stock).order_by('-time').first()
        
        if last_price:
            # 마지막 거래일의 전체 거래량 합계
            from django.db.models import Sum
            from django.db.models.functions import TruncDate
            
            last_date = last_price.time.date()
            daily_volume = StockPrice.objects.filter(
                stock=stock,
                time__date=last_date
            ).aggregate(total_volume=Sum('volume'))['total_volume'] or 0
            
            return JsonResponse({
                "code": code,
                "price": last_price.close or last_price.open,
                "change_rate": 0,  # 마지막 데이터이므로 변동률 0
                "volume": int(daily_volume),  # 해당일 전체 거래량
                "timestamp": last_price.time.isoformat(),
                "message": "Last cached price from database"
            })
    except Stock.DoesNotExist:
        pass
    except Exception as e:
        print(f"⚠️ StockPrice 조회 실패: {e}")
    
    # 데이터가 전혀 없으면 기본값 반환
    return JsonResponse(
        {"code": code, "price": None, "change_rate": 0, "volume": 0, "timestamp": None, "message": "No data available"}
    )


def _parse_range(range_str: str):
    """
    차트 범위 파라미터 → timedelta
    range: rt (실시간 1시간) | 1w (1주) | 1m (1달) | 3m (3달)
    """
    mapping = {
        "rt": timedelta(hours=1),  # 실시간: 1시간
        "1w": timedelta(days=7),   # 1주
        "1m": timedelta(days=30),  # 1달
        "3m": timedelta(days=90),  # 3달
    }
    return mapping.get(range_str, timedelta(hours=1))  # default 1시간


def chart(request, code: str):
    """
    GET /api/chart/{code}?range=rt|1w|1m
    - 실시간(rt): 1시간 전부터 1분 단위 캔들 (60개)
    - 1주(1w): 최근 7일, 하루를 오전/오후로 구분 (14개 캔들)
    - 1달(1m): 최근 30일, 1일 1개 캔들 (30개)
    """
    range_str = request.GET.get("range", "rt")
    delta = _parse_range(range_str)
    since = timezone.now() - delta

    candles = []
    labels = []

    if range_str == "rt":
        # 실시간: 1분 단위 캔들 (1시간 전부터, 60개)
        # StockPrice 모델에서 최근 1시간 데이터 조회
        try:
            stock = Stock.objects.get(stock_code=code)
        except Stock.DoesNotExist:
            return JsonResponse({"error": f"종목 {code}를 찾을 수 없습니다."}, status=404)
        
        # 최근 1시간의 1분 단위 데이터 조회
        prices = StockPrice.objects.filter(
            stock=stock,
            time__gte=since
        ).order_by('time')[:60]
        
        if prices.exists():
            # StockPrice에서 실제 데이터 사용
            for price in prices:
                candles.append({
                    'x': price.time.isoformat(),
                    'o': float(price.open) if price.open else None,
                    'h': float(price.high) if price.high else None,
                    'l': float(price.low) if price.low else None,
                    'c': float(price.close) if price.close else None,
                    'v': int(price.volume) if price.volume else 0,
                    'date': price.time.strftime('%Y-%m-%d'),
                })
                labels.append(price.time.strftime('%H:%M'))
        else:
            # 데이터가 없으면 마지막 거래 데이터로 고정
            last_price = StockPrice.objects.filter(stock=stock).order_by('-time').first()
            
            if last_price:
                # 마지막 거래일의 전체 거래량 합계
                from django.db.models import Sum
                last_date = last_price.time.date()
                daily_volume = StockPrice.objects.filter(
                    stock=stock,
                    time__date=last_date
                ).aggregate(total_volume=Sum('volume'))['total_volume'] or 0
                
                # 마지막 가격 사용
                base_price = float(last_price.close or last_price.open or 85000)
                
                # 1시간 전부터 현재까지 마지막 가격으로 고정
                now = timezone.now()
                for i in range(60):
                    minute_time = now - timedelta(minutes=60-i)
                    # 마지막 가격으로 고정 (변동 없음)
                    candles.append({
                        'x': minute_time.isoformat(),
                        'o': base_price,
                        'h': base_price,
                        'l': base_price,
                        'c': base_price,
                        'v': int(daily_volume // 60) if daily_volume > 0 else 0,  # 시간당 평균 거래량
                        'date': minute_time.strftime('%Y-%m-%d'),
                    })
                    labels.append(minute_time.strftime('%H:%M'))
            else:
                # 데이터가 전혀 없으면 Redis에서 현재가를 가져와서 더미 데이터 생성
                r = _get_redis_client()
                current_data = r.get(f"current_price:{code}")
                base_price = 85000  # 기본값
                if current_data:
                    try:
                        data = json.loads(current_data)
                        base_price = float(data.get("price", base_price))
                    except:
                        pass
                
                # 1시간 전부터 1분 단위로 60개 캔들 생성
                now = timezone.now()
                import random
                for i in range(60):
                    minute_time = now - timedelta(minutes=60-i)
                    # 간단한 변동 시뮬레이션
                    variation = random.uniform(-0.002, 0.002)  # ±0.2%
                    open_price = base_price * (1 + variation)
                    high_price = open_price * (1 + abs(random.uniform(0, 0.001)))
                    low_price = open_price * (1 - abs(random.uniform(0, 0.001)))
                    close_price = open_price * (1 + random.uniform(-0.001, 0.001))
                    volume = random.randint(1000, 10000)
                    
                    candles.append({
                        'x': minute_time.isoformat(),
                        'o': round(open_price, 0),
                        'h': round(high_price, 0),
                        'l': round(low_price, 0),
                        'c': round(close_price, 0),
                        'v': volume,
                        'date': minute_time.strftime('%Y-%m-%d'),
                    })
                    labels.append(minute_time.strftime('%H:%M'))
            
    elif range_str == "1w":
        # 1주: 최근 7일, 하루를 오전/오후로 구분 (14개 캔들)
        # StockPrice 모델에서 일봉 데이터를 기반으로 오전/오후로 분할
        try:
            stock = Stock.objects.get(stock_code=code)
        except Stock.DoesNotExist:
            return JsonResponse({"error": f"종목 {code}를 찾을 수 없습니다."}, status=404)
        
        # StockPrice에서 최근 7일 데이터 조회 (일봉 - 하루에 하나씩)
        # 날짜별로 그룹화하여 일봉 데이터 추출
        from django.db.models import Min, Max, Sum
        from django.db.models.functions import TruncDate
        
        daily_prices = StockPrice.objects.filter(
            stock=stock,
            time__gte=since
        ).annotate(
            date=TruncDate('time')
        ).values('date').annotate(
            open_price=Min('open'),
            high_price=Max('high'),
            low_price=Min('low'),
            close_price=Max('close'),
            volume=Sum('volume')
        ).order_by('date')[:7]
        
        rows = []
        for daily in daily_prices:
            rows.append((
                daily['date'],
                daily['open_price'],
                daily['high_price'],
                daily['low_price'],
                daily['close_price'],
                daily['volume']
            ))
        
        for row in rows:
            trade_date, open_price, high_price, low_price, close_price, volume = row
            if isinstance(trade_date, str):
                trade_date = datetime.strptime(trade_date, '%Y-%m-%d')
            if isinstance(trade_date, date_type):
                trade_date = datetime.combine(trade_date, datetime.min.time())
            if timezone.is_naive(trade_date):
                trade_date = timezone.make_aware(trade_date)
            
            date_str = trade_date.strftime('%Y-%m-%d')
            
            # 오전 캔들 (09:00 기준)
            am_time = trade_date.replace(hour=9, minute=0)
            mid_price = (float(open_price) + float(close_price)) / 2
            candles.append({
                'x': am_time.isoformat(),
                'o': float(open_price) if open_price else None,
                'h': mid_price,
                'l': float(low_price) if low_price else None,
                'c': mid_price,
                'v': int(volume) // 2 if volume else 0,
                'date': date_str,
            })
            labels.append(f"{date_str} AM")
            
            # 오후 캔들 (12:00 기준)
            pm_time = trade_date.replace(hour=12, minute=0)
            candles.append({
                'x': pm_time.isoformat(),
                'o': mid_price,
                'h': float(high_price) if high_price else None,
                'l': mid_price,
                'c': float(close_price) if close_price else None,
                'v': int(volume) // 2 if volume else 0,
                'date': date_str,
            })
            labels.append(f"{date_str} PM")
            
    elif range_str == "1m":
        # 1달: 1일 1개 캔들 (30개)
        try:
            stock = Stock.objects.get(stock_code=code)
        except Stock.DoesNotExist:
            return JsonResponse({"error": f"종목 {code}를 찾을 수 없습니다."}, status=404)
        
        # StockPrice에서 최근 30일 데이터 조회 (일봉 - 날짜별 그룹화)
        from django.db.models import Min, Max, Sum
        from django.db.models.functions import TruncDate
        
        daily_prices = StockPrice.objects.filter(
            stock=stock,
            time__gte=since
        ).annotate(
            date=TruncDate('time')
        ).values('date').annotate(
            open_price=Min('open'),
            high_price=Max('high'),
            low_price=Min('low'),
            close_price=Max('close'),
            volume=Sum('volume')
        ).order_by('date')[:30]
        
        rows = []
        for daily in daily_prices:
            rows.append((
                daily['date'],
                daily['open_price'],
                daily['high_price'],
                daily['low_price'],
                daily['close_price'],
                daily['volume']
            ))
        
        for row in rows:
            trade_date, open_price, high_price, low_price, close_price, volume = row
            if isinstance(trade_date, str):
                trade_date = datetime.strptime(trade_date, '%Y-%m-%d')
            if isinstance(trade_date, date_type):
                trade_date = datetime.combine(trade_date, datetime.min.time())
            if timezone.is_naive(trade_date):
                trade_date = timezone.make_aware(trade_date)
            
            date_str = trade_date.strftime('%Y-%m-%d')
            candles.append({
                'x': trade_date.isoformat(),
                'o': float(open_price) if open_price else None,
                'h': float(high_price) if high_price else None,
                'l': float(low_price) if low_price else None,
                'c': float(close_price) if close_price else None,
                'v': int(volume) if volume else 0,
                'date': date_str,
            })
            labels.append(date_str)
            
    elif range_str == "3m":
        # 3달: 1일 1개 캔들 (90개)
        try:
            stock = Stock.objects.get(stock_code=code)
        except Stock.DoesNotExist:
            return JsonResponse({"error": f"종목 {code}를 찾을 수 없습니다."}, status=404)
        
        # StockPrice에서 최근 90일 데이터 조회 (일봉 - 날짜별 그룹화)
        from django.db.models import Min, Max, Sum
        from django.db.models.functions import TruncDate
        
        daily_prices = StockPrice.objects.filter(
            stock=stock,
            time__gte=since
        ).annotate(
            date=TruncDate('time')
        ).values('date').annotate(
            open_price=Min('open'),
            high_price=Max('high'),
            low_price=Min('low'),
            close_price=Max('close'),
            volume=Sum('volume')
        ).order_by('date')[:90]
        
        rows = []
        for daily in daily_prices:
            rows.append((
                daily['date'],
                daily['open_price'],
                daily['high_price'],
                daily['low_price'],
                daily['close_price'],
                daily['volume']
            ))
        
        for row in rows:
            trade_date, open_price, high_price, low_price, close_price, volume = row
            if isinstance(trade_date, str):
                trade_date = datetime.strptime(trade_date, '%Y-%m-%d')
            if isinstance(trade_date, date_type):
                trade_date = datetime.combine(trade_date, datetime.min.time())
            if timezone.is_naive(trade_date):
                trade_date = timezone.make_aware(trade_date)
            
            date_str = trade_date.strftime('%Y-%m-%d')
            candles.append({
                'x': trade_date.isoformat(),
                'o': float(open_price) if open_price else None,
                'h': float(high_price) if high_price else None,
                'l': float(low_price) if low_price else None,
                'c': float(close_price) if close_price else None,
                'v': int(volume) if volume else 0,
                'date': date_str,
            })
            labels.append(date_str)

    # StockDailyReport 데이터 조회 (전날 분석 리포트용)
    ai_reports = {}
    try:
        stock = Stock.objects.get(stock_code=code)
        reports = StockDailyReport.objects.filter(stock=stock).order_by('-target_date')[:30]
        for report in reports:
            date_str = report.target_date.strftime('%Y-%m-%d')
            ai_reports[date_str] = {
                'summary': report.ai_summary,
                'sentiment': report.sentiment_avg,
                'date': date_str,
            }
    except Stock.DoesNotExist:
        pass
    except Exception as e:
        print(f"⚠️ StockDailyReport 조회 실패: {e}")

    return JsonResponse({
        "code": code,
        "range": range_str,
        "labels": labels,
        "candles": candles,
        "sentiment": [],
        "flow": [],
        "ai_reports": ai_reports,  # 전날 분석 리포트 데이터 추가
    })
