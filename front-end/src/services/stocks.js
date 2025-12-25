/**
 * 주식 데이터 API 서비스
 * 백엔드 API와 통신하는 함수들을 제공합니다.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * 현재가 조회 (Redis에서)
 * @param {string} ticker - 종목 코드 (예: "005930")
 * @returns {Promise<{code: string, price: number, change_rate: number, volume: number, timestamp: string}>}
 */
export async function fetchCurrentPrice(ticker) {
  try {
    const response = await fetch(`${API_BASE}/api/current-price/${ticker}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        // Redis에 데이터가 없는 경우 (정상적인 상황일 수 있음)
        return {
          code: ticker,
          price: null,
          change_rate: 0,
          volume: 0,
          timestamp: null,
        };
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      code: data.code || ticker,
      price: data.price || null,
      change_rate: data.change_rate || 0,
      volume: data.volume || 0,
      timestamp: data.timestamp || null,
    };
  } catch (error) {
    console.error(`❌ 현재가 조회 실패 (${ticker}):`, error);
    // 에러 발생 시 기본값 반환
    return {
      code: ticker,
      price: null,
      change_rate: 0,
      volume: 0,
      timestamp: null,
    };
  }
}

/**
 * 차트 데이터 조회 (PostgreSQL에서)
 * @param {string} ticker - 종목 코드 (예: "005930")
 * @param {string} range - 조회 기간 (예: "1d", "1w", "1m", "3m", "1y")
 * @returns {Promise<{code: string, range: string, labels: string[], candles: Array, price: number[], volume: number[], sentiment: any[], flow: any[]}>}
 */
export async function fetchChart(ticker, range = "1w") {
  try {
    const response = await fetch(`${API_BASE}/api/chart/${ticker}?range=${range}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      code: data.code || ticker,
      range: data.range || range,
      labels: data.labels || [],
      candles: data.candles || [], // OHLCV 캔들 데이터
      price: data.price || [], // 하위 호환성
      volume: data.volume || [], // 하위 호환성
      sentiment: data.sentiment || [],
      flow: data.flow || [],
      ai_reports: data.ai_reports || {},
    };
  } catch (error) {
    console.error(`❌ 차트 데이터 조회 실패 (${ticker}, ${range}):`, error);
    // 에러 발생 시 기본값 반환
    return {
      code: ticker,
      range: range,
      labels: [],
      candles: [],
      price: [],
      volume: [],
      sentiment: [],
      flow: [],
      ai_reports: {},
    };
  }
}

/**
 * 여러 종목의 현재가를 한 번에 조회
 * @param {string[]} tickers - 종목 코드 배열
 * @returns {Promise<Array>}
 */
export async function fetchMultiplePrices(tickers) {
  const promises = tickers.map(ticker => fetchCurrentPrice(ticker));
  return Promise.allSettled(promises);
}

/**
 * 특정 날짜의 뉴스 조회 (캔들 차트 호버용)
 * @param {string} ticker - 종목 코드 (예: "005930")
 * @param {string} date - 날짜 (예: "2024-12-25")
 * @returns {Promise<{ticker: string, date: string, items: Array, count: number}>}
 */
export async function fetchNewsByDate(ticker, date) {
  try {
    const response = await fetch(`${API_BASE}/api/news/by-date/?ticker=${ticker}&date=${date}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      ticker: data.ticker || ticker,
      date: data.date || date,
      items: data.items || [],
      count: data.count || 0,
    };
  } catch (error) {
    console.error(`❌ 뉴스 조회 실패 (${ticker}, ${date}):`, error);
    return {
      ticker: ticker,
      date: date,
      items: [],
      count: 0,
    };
  }
}

