-- ============================================================
-- SAC on Screen: Hive External Table 생성 DDL
-- ============================================================
-- Spark에서 처리한 Parquet 결과를 Hive External Table로 등록합니다.
-- HDP Sandbox 환경에서 beeline 또는 hive CLI로 실행합니다.
--
-- Usage:
--   beeline -u jdbc:hive2://localhost:10000 -f create_tables.hql
-- ============================================================

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS sac_on_screen;
USE sac_on_screen;

-- ============================================================
-- 1. 연령대별 콘텐츠 선호도 가중치 테이블
-- ============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS age_preference_weights (
    genre           STRING      COMMENT '공연/전시 장르 (클래식, 발레, 연극, 뮤지컬 등)',
    age_group       STRING      COMMENT '연령대 (10대, 20대, 30대, 40대, 50대, 60대이상)',
    booking_count   BIGINT      COMMENT '해당 장르-연령대 예매 건수',
    preference_weight DOUBLE    COMMENT '장르 내 연령대별 선호도 가중치 (0~1)'
)
STORED AS PARQUET
LOCATION '/user/ubuntu/sac_on_screen/processed/age_preference_weights/';

-- ============================================================
-- 2. 지역별 잠재 수요 지수 테이블
-- ============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS region_demand_index (
    region_code     STRING      COMMENT '시군구 행정코드',
    region_name     STRING      COMMENT '시군구명',
    genre           STRING      COMMENT '공연/전시 장르',
    demand_index    DOUBLE      COMMENT '잠재 수요 지수 (인구비율 × 선호도가중치 합산)'
)
STORED AS PARQUET
LOCATION '/user/ubuntu/sac_on_screen/processed/region_demand_index/';

-- ============================================================
-- 3. 최적 상영 입지 테이블
-- ============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS optimal_locations (
    region_code     STRING      COMMENT '시군구 행정코드',
    region_name     STRING      COMMENT '시군구명',
    facility_name   STRING      COMMENT '상영 가능 문화시설명',
    facility_type   STRING      COMMENT '시설 유형 (문화예술회관, 복합문화공간 등)',
    seat_count      INT         COMMENT '좌석 수',
    demand_index    DOUBLE      COMMENT '해당 지역 종합 수요 지수',
    accessibility_score DOUBLE  COMMENT '문화 접근성 점수 (낮을수록 사각지대)',
    priority_rank   INT         COMMENT '상영 우선순위 순위'
)
STORED AS PARQUET
LOCATION '/user/ubuntu/sac_on_screen/processed/optimal_locations/';
