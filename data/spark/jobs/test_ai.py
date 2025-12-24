import os
from dotenv import load_dotenv

# 1. .env 파일의 환경 변수를 불러옵니다.
# (파일이 스크립트와 같은 경로에 있다고 가정합니다)
load_dotenv()
from news_ai_batch import openai_summarize_and_sentiment

# 2. os.environ에서 값을 가져옵니다. 
# 만약 키가 없다면 None을 반환하므로 미리 체크할 수 있습니다.
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ 에러: .env 파일에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
else:
    # news_ai_batch 내의 함수들이 os.environ["OPENAI_API_KEY"]를 사용하므로 별도 설정 불필요
    test_title = "삼성전자, 4만전자 탈출하나? 외국인 대규모 매수세"
    test_content = "최근 삼성전자의 주가가 반등하며 외국인 투자자들의 매수세가 이어지고 있습니다. 반도체 업황 개선 기대감이 반영된 것으로 보입니다..."

    print("🤖 AI 분석을 시작합니다...")
    try:
        summary, score = openai_summarize_and_sentiment(test_title, test_content)

        print(f"\n--- AI 분석 결과 ---")
        print(f"요약: {summary}")
        print(f"감정 점수: {score} (1에 가까울수록 긍정)")
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")