#!/bin/bash
# ============================================================
# SAC on Screen: HDFS sample smoke test
# ============================================================
# Runs the committed sample CSV files through HDFS, Spark, and Hive.
# This validates distributed-environment wiring without requiring full raw data.
#
# Usage:
#   bash scripts/run_hdfs_sample_pipeline.sh
#
# Optional environment variables:
#   HDFS_BASE=/user/maria_dev/sac_on_screen_sample
#   HIVE_USER=hive
#   HIVE_DB=default
#   HIVE_TABLE_PREFIX=sac_sample_
#   RESULT_CSV=sample_region_genre_recommendations.csv
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

HDFS_BASE="${HDFS_BASE:-/user/maria_dev/sac_on_screen_sample}"
HIVE_USER="${HIVE_USER:-hive}"
HIVE_DB="${HIVE_DB:-default}"
HIVE_TABLE_PREFIX="${HIVE_TABLE_PREFIX:-sac_sample_}"
RESULT_CSV="${RESULT_CSV:-sample_region_genre_recommendations.csv}"

SAMPLE_DIR="data/sample"
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
echo " SAC on Screen HDFS sample smoke test"
echo " Project root: ${PROJECT_ROOT}"
echo " HDFS base   : ${HDFS_BASE}"
echo " Hive user   : ${HIVE_USER}"
echo " Hive DB     : ${HIVE_DB}"
echo " Hive prefix : ${HIVE_TABLE_PREFIX}"
echo " Python      : ${SPARK_PYTHON}"
echo "============================================================"

for file in \
  "${SAMPLE_DIR}/sac_performances_sample.csv" \
  "${SAMPLE_DIR}/sac_booking_age_sample.csv" \
  "${SAMPLE_DIR}/population_age_sample.csv"
do
  if [ ! -f "$file" ]; then
    echo "[ERROR] Missing sample file: ${file}"
    exit 1
  fi
done

TMP_SAMPLE_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_SAMPLE_DIR}"' EXIT

echo "[INFO] Build HDFS smoke-test sample files"
"${SPARK_PYTHON}" - "${SAMPLE_DIR}" "${TMP_SAMPLE_DIR}" <<'PY'
import csv
import shutil
import sys
from pathlib import Path

sample_dir = Path(sys.argv[1])
tmp_dir = Path(sys.argv[2])

performance_src = sample_dir / "sac_performances_sample.csv"
booking_src = sample_dir / "sac_booking_age_sample.csv"
population_src = sample_dir / "population_age_sample.csv"

performance_dst = tmp_dir / "sac_performances.csv"
booking_dst = tmp_dir / "sac_booking_age.csv"
population_dst = tmp_dir / "population_age.csv"

shutil.copyfile(str(performance_src), str(performance_dst))
shutil.copyfile(str(population_src), str(population_dst))

with performance_src.open(encoding="utf-8-sig", newline="") as handle:
    performance_rows = list(csv.DictReader(handle))
titles = [row["TITLE"] for row in performance_rows if row.get("TITLE")]

with booking_src.open(encoding="utf-8-sig", newline="") as handle:
    reader = csv.DictReader(handle)
    fieldnames = reader.fieldnames
    booking_rows = list(reader)

if not titles or not booking_rows or not fieldnames:
    raise SystemExit("[ERROR] Sample files do not contain enough rows.")

for index, row in enumerate(booking_rows):
    row["TITLE"] = titles[index % len(titles)]

with booking_dst.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(booking_rows)
PY

echo "[STEP 1/8] Prepare HDFS directories"
hdfs dfs -rm -r -f "${HDFS_BASE}/raw" "${HDFS_BASE}/processed" >/dev/null 2>&1 || true
hdfs dfs -mkdir -p "${HDFS_BASE}/raw" "${HDFS_BASE}/processed"

echo "[STEP 2/8] Upload sample CSV files to HDFS"
hdfs dfs -put -f "${TMP_SAMPLE_DIR}/sac_performances.csv" "${HDFS_BASE}/raw/sac_performances.csv"
hdfs dfs -put -f "${TMP_SAMPLE_DIR}/sac_booking_age.csv" "${HDFS_BASE}/raw/sac_booking_age.csv"
hdfs dfs -put -f "${TMP_SAMPLE_DIR}/population_age.csv" "${HDFS_BASE}/raw/population_age.csv"

echo "[STEP 3/8] Run Spark preprocessing on HDFS sample data"
spark-submit --master yarn \
  --conf spark.pyspark.python="${SPARK_PYTHON}" \
  --conf spark.pyspark.driver.python="${SPARK_DRIVER_PYTHON}" \
  src/pipeline/spark_preprocess.py \
  --base-path "${HDFS_BASE}" \
  --performance-path "${HDFS_BASE}/raw/sac_performances.csv" \
  --booking-path "${HDFS_BASE}/raw/sac_booking_age.csv" \
  --population-path "${HDFS_BASE}/raw/population_age.csv"

echo "[STEP 4/8] Grant Hive access to processed HDFS outputs"
hdfs dfs -chmod -R 777 "${HDFS_BASE}/processed"

echo "[STEP 5/8] Create Hive database and external tables for sample outputs"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  -e "CREATE DATABASE IF NOT EXISTS ${HIVE_DB};"

beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --hivevar db_name="${HIVE_DB}" \
  --hivevar hdfs_base="${HDFS_BASE}" \
  --hivevar table_prefix="${HIVE_TABLE_PREFIX}" \
  -f hive/create_tables.hql

echo "[STEP 6/8] Run Hive analysis queries"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --hivevar db_name="${HIVE_DB}" \
  --hivevar table_prefix="${HIVE_TABLE_PREFIX}" \
  -f hive/analysis_queries.hql

echo "[STEP 7/8] Export sample recommendation CSV"
beeline -u jdbc:hive2://localhost:10000 -n "${HIVE_USER}" \
  --silent=true \
  --showHeader=true \
  --outputformat=csv2 \
  -e "USE ${HIVE_DB}; SELECT region_name, genre, demand_index, recommendation_rank FROM ${HIVE_TABLE_PREFIX}region_genre_recommendations WHERE recommendation_rank <= 3 ORDER BY region_name, recommendation_rank;" \
  1> "${RESULT_CSV}"

echo "[STEP 8/8] Export sample report CSV files and upload to HDFS"
LOCAL_EXPORT_DIR="sample_exports" \
HDFS_EXPORT_DIR="${HDFS_BASE}/exports" \
bash scripts/export_hive_results.sh

echo "============================================================"
echo " HDFS sample smoke test finished"
echo " HDFS processed path: ${HDFS_BASE}/processed"
echo " Hive database      : ${HIVE_DB}"
echo " Hive table prefix  : ${HIVE_TABLE_PREFIX}"
echo " Result CSV         : ${RESULT_CSV}"
echo " HDFS exports path  : ${HDFS_BASE}/exports"
echo "============================================================"
