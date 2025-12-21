from django.db import connection

def get_latest_price_from_db(stock_code: str):
    """
    TimescaleDB에서 해당 종목의 가장 최근 close 가격 조회
    """
    query = """
        SELECT close
        FROM stocks_stockprice
        WHERE stock_id = %s
        ORDER BY time DESC
        LIMIT 1;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [stock_code])
        row = cursor.fetchone()

    if row:
        return row[0]
    return None
