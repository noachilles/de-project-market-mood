import FinanceDataReader as fdr
from elasticsearch import Elasticsearch, helpers
import os

# 1. Elasticsearch 연결 (Docker 환경에 맞게 수정)
# 로컬에서 실행 시 localhost, 도커 내부면 es-container
es = Elasticsearch("http://elasticsearch:9200")

INDEX_NAME = "stock_meta_idx"

def load_stocks_to_es():
    print("⏳ KRX 전체 종목 다운로드 중...")
    # KRX: 한국거래소 전체 종목 (코스피, 코스닥, 코넥스)
    df = fdr.StockListing('KRX') 
    
    # 필요한 컬럼만 선택: 종목코드, 종목명, 시장구분, 섹터
    # Code, Name, Market, Sector
    stocks = df[['Code', 'Name', 'Market']].to_dict('records')
    
    print(f"✅ 총 {len(stocks)}개 종목 데이터 준비 완료. ES 적재 시작...")

    # 2. 인덱스 생성 (없으면 생성)
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "ticker": {"type": "keyword"}, # 정확한 매칭용
                        "name": {"type": "text"},      # 부분 검색용
                        "market": {"type": "keyword"}
                    }
                }
            }
        )

    # 3. Bulk Insert (한번에 때려넣기)
    actions = []
    for stock in stocks:
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "ticker": stock['Code'], # 005930
                "name": stock['Name'],   # 삼성전자
                "market": stock['Market'] # KOSPI
            }
        })

    helpers.bulk(es, actions)
    print(f"🎉 성공! {len(actions)}개 종목이 Elasticsearch에 저장되었습니다.")

if __name__ == "__main__":
    # 실행 전: pip install finance-datareader elasticsearch
    try:
        load_stocks_to_es()
    except Exception as e:
        print(f"오류 발생: {e}")