# yfinance: 1d 전 데이터부터 가져올 수 있음
# import yfinance as yf
# import time
# import matplotlib.pyplot as plt

# while True:
#     data = yf.Ticker("AAPL")
#     price = data.history(period="10m")["Close"].iloc[-1]
#     print(f"현재 AAPL 주가: {price:.2f} USD")
#     time.sleep(60)  # 60초마다 데이터를 갱신합니다.

#     # 주가 데이터 리스트
#     prices = []

#     # 무한 루프 코드 부분은 생략
#     # 1분마다 주가 가격을 prices 리스트에 추가
#     prices.append(price)

#     # 그래프 그리기
#     plt.plot(prices)
#     plt.title("AAPL 주가 실시간 모니터링")
#     plt.xlabel("시간(분)")
#     plt.ylabel("가격(USD)")
#     plt.show()

# 2. 제대로 실행되지 않음 - HTTP Error 403: Forbidden
# import pandas as pd

# # S&P 500 기업 목록 Wikipedia URL
# sp_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# # read_html은 URL을 직접 읽을 수 있습니다.
# # 페이지에는 2개의 테이블이 있으며, 첫 번째 테이블[0]이 S&P 500 구성 종목입니다.
# sp500_constituents = pd.read_html(sp_url, header=0)[0]

# # sp500_constituents.info()

# # 상위 5개 행 출력
# print(sp500_constituents.head())

# 3. 가능 주식 항목: ['france', 'germany', 'italy', 'netherlands', 'sweden']
# import investpy
# import pandas
# from datetime import datetime

# countriesAvailable = investpy.get_certificate_countries()
# print(countriesAvailable)

