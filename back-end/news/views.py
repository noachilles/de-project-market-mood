from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import os
from elasticsearch import Elasticsearch
import json

# Elasticsearch 클라이언트 설정
ES_HOST = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
ES_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ES_INDEX = os.getenv("ELASTICSEARCH_NEWS_INDEX", "news")

def _get_elasticsearch_client():
    """Elasticsearch 클라이언트 반환"""
    try:
        return Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    except Exception as e:
        print(f"Elasticsearch 연결 실패: {e}")
        return None


@require_http_methods(["GET"])
def news_list(request):
    """
    GET /api/news/?ticker=005930&size=5
    - 최근 뉴스 목록 조회 (NewsFeed용)
    """
    ticker = request.GET.get("ticker", "")
    size = int(request.GET.get("size", 5))
    
    if not ticker:
        return JsonResponse({
            "error": "ticker 파라미터가 필요합니다."
        }, status=400)
    
    es = _get_elasticsearch_client()
    if not es:
        return JsonResponse({
            "items": [],
            "message": "Elasticsearch 연결 실패"
        })
    
    # Elasticsearch 쿼리: 최근 뉴스 조회
    query = {
        "bool": {
            "must": [
                {
                    "term": {
                        "stock_codes": ticker
                    }
                }
            ]
        }
    }
    
    try:
        response = es.search(
            index=ES_INDEX,
            body={
                "query": query,
                "size": size,
                "sort": [
                    {"published_at": {"order": "desc"}}
                ],
                "_source": ["title", "published_at", "sentiment_score"]
            }
        )
        
        items = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            items.append({
                "title": source.get("title", ""),
                "published_at": source.get("published_at", ""),
                "sentiment_score": source.get("sentiment_score", 0.0),
                "original_url": source.get("original_url", ""),
            })
        
        return JsonResponse({
            "ticker": ticker,
            "items": items,
            "count": len(items)
        })
        
    except Exception as e:
        return JsonResponse({
            "items": [],
            "error": str(e)
        }, status=500)


@require_http_methods(["GET"])
def news_by_date(request):
    """
    GET /api/news/by-date/?ticker=005930&date=2024-12-25
    - 특정 날짜의 뉴스 조회 (캔들 차트 호버용)
    """
    ticker = request.GET.get("ticker", "")
    date_str = request.GET.get("date", "")
    
    if not ticker or not date_str:
        return JsonResponse({
            "error": "ticker와 date 파라미터가 필요합니다."
        }, status=400)
    
    try:
        # 날짜 파싱
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        es = _get_elasticsearch_client()
        if not es:
            return JsonResponse({
                "items": [],
                "message": "Elasticsearch 연결 실패"
            })
        
        # Elasticsearch 쿼리: 해당 날짜의 뉴스 조회
        query = {
            "bool": {
                "must": [
                    {
                        "term": {
                            "stock_codes": ticker
                        }
                    },
                    {
                        "range": {
                            "published_at": {
                                "gte": date_start.isoformat(),
                                "lt": date_end.isoformat()
                            }
                        }
                    }
                ]
            }
        }
        
        try:
            response = es.search(
                index=ES_INDEX,
                body={
                    "query": query,
                    "size": 5,  # 최대 5개 뉴스
                    "sort": [
                        {"published_at": {"order": "desc"}}
                    ],
                    "_source": ["title", "published_at", "sentiment_score"]
                }
            )
            
            items = []
            for hit in response.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                items.append({
                    "title": source.get("title", ""),
                    "published_at": source.get("published_at", ""),
                    "sentiment_score": source.get("sentiment_score", 0.0),
                })
            
            return JsonResponse({
                "ticker": ticker,
                "date": date_str,
                "items": items,
                "count": len(items)
            })
            
        except Exception as e:
            return JsonResponse({
                "items": [],
                "error": str(e)
            }, status=500)
            
    except ValueError:
        return JsonResponse({
            "error": "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요."
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)
