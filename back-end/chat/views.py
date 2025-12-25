import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .rag_service import rag_service

# ✅ Swagger 임포트
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

logger = logging.getLogger(__name__)

class AskQuestionView(APIView):
    @extend_schema(
        summary="RAG AI 챗봇 질문",
        description="사용자의 질문을 받아 벡터 DB(Elasticsearch) 검색 후 LLM이 답변을 생성합니다.",
        request=inline_serializer(
            name='ChatQuestionRequest',
            fields={
                'question': serializers.CharField(help_text="예: 삼성전자 최근 이슈 알려줘")
            }
        ),
        responses={
            200: inline_serializer(
                name='ChatResponse',
                fields={
                    'question': serializers.CharField(),
                    'answer': serializers.CharField(),
                    'references': serializers.ListField(child=serializers.CharField())
                }
            )
        }
    )
    def post(self, request):
        query = request.data.get("question")
        
        if not query:
            return Response(
                {"error": "Question field is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contexts = rag_service.retrieve_context(query)
            answer = rag_service.generate_answer(query, contexts)
            
            return Response({
                "question": query,
                "answer": answer,
                "references": contexts
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing RAG request: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred.", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )