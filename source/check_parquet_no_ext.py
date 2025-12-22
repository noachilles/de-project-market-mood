import pandas as pd
import os

# [수정] 확인하고 싶은 파일의 "전체 경로"를 복사해서 아래에 넣으세요.
# 예: ./data/volumes/data-lake/news/dt=2025-12-22/hr=14/part-어쩌구저쩌구...
TARGET_FILE = "/home/ssafy/de-project/data/volumes/data-lake/news/dt=2025-12-22/hr=05/part-62170f0d-2e7b-458d-adc6-1fd77a51801a-0-12"

# 파일 경로 자동 찾기 (위 경로를 모르겠으면 사용)
base_path = "../data/volumes/data-lake/news/"
if not os.path.exists(TARGET_FILE):
    print("⚠️ 지정한 파일이 없어서, 자동으로 가장 최신 파일을 찾습니다...")
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.startswith("part-"):
                TARGET_FILE = os.path.join(root, file)
                break

print(f"📂 읽으려는 파일: {TARGET_FILE}")

try:
    # 확장자가 없어도 engine='pyarrow'라고 알려주면 Parquet으로 읽습니다.
    df = pd.read_parquet(TARGET_FILE, engine='pyarrow')
    
    print("\n✅ 데이터 로드 성공! (상위 5개)")
    print("-" * 50)
    # 모든 컬럼이 다 나오게 설정
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    print(df.head())
    
    print("-" * 50)
    print(f"📊 저장된 데이터 개수: {len(df)}개")
    
    # [핵심 확인] related_stocks 컬럼 확인
    if 'related_stocks' in df.columns:
        print("\n🔍 종목 매칭 샘플 (related_stocks):")
        print(df[['title', 'related_stocks']].head())

except Exception as e:
    print(f"\n❌ 읽기 실패: {e}")