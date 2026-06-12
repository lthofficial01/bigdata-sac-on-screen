-- ============================================================
-- SAC on Screen: HiveQL analysis queries
-- ============================================================
-- Required hive variables:
--   db_name      Existing Hive database name
--   table_prefix Prefix for table names, for example sac_sample_
--
-- Usage:
--   beeline -u jdbc:hive2://localhost:10000 \
--     --hivevar db_name=default \
--     --hivevar table_prefix=sac_ \
--     -f hive/analysis_queries.hql
-- ============================================================

USE ${hivevar:db_name};

-- Q1. Age-group genre preference ranking.
SELECT
    age_group,
    genre,
    preference_weight,
    RANK() OVER (PARTITION BY age_group ORDER BY preference_weight DESC) AS genre_rank
FROM ${hivevar:table_prefix}age_preference_weights
WHERE preference_weight > 0
ORDER BY age_group, genre_rank;

-- Q2. Top regions by genre demand index.
WITH ranked AS (
    SELECT
        region_code,
        region_name,
        genre,
        demand_index,
        RANK() OVER (
            PARTITION BY genre
            ORDER BY demand_index DESC
        ) AS region_rank_in_genre
    FROM ${hivevar:table_prefix}region_demand_index
)
SELECT
    genre,
    region_rank_in_genre,
    region_code,
    region_name,
    demand_index
FROM ranked
WHERE region_rank_in_genre <= 10
ORDER BY genre, region_rank_in_genre;

-- Q3. Top recommended genres by region.
SELECT
    region_code,
    region_name,
    genre AS recommended_genre,
    demand_index,
    recommendation_rank
FROM ${hivevar:table_prefix}region_genre_recommendations
WHERE recommendation_rank <= 3
ORDER BY region_name, recommendation_rank;
