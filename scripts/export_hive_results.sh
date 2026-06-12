#!/bin/bash
# ============================================================
# SAC on Screen: Hive result CSV export
# ============================================================
# Exports the three report CSV files from Hive, creates Excel-friendly
# UTF-8 BOM copies, and uploads them to HDFS for Ambari Files View.
#
# Usage:
#   bash scripts/export_hive_results.sh
#
# Optional environment variables:
#   HDFS_BASE=/user/maria_dev/sac_on_screen
#   HDFS_EXPORT_DIR=/user/maria_dev/sac_on_screen/exports
#   HIVE_USER=hive
#   HIVE_DB=sac_on_screen
#   HIVE_TABLE_PREFIX=
#   LOCAL_EXPORT_DIR=.
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

HDFS_BASE="${HDFS_BASE:-/user/maria_dev/sac_on_screen}"
HDFS_EXPORT_DIR="${HDFS_EXPORT_DIR:-${HDFS_BASE}/exports}"
HIVE_USER="${HIVE_USER:-hive}"
HIVE_DB="${HIVE_DB:-sac_on_screen}"
HIVE_TABLE_PREFIX="${HIVE_TABLE_PREFIX-}"
LOCAL_EXPORT_DIR="${LOCAL_EXPORT_DIR:-.}"

mkdir -p "${LOCAL_EXPORT_DIR}"

AGE_CSV="${LOCAL_EXPORT_DIR}/age_preference_weights.csv"
GENRE_TOP_CSV="${LOCAL_EXPORT_DIR}/genre_top_regions.csv"
RECOMMEND_CSV="${LOCAL_EXPORT_DIR}/region_genre_recommendations.csv"

AGE_EXCEL_CSV="${LOCAL_EXPORT_DIR}/age_preference_weights_excel.csv"
GENRE_TOP_EXCEL_CSV="${LOCAL_EXPORT_DIR}/genre_top_regions_excel.csv"
RECOMMEND_EXCEL_CSV="${LOCAL_EXPORT_DIR}/region_genre_recommendations_excel.csv"

echo "============================================================"
echo " SAC on Screen Hive result export"
echo " Hive user       : ${HIVE_USER}"
echo " Hive DB         : ${HIVE_DB}"
echo " Hive prefix     : ${HIVE_TABLE_PREFIX}"
echo " Local export dir: ${LOCAL_EXPORT_DIR}"
echo " HDFS export dir : ${HDFS_EXPORT_DIR}"
echo "============================================================"

echo "[EXPORT 1/3] Age-group genre preference ranking"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --silent=true \
  --showHeader=true \
  --outputformat=csv2 \
  -e "USE ${HIVE_DB};
      SELECT
        age_group,
        genre,
        booking_count,
        preference_weight,
        RANK() OVER (
          PARTITION BY age_group
          ORDER BY preference_weight DESC
        ) AS genre_rank
      FROM ${HIVE_TABLE_PREFIX}age_preference_weights
      WHERE preference_weight > 0
      ORDER BY age_group, genre_rank;" \
  > "${AGE_CSV}"

echo "[EXPORT 2/3] Top regions by genre demand index"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --silent=true \
  --showHeader=true \
  --outputformat=csv2 \
  -e "USE ${HIVE_DB};
      WITH ranked AS (
        SELECT
          genre,
          region_code,
          region_name,
          demand_index,
          RANK() OVER (
            PARTITION BY genre
            ORDER BY demand_index DESC
          ) AS region_rank_in_genre
        FROM ${HIVE_TABLE_PREFIX}region_demand_index
      )
      SELECT
        genre,
        region_rank_in_genre,
        region_code,
        region_name,
        demand_index
      FROM ranked
      WHERE region_rank_in_genre <= 10
      ORDER BY genre, region_rank_in_genre;" \
  > "${GENRE_TOP_CSV}"

echo "[EXPORT 3/3] Region recommendation Top 3"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --silent=true \
  --showHeader=true \
  --outputformat=csv2 \
  -e "USE ${HIVE_DB};
      SELECT
        region_code,
        region_name,
        genre,
        demand_index,
        recommendation_rank
      FROM ${HIVE_TABLE_PREFIX}region_genre_recommendations
      WHERE recommendation_rank <= 3
      ORDER BY region_name, recommendation_rank;" \
  > "${RECOMMEND_CSV}"

echo "[EXCEL] Create UTF-8 BOM CSV files"
printf '\xEF\xBB\xBF' > "${AGE_EXCEL_CSV}"
cat "${AGE_CSV}" >> "${AGE_EXCEL_CSV}"

printf '\xEF\xBB\xBF' > "${GENRE_TOP_EXCEL_CSV}"
cat "${GENRE_TOP_CSV}" >> "${GENRE_TOP_EXCEL_CSV}"

printf '\xEF\xBB\xBF' > "${RECOMMEND_EXCEL_CSV}"
cat "${RECOMMEND_CSV}" >> "${RECOMMEND_EXCEL_CSV}"

echo "[HDFS] Upload Excel CSV files for Ambari Files View"
hdfs dfs -mkdir -p "${HDFS_EXPORT_DIR}"
hdfs dfs -put -f "${AGE_EXCEL_CSV}" "${HDFS_EXPORT_DIR}/"
hdfs dfs -put -f "${GENRE_TOP_EXCEL_CSV}" "${HDFS_EXPORT_DIR}/"
hdfs dfs -put -f "${RECOMMEND_EXCEL_CSV}" "${HDFS_EXPORT_DIR}/"

echo "============================================================"
echo " Result export finished"
echo " Local CSV files:"
echo "  - ${AGE_CSV}"
echo "  - ${GENRE_TOP_CSV}"
echo "  - ${RECOMMEND_CSV}"
echo " HDFS exports:"
hdfs dfs -ls -h "${HDFS_EXPORT_DIR}"
echo "============================================================"
