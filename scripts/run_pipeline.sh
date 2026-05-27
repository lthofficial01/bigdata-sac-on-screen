#!/bin/bash
# ============================================================
# SAC on Screen: 전체 파이프라인 실행 스크립트
# ============================================================
# 데이터 수집 → HDFS 적재 → Spark 전처리 → Hive 테이블 생성 → 분석
# 전 과정을 순차적으로 실행합니다.
#
# Usage:
#   bash scripts/run_pipeline.sh
#
# Prerequisites:
#   - HDP Sandbox 환경 (HDFS, Spark, Hive 사용 가능)
#   - Python 3.x + 필요 패키지 설치 (pip install -r requirements.txt)
#   - API 키 환경변수 설정 (CULTURE_API_KEY, DATA_GO_KR_API_KEY)
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo " SAC on Screen 빅데이터 파이프라인"
echo " 프로젝트 루트: ${PROJECT_ROOT}"
echo "============================================================"
echo ""

# ---- STEP 1: 데이터 수집 ----
echo "[STEP 1/5] 데이터 수집 시작..."
python src/ingest/collect_sac_performances.py --output_dir data/raw/sac_performances/
python src/ingest/collect_sac_booking_age.py --output_dir data/raw/sac_booking_age/
python src/ingest/collect_population.py --output_dir data/raw/population/
python src/ingest/collect_culture_facilities.py --output_dir data/raw/culture_facilities/
echo "[STEP 1/5] 데이터 수집 완료."
echo ""

# ---- STEP 2: HDFS 적재 ----
echo "[STEP 2/5] HDFS 데이터 적재..."
bash scripts/upload_to_hdfs.sh
echo "[STEP 2/5] HDFS 적재 완료."
echo ""

# ---- STEP 3: Spark 전처리 ----
echo "[STEP 3/5] Spark 전처리 및 피처 엔지니어링..."
spark-submit --master yarn src/pipeline/spark_preprocess.py
echo "[STEP 3/5] Spark 전처리 완료."
echo ""

# ---- STEP 4: Hive 테이블 생성 ----
echo "[STEP 4/5] Hive External Table 생성..."
beeline -u jdbc:hive2://localhost:10000 -f hive/create_tables.hql
echo "[STEP 4/5] Hive 테이블 생성 완료."
echo ""

# ---- STEP 5: HiveQL 분석 ----
echo "[STEP 5/5] HiveQL 분석 쿼리 실행..."
beeline -u jdbc:hive2://localhost:10000 -f hive/analysis_queries.hql
echo "[STEP 5/5] 분석 완료."
echo ""

echo "============================================================"
echo " 전체 파이프라인 실행 완료!"
echo " 결과 확인: HDFS /user/ubuntu/sac_on_screen/processed/"
echo " 시각화: python src/visualization/dashboard.py"
echo "============================================================"
