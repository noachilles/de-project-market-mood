import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, lit
from pyspark.sql.types import StringType
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def fetch_content(url):
    if not url: return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 기사 본문 영역만 타겟팅 (사이트별 최적화 필요)
            paragraphs = soup.find_all('p')
            content = " ".join([p.get_text() for p in paragraphs])
            return content[:5000] 
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Airflow에서 전달하는 기준 날짜 (예: 20251223)
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    spark = SparkSession.builder \
        .appName(f"NewsCrawler_{target_date}") \
        .getOrCreate()

    crawl_udf = udf(fetch_content, StringType())

    # 1. 원천 데이터(Kafka에서 넘어온 Parquet) 읽기
    input_path = f"/opt/data-lake/news/dt={target_date}/hr=*/"
    output_path = f"/opt/data-lake/news_enriched/dt={target_date}/"
    
    try:
        raw_df = spark.read.parquet(input_path)
        
        # 2. 중복 방지: 이미 크롤링된 데이터가 있는지 확인 (Incremental Load)
        try:
            existing_df = spark.read.parquet(output_path)
            # 기존에 없는 링크만 필터링
            df_to_crawl = raw_df.join(existing_df, ["link"], "left_anti")
        except:
            df_to_crawl = raw_df

        # 3. 크롤링 수행
        if df_to_crawl.count() > 0:
            result_df = df_to_crawl.withColumn("content", crawl_udf(col("link"))) \
                                   .withColumn("updated_at", lit(datetime.now().isoformat()))
            
            # 4. 데이터 레이크에 누적 저장
            result_df.write.mode("append").parquet(output_path)
            print(f"✅ {result_df.count()}건의 새로운 뉴스 본문 수집 완료")
        else:
            print("ℹ️ 새로 수집할 뉴스 데이터가 없습니다.")

    except Exception as e:
        print(f"❌ 작업 실패: {e}")

    spark.stop()

if __name__ == "__main__":
    main()