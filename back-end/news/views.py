# import math
# import requests
# from django.conf import settings
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# def es_search(index: str, body: dict):
#     url = f"{settings.ES_BASE_URL}/{index}/_search"
#     r = requests.get(url, json=body, timeout=10)
#     r.raise_for_status()
#     return r.json()

# class NewsListAPIView(APIView):
#     """
#     GET /api/news?q=&page=1&size=20&from=YYYY-MM-DD&to=YYYY-MM-DD&source=
#     - q 없으면 최신순
#     - q 있으면 title/content 검색
#     """

#     def get(self, request):
#         q = (request.query_params.get("q") or "").strip()
#         size = int(request.query_params.get("size", 20))
#         page = int(request.query_params.get("page", 1))
#         date_from = request.query_params.get("from")
#         date_to = request.query_params.get("to")
#         source = (request.query_params.get("source") or "").strip()

#         must = []
#         filt = []

#         if q:
#             must.append({
#                 "multi_match": {
#                     "query": q,
#                     "fields": ["title^3", "content"],
#                     "type": "best_fields"
#                 }
#             })
#         else:
#             must.append({"match_all": {}})

#         if source:
#             filt.append({"term": {"source": source}})

#         if date_from or date_to:
#             r = {"range": {"published_at": {}}}
#             if date_from:
#                 r["range"]["published_at"]["gte"] = date_from
#             if date_to:
#                 r["range"]["published_at"]["lte"] = date_to
#             filt.append(r)

#         body = {
#             "from": (page - 1) * size,
#             "size": size,
#             "sort": [{"published_at": {"order": "desc"}}],
#             "_source": ["source", "title", "link", "published_at", "content"],
#             "query": {"bool": {"must": must, "filter": filt}},
#         }

#         try:
#             data = es_search(settings.NEWS_INDEX, body)
#         except requests.HTTPError as e:
#             return Response(
#                 {"error": "Elasticsearch query failed", "detail": str(e)},
#                 status=status.HTTP_502_BAD_GATEWAY
#             )

#         hits = data["hits"]["hits"]
#         total = data["hits"]["total"]["value"]

#         items = []
#         for h in hits:
#             src = h.get("_source", {})
#             items.append({
#                 "id": h.get("_id"),
#                 "source": src.get("source", ""),
#                 "title": src.get("title", ""),
#                 "link": src.get("link", ""),
#                 "published_at": src.get("published_at", ""),
#                 "content": src.get("content", ""),
#             })

#         return Response({
#             "items": items,
#             "page": page,
#             "size": size,
#             "total": total,
#             "total_pages": math.ceil(total / size) if size else 1
#         })

import math
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import News, NewsStockMapping # DB 연동을 위해 추가

def es_search(index: str, body: dict):
    url = f"{settings.ES_BASE_URL}/{index}/_search"
    # [수정] GET -> POST: 500 에러 방지를 위한 표준 변경
    r = requests.post(url, json=body, timeout=10)
    r.raise_for_status()
    return r.json()

class NewsListAPIView(APIView):
    def get(self, request):
        ticker = request.query_params.get("ticker")
        q = (request.query_params.get("q") or "").strip()
        size = int(request.query_params.get("size", 20))
        page = int(request.query_params.get("page", 1))

        # 1. Ticker 기반 DB 조회 (AiInsight 영역)
        if ticker:
            try:
                mappings = NewsStockMapping.objects.filter(
                    stock__stock_code=ticker 
                ).select_related('news').order_by('-news__published_at')[(page-1)*size : page*size]
                
                items = []
                for m in mappings:
                    items.append({
                        "id": str(m.news.id),
                        "title": m.news.title,
                        "content_summary": m.news.content_summary,
                        "sentiment_score": m.news.sentiment_score,
                        "published_at": m.news.published_at.isoformat() if m.news.published_at else "",
                        "link": m.news.original_url,
                    })
                
                # ✅ 필터링 결과 반환
                return Response({
                    "items": items,
                    "page": page,
                    "size": size,
                    "total": len(items)
                })
            except Exception as e:
                print(f"❌ DB News Error: {e}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. 검색어 기반 Elasticsearch 조회 (NewsFeed 영역)
        must = [{"multi_match": {"query": q, "fields": ["title^3", "content"]}}] if q else [{"match_all": {}}]
        
        body = {
            "from": (page - 1) * size,
            "size": size,
            "sort": [{"published_at": {"order": "desc"}}],
            "query": {"bool": {"must": must}},
        }

        try:
            data = es_search(settings.NEWS_INDEX, body)
            hits = data.get("hits", {}).get("hits", [])
            total = data.get("hits", {}).get("total", {}).get("value", 0)

            items = []
            for h in hits:
                src = h.get("_source", {})
                items.append({
                    "id": h.get("_id"),
                    "title": src.get("title", ""),
                    "link": src.get("link", ""),
                    "published_at": src.get("published_at", ""),
                    "content": src.get("content", ""),
                })

            # ✅ 검색 결과 반환
            return Response({
                "items": items,
                "page": page,
                "size": size,
                "total": total,
                "total_pages": math.ceil(total / size) if size else 1
            })
            
        except Exception as e:
            print(f"❌ ES Search Error: {e}")
            # ✅ 에러 상황에서도 반드시 Response를 반환해야 합니다.
            return Response({"error": f"Elasticsearch Error: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)