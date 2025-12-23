import csv
import re
from elasticsearch import Elasticsearch, helpers

ES_URL = "http://elasticsearch:9200"   # docker-compose 내부 기준
INDEX = "stocks-kospi"
CSV_PATH = "/data/flink/jobs/kospi_code.csv"

CODE_6DIGIT = re.compile(r"^\d{6}$")

def get_first(row, keys, default=""):
    for k in keys:
        v = row.get(k)
        if v is not None:
            return str(v).strip()
    return default

def main():
    es = Elasticsearch(ES_URL)

    actions = []
    total = 0
    kept = 0

    # ✅ BOM 처리: encoding="utf-8-sig" 사용하면 헤더의 \ufeff 제거됨
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print("CSV headers:", reader.fieldnames)

        for row in reader:
            total += 1

            # ✅ 단축코드(6자리) / 한글명 / 표준코드 / 그룹코드
            code = get_first(row, ["단축코드", "\ufeff단축코드"])
            name = get_first(row, ["한글명"])
            std_code = get_first(row, ["표준코드"])
            group_code = get_first(row, ["그룹코드"])

            if not code or not name:
                continue

            # ✅ 주식(일반 종목)만: 6자리 숫자 코드만 적재
            if not CODE_6DIGIT.match(code):
                continue

            kept += 1
            actions.append({
                "_index": INDEX,
                "_id": code,
                "_source": {
                    "code": code,
                    "name": name,
                    "std_code": std_code,
                    "group_code": group_code,
                }
            })

    if actions:
        helpers.bulk(es, actions, request_timeout=120)

    print(f"✅ Indexed {kept}/{total} rows into {INDEX}")

if __name__ == "__main__":
    main()
