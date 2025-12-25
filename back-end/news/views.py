from rest_framework.decorators import api_view # ✅ @require_http_methods 대신 사용
from rest_framework.response import Response
from datetime import datetime, timedelta
import os
from elasticsearch import Elasticsearch
import json
from core.utils.openai_client import get_openai_client

# ✅ Swagger 임포트
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from rest_framework import serializers

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
ES_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ES_INDEX = os.getenv("ELASTICSEARCH_NEWS_INDEX", "news")

def _get_elasticsearch_client():
    try:
        return Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    except Exception as e:
        print(f"Elasticsearch 연결 실패: {e}")
        return None


@extend_schema(
    summary="뉴스 목록 조회",
    description="특정 종목(ticker)과 관련된 최신 뉴스를 가져옵니다.",
    parameters=[
        OpenApiParameter(name='ticker', description='종목 코드 (예: 005930)', required=True, type=str),
        OpenApiParameter(name='size', description='가져올 뉴스 개수 (기본: 5)', required=False, type=int),
    ],
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['GET']) # ✅ DRF 뷰로 변환
def news_list(request):
    ticker = request.GET.get("ticker", "")
    size = int(request.GET.get("size", 5))
    
    if not ticker:
        return Response({"error": "ticker 파라미터가 필요합니다."}, status=400)
    
    stock_name_map = {
        "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER",
        "035720": "카카오", "005380": "현대차", "051910": "LG화학",
    }
    stock_name = stock_name_map.get(ticker, "")
    
    es = _get_elasticsearch_client()
    if not es:
        return Response({"items": [], "message": "Elasticsearch 연결 실패"})
    
    # Elasticsearch 쿼리: 타이틀에 종목명이 포함된 뉴스 검색
    # stock_codes로 필터링하거나 타이틀에 종목명이 포함된 뉴스 검색
    should_clauses = []
    
    # 1. stock_codes로 필터링 (기존 방식)
    should_clauses.append({
        "term": {
            "stock_codes": ticker
        }
    })
    
    # 2. 타이틀에 종목명이 포함된 뉴스 검색
    if stock_name:
        should_clauses.append({
            "match": {
                "title": stock_name
            }
        })
    
    query = {
        "bool": {
            "should": should_clauses,
            "minimum_should_match": 1,  # 최소 하나의 조건은 만족해야 함
            "must_not": [
                # 더미 URL 패턴 제외
                {
                    "wildcard": {
                        "original_url": "*news.example.com*"
                    }
                }
            ]
        }
    }
    
    try:
        # news-enriched 인덱스만 검색 (실제 크롤링된 뉴스)
        # news 인덱스는 더미 데이터이므로 제외
        indices = ["news-enriched"]
        
        response = es.search(
            index=",".join(indices),
            body={
                "query": query,
                "size": size,
                "sort": [
                    {"published_at": {"order": "desc"}}
                ],
                "_source": ["title", "published_at", "sentiment_score", "original_url", "link"]
            }
        )
        
        items = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            # original_url이 없으면 link 필드 사용 (news-enriched 인덱스)
            original_url = source.get("original_url") or source.get("link") or ""
            items.append({
                "title": source.get("title", ""),
                "published_at": source.get("published_at", ""),
                "sentiment_score": source.get("sentiment_score", 0.0),
                "original_url": original_url,
            })
        
        return Response({
            "ticker": ticker,
            "items": items,
            "count": len(items)
        })
        
    except Exception as e:
        return Response({
            "items": [],
            "error": str(e)
        }, status=500)


@extend_schema(
    summary="특정 날짜 뉴스 조회",
    description="캔들 차트에서 특정 날짜를 클릭/호버했을 때 해당 일자의 뉴스를 보여줍니다.",
    parameters=[
        OpenApiParameter(name='ticker', description='종목 코드', required=True, type=str),
        OpenApiParameter(name='date', description='날짜 (YYYY-MM-DD)', required=True, type=str),
    ],
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['GET'])
def news_by_date(request):
    """
    GET /api/news/by-date/?ticker=005930&date=2024-12-25
    - 특정 날짜의 뉴스 조회 (캔들 차트 호버용)
    """
    ticker = request.GET.get("ticker", "")
    date_str = request.GET.get("date", "")
    
    if not ticker or not date_str:
        return Response({
            "error": "ticker와 date 파라미터가 필요합니다."
        }, status=400)
    
    try:
        # 날짜 파싱
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        es = _get_elasticsearch_client()
        if not es:
            return Response({
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
            
            return Response({
                "ticker": ticker,
                "date": date_str,
                "items": items,
                "count": len(items)
            })
            
        except Exception as e:
            return Response({
                "items": [],
                "error": str(e)
            }, status=500)
            
    except ValueError:
        return Response({
            "error": "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요."
        }, status=400)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=500)

@extend_schema(
    summary="실시간 Hot 키워드",
    description="최근 7일간 뉴스 데이터에서 가장 많이 언급된 키워드 TOP 5를 반환합니다.",
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['GET'])
def hot_keywords(request):
    """
    GET /api/news/hot-keywords/
    - 최근 7일간 뉴스 제목에서 빈도수가 높은 상위 5개 키워드 반환
    - Elasticsearch Aggregation 사용
    """
    es = _get_elasticsearch_client()
    if not es:
        return Response({
            "keywords": [],
            "message": "Elasticsearch 연결 실패"
        }, status=500)
    
    # 최근 7일 계산
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    try:
        # Elasticsearch 쿼리: 최근 7일간 뉴스 제목 집계
        # news-enriched 인덱스 사용
        response = es.search(
            index="news-enriched",  # news-enriched 인덱스 사용
            body={
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "published_at": {
                                        "gte": seven_days_ago.isoformat()
                                    }
                                }
                            },
                            {
                                "exists": {
                                    "field": "title"
                                }
                            }
                        ]
                    }
                },
                "size": 200,  # 최근 200개 뉴스 제목 가져오기
                "_source": ["title"]
            }
        )
        
        # 제목에서 단어 빈도 계산
        stopwords = {
            "이", "가", "을", "를", "의", "에", "와", "과", "도", "로", "으로",
            "는", "은", "에서", "에게", "한", "하다", "되다", "있다", "없다",
            "그", "그것", "이것", "저것", "것", "수", "때", "경우", "등", "및",
            "또한", "또", "그리고", "하지만", "그러나", "따라서", "그래서",
            "뉴스", "기사", "보도", "발표", "확인", "알려", "밝혀", "전해",
            "오늘", "어제", "내일", "최근", "지난", "올해", "작년", "내년",
            "KBS", "MBC", "SBS", "JTBC", "조선", "중앙", "동아", "한겨레"
        }
        
        word_freq = {}
        for hit in response.get("hits", {}).get("hits", []):
            title = hit.get("_source", {}).get("title", "")
            # 공백과 특수문자로 분리
            words = title.replace("…", " ").replace("-", " ").replace(":", " ").replace("·", " ").split()
            for word in words:
                word = word.strip(".,!?()[]\"'")
                # 2글자 이상, 불용어 제외, 숫자 제외
                if (word and 
                    len(word) >= 2 and 
                    word not in stopwords and
                    not word.isdigit() and
                    not word.startswith("http")):
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬하여 상위 키워드 추출
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = []
        for word, count in sorted_words:
            keywords.append({
                "keyword": word,
                "count": count
            })
            if len(keywords) >= 5:
                break
        
        return Response({
            "keywords": keywords[:5],  # 최대 5개
            "period": "7일",
            "total_news": response.get("hits", {}).get("total", {}).get("value", 0)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "keywords": [],
            "error": str(e)
        }, status=500)


@extend_schema(
    summary="뉴스 기반 AI 채팅 (Deprecated)",
    description="뉴스 앱 내부의 간단한 챗봇 기능입니다. (chat 앱의 AskQuestionView 사용 권장)",
    request=inline_serializer(
        name='NewsChatRequest',
        fields={'question': serializers.CharField()}
    ),
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(['POST'])
def chat(request):
    """
    POST /api/news/chat/
    - RAG 기반 AI 챗봇
    - 사용자 질문을 받아 Elasticsearch에서 관련 뉴스를 검색하고, LLM으로 답변 생성
    """
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        
        if not question:
            return Response({
                "error": "question 파라미터가 필요합니다."
            }, status=400)
        
        es = _get_elasticsearch_client()
        if not es:
            return Response({
                "error": "Elasticsearch 연결 실패"
            }, status=500)
        
        # 1. Elasticsearch에서 관련 뉴스 검색
        search_query = {
            "bool": {
                "should": [
                    {
                        "match": {
                            "title": question
                        }
                    },
                    {
                        "match": {
                            "content_summary": question
                        }
                    }
                ],
                "minimum_should_match": 1,
                "must_not": [
                    # 더미 URL 제외
                    {
                        "wildcard": {
                            "original_url": "*news.example.com*"
                        }
                    }
                ]
            }
        }
        
        try:
            # news-enriched 인덱스에서 검색
            es_response = es.search(
                index="news-enriched",
                body={
                    "query": search_query,
                    "size": 5,  # 최대 5개 뉴스
                    "sort": [
                        {"published_at": {"order": "desc"}}
                    ],
                    "_source": ["title", "content_summary", "published_at", "link", "original_url"]
                }
            )
            
            # 검색된 뉴스 추출
            news_items = []
            for hit in es_response.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                news_items.append({
                    "title": source.get("title", ""),
                    "content": source.get("content_summary", ""),
                    "published_at": source.get("published_at", ""),
                    "url": source.get("link") or source.get("original_url", "")
                })
            
            # 뉴스가 없으면 기본 메시지 반환
            if not news_items:
                return Response({
                    "answer": "죄송합니다. 관련 뉴스를 찾을 수 없습니다.",
                    "sources": []
                })
            
            # 2. 검색된 뉴스를 컨텍스트로 LLM에 전달
            context = "\n\n".join([
                f"제목: {item['title']}\n내용: {item['content'][:500]}"
                for item in news_items
            ])
            
            prompt = f"""다음은 최근 뉴스 기사들입니다:

{context}

위 뉴스 기사들을 참고하여 다음 질문에 답변해주세요. 답변은 간결하고 명확하게 작성해주세요.

질문: {question}

답변:"""
            
            # OpenAI API 호출
            try:
                client = get_openai_client()
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 주식 시장 뉴스를 분석하는 전문가입니다. 제공된 뉴스 기사를 바탕으로 사용자의 질문에 정확하고 간결하게 답변해주세요."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                answer = response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"OpenAI API 호출 실패: {e}")
                # OpenAI API 실패 시 간단한 답변 생성
                answer = f"'{question}'에 대한 관련 뉴스를 {len(news_items)}개 찾았습니다. 주요 내용은 다음과 같습니다:\n\n"
                for i, item in enumerate(news_items[:3], 1):
                    answer += f"{i}. {item['title']}\n"
            
            # 3. 참고한 뉴스 제목 목록
            sources = [item["title"] for item in news_items]
            
            return Response({
                "answer": answer,
                "sources": sources
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"뉴스 검색 실패: {str(e)}"
            }, status=500)
            
    except json.JSONDecodeError:
        return Response({
            "error": "잘못된 JSON 형식입니다."
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "error": str(e)
        }, status=500)
