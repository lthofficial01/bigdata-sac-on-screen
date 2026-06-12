#!/bin/bash
# ============================================================
# SAC on Screen: HDP full pipeline
# ============================================================
# Runs the reproducible full pipeline:
#   HDFS raw CSV -> Spark Parquet -> Hive tables
#   -> HiveQL analysis -> result CSV
#
# Usage:
#   bash scripts/run_pipeline.sh
#
# Required:
#   - HDP Sandbox with HDFS, Spark, HiveServer2
#   - Full raw CSV files in HDFS raw path
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

HDFS_BASE="${HDFS_BASE:-/user/maria_dev/sac_on_screen}"
HIVE_USER="${HIVE_USER:-hive}"
HIVE_DB="${HIVE_DB:-sac_on_screen}"
HIVE_TABLE_PREFIX="${HIVE_TABLE_PREFIX-}"
export HDFS_BASE HIVE_USER HIVE_DB HIVE_TABLE_PREFIX

detect_python() {
  local candidate
  for candidate in python3.6 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 6) else 1)
PY
    then
      command -v "$candidate"
      return 0
    fi
  done

  echo "[ERROR] Python 3.6+ executable not found. Set PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON." >&2
  exit 1
}

SPARK_PYTHON="${PYSPARK_PYTHON:-$(detect_python)}"
SPARK_DRIVER_PYTHON="${PYSPARK_DRIVER_PYTHON:-$SPARK_PYTHON}"
export PYSPARK_PYTHON="$SPARK_PYTHON"
export PYSPARK_DRIVER_PYTHON="$SPARK_DRIVER_PYTHON"

echo "============================================================"
echo " SAC on Screen full pipeline"
echo " Project root: ${PROJECT_ROOT}"
echo " HDFS base   : ${HDFS_BASE}"
echo " Hive user   : ${HIVE_USER}"
echo " Hive DB     : ${HIVE_DB}"
echo " Hive prefix : ${HIVE_TABLE_PREFIX}"
echo " Python      : ${SPARK_PYTHON}"
echo "============================================================"

echo "[STEP 1/6] Prepare raw CSV files in HDFS"
hdfs dfs -mkdir -p "${HDFS_BASE}/raw" "${HDFS_BASE}/processed"
for raw_file in sac_performances.csv sac_booking_age.csv population_age.csv; do
  if ! hdfs dfs -test -f "${HDFS_BASE}/raw/${raw_file}"; then
    echo "[ERROR] Missing HDFS raw CSV: ${HDFS_BASE}/raw/${raw_file}"
    echo "Upload the three raw CSV files to ${HDFS_BASE}/raw in Ambari Files View."
    exit 1
  fi
done

echo "[STEP 2/6] Run Spark preprocessing"
spark-submit --master yarn \
  --conf spark.pyspark.python="${SPARK_PYTHON}" \
  --conf spark.pyspark.driver.python="${SPARK_DRIVER_PYTHON}" \
  src/pipeline/spark_preprocess.py \
  --base-path "${HDFS_BASE}" \
  --performance-path "${HDFS_BASE}/raw/sac_performances.csv" \
  --booking-path "${HDFS_BASE}/raw/sac_booking_age.csv" \
  --population-path "${HDFS_BASE}/raw/population_age.csv"

echo "[STEP 3/6] Grant Hive access to processed HDFS outputs"
hdfs dfs -chmod -R 777 "${HDFS_BASE}/processed"

echo "[STEP 4/6] Create Hive database and external tables"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  -e "CREATE DATABASE IF NOT EXISTS ${HIVE_DB};"

beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --hivevar db_name="${HIVE_DB}" \
  --hivevar hdfs_base="${HDFS_BASE}" \
  --hivevar table_prefix="${HIVE_TABLE_PREFIX}" \
  -f hive/create_tables.hql

echo "[STEP 5/6] Run Hive analysis queries"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --hivevar db_name="${HIVE_DB}" \
  --hivevar table_prefix="${HIVE_TABLE_PREFIX}" \
  -f hive/analysis_queries.hql

echo "[STEP 6/6] Export result CSV files and upload to HDFS"
bash scripts/export_hive_results.sh

echo "============================================================"
echo " Pipeline finished"
echo " HDFS processed path: ${HDFS_BASE}/processed"
echo " HDFS exports path  : ${HDFS_BASE}/exports"
echo "============================================================"
