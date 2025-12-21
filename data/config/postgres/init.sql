-- 1. TimescaleDB 확장 (필수)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. StockPrices (시계열 데이터 - 이건 Django가 못 만듦)
CREATE TABLE IF NOT EXISTS StockPrices (
    time TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(20),
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    PRIMARY KEY (time, stock_code)
);

-- 3. Hypertable 변환 (핵심)
-- (이미 존재한다는 에러 방지를 위해 if not exists 로직 추가 가능하지만, 
--  보통 init.sql은 최초 1회만 실행되므로 그냥 둬도 됨)
SELECT create_hypertable('StockPrices', 'time', if_not_exists => TRUE);