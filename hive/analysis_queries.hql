-- ============================================================
-- SAC on Screen: HiveQL 분석 쿼리
-- ============================================================
-- 핵심 분석 질문 3가지에 대한 답을 도출하는 쿼리입니다.
--
-- Usage:
--   beeline -u jdbc:hive2://localhost:10000 -f analysis_queries.hql
-- ============================================================

USE sac_on_screen;

-- ============================================================
-- Q1. 연령대별 선호 콘텐츠와 킬러 장르는 어떻게 분포하는가?
-- ============================================================
-- 각 연령대에서 가장 선호도가 높은 상위 3개 장르를 추출합니다.
SELECT
    age_group,
    genre,
    preference_weight,
    RANK() OVER (PARTITION BY age_group ORDER BY preference_weight DESC) AS genre_rank
FROM age_preference_weights
WHERE preference_weight > 0
ORDER BY age_group, genre_rank;

-- ============================================================
-- Q2. 지역별 잠재적 문화 수요 지수 상위 지역은 어디인가?
-- ============================================================
-- 장르 무관하게 종합 수요 지수가 높은 상위 20개 지역을 추출합니다.
SELECT
    region_code,
    region_name,
    SUM(demand_index) AS total_demand_index
FROM region_demand_index
GROUP BY region_code, region_name
ORDER BY total_demand_index DESC
LIMIT 20;

-- ============================================================
-- Q3. 문화 사각지대 내 최적 우선순위 상영 입지는 어디인가?
-- ============================================================
-- 접근성이 낮으면서 수요가 높은 지역의 상영 가능 시설을 우선순위로 정렬합니다.
SELECT
    region_name,
    facility_name,
    facility_type,
    seat_count,
    demand_index,
    accessibility_score,
    priority_rank
FROM optimal_locations
WHERE accessibility_score < 0.3  -- 문화 접근성 하위 30% 지역
ORDER BY priority_rank ASC
LIMIT 30;
