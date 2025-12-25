from django.urls import path
from .views import AskQuestionView

urlpatterns = [
    # API 엔드포인트: /api/chat/ask/
    path('ask/', AskQuestionView.as_view(), name='ask_question'),
]