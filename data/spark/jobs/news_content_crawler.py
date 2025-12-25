from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------
# 1. 크롤링 함수 (Worker Node에서 실행됨)
# ---------------------------------------------------------
def fetch_content(url):
    try:
        # 타임아웃 필수 설정 (무한 대기 방지)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # [간단 로직] p 태그를 모두 긁어서 합침
            # 실제로는 사이트(mk, naver 등)별로 로직 분기 처리가 필요함
            paragraphs = soup.find_all('p')
            content = " ".join([p.get_text() for p in paragraphs])
            
            return content[:5000] # 너무 길면 자름
        else:
            return "Error: Status Code " + str(response.status_code)
            
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------------------------------------------------
# 2. Main Spark Job
# ---------------------------------------------------------
def main():
    # Spark 세션 생성 (ES 커넥터 JAR은 이미 Dockerfile에서 다운로드됨)
    # --jars 옵션으로 직접 지정하거나, SparkSession에서 설정
    spark = SparkSession.builder \
        .appName("NewsContentCrawler") \
        .getOrCreate()

    # UDF 등록
    crawl_udf = udf(fetch_content, StringType())

    # 1. Parquet 읽기 (오늘 날짜 폴더 예시)
    # 실제로는 변수로 날짜를 받아야 함 (f".../dt={today_date}")
    parquet_path = "/opt/data-lake/news/" 
    df = spark.read.parquet(parquet_path)

    print("=== 원본 데이터 (Parquet) ===")
    df.select("title", "link").show(3, truncate=False)

    # 2. 크롤링 수행 (가장 무거운 작업)
    # link 컬럼을 UDF에 넣어서 content 컬럼 생성
    result_df = df.withColumn("content", crawl_udf(col("link")))

    # 3. 결과 확인
    print("=== 크롤링 결과 (Content Added) ===")
    result_df.select("title", "content").show(3, truncate=True)

    try:
        # 에러가 발생한 행은 건너뛰고 나머지만 저장
        # content가 "Error:"로 시작하는 행 필터링
        valid_df = result_df.filter(~col("content").startswith("Error:"))
        
        print(f"=== 크롤링 성공: {valid_df.count()}건 / 전체: {result_df.count()}건 ===")
        
        if valid_df.count() > 0:
            # 필요한 컬럼만 선택하여 저장 (Elasticsearch 매핑과 일치)
            es_df = valid_df.select(
                col("title"),
                col("link"),
                col("content").alias("content_summary"),  # content를 content_summary로 매핑
                col("source"),
                col("published_at"),
                col("related_stocks").alias("stock_codes")  # related_stocks를 stock_codes로 매핑
            )
            
            es_df.write \
                .format("org.elasticsearch.spark.sql") \
                .option("es.nodes", "elasticsearch") \
                .option("es.port", "9200") \
                .option("es.resource", "news-enriched/_doc") \
                .option("es.nodes.wan.only", "true") \
                .option("es.mapping.id", "link") \
                .option("es.write.operation", "upsert") \
                .option("es.mapping.date.rich", "false") \
                .mode("append") \
                .save()
                
            print("=== [Success] 저장 완료! 'news-enriched' 인덱스를 확인하세요. ===")
        else:
            print("=== [Warning] 저장할 유효한 데이터가 없습니다. ===")
        
    except Exception as e:
        print(f"=== [Error] 저장 실패: {e} ===")
        import traceback
        traceback.print_exc()

    spark.stop()

if __name__ == "__main__":
    main()