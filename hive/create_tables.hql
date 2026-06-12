-- ============================================================
-- SAC on Screen: Hive External Table DDL
-- ============================================================
-- Required hive variables:
--   db_name      Existing Hive database name
--   hdfs_base    HDFS project base path
--   table_prefix Prefix for table names, for example sac_sample_
--
-- Usage:
--   beeline -u jdbc:hive2://localhost:10000 \
--     --hivevar db_name=default \
--     --hivevar hdfs_base=/user/maria_dev/sac_on_screen \
--     --hivevar table_prefix=sac_ \
--     -f hive/create_tables.hql
-- ============================================================

USE ${hivevar:db_name};

DROP TABLE IF EXISTS ${hivevar:table_prefix}age_preference_weights;
CREATE EXTERNAL TABLE ${hivevar:table_prefix}age_preference_weights (
    genre             STRING,
    age_group         STRING,
    booking_count     BIGINT,
    preference_weight DOUBLE
)
STORED AS PARQUET
LOCATION '${hivevar:hdfs_base}/processed/age_preference_weights/';

DROP TABLE IF EXISTS ${hivevar:table_prefix}region_demand_index;
CREATE EXTERNAL TABLE ${hivevar:table_prefix}region_demand_index (
    region_code  STRING,
    region_name  STRING,
    genre        STRING,
    demand_index DOUBLE
)
STORED AS PARQUET
LOCATION '${hivevar:hdfs_base}/processed/region_demand_index/';

DROP TABLE IF EXISTS ${hivevar:table_prefix}region_genre_recommendations;
CREATE EXTERNAL TABLE ${hivevar:table_prefix}region_genre_recommendations (
    region_code          STRING,
    region_name          STRING,
    genre                STRING,
    demand_index         DOUBLE,
    recommendation_rank  INT
)
STORED AS PARQUET
LOCATION '${hivevar:hdfs_base}/processed/region_genre_recommendations/';
