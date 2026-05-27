#!/bin/bash
# ============================================================
# SAC on Screen: HDFS 데이터 업로드 스크립트
# ============================================================
# 로컬 data/raw/ 디렉토리의 수집 데이터를 HDFS에 적재합니다.
#
# Usage:
#   bash scripts/upload_to_hdfs.sh
# ============================================================

set -e

HDFS_BASE="/user/ubuntu/sac_on_screen"
LOCAL_DATA_DIR="$(dirname "$0")/../data/raw"

echo "============================================================"
echo "[INFO] SAC on Screen HDFS 데이터 업로드 시작"
echo "============================================================"

# HDFS 디렉토리 생성
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/sac_performances
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/sac_booking_age
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/sac_exhibitions
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/culture_facilities
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/population
hdfs dfs -mkdir -p ${HDFS_BASE}/raw/performance_index
hdfs dfs -mkdir -p ${HDFS_BASE}/processed

# 데이터 업로드
echo "[UPLOAD] 예술의전당 공연정보..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/sac_performances/* ${HDFS_BASE}/raw/sac_performances/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo "[UPLOAD] 예술의전당 연령대별 예매 건수..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/sac_booking_age/* ${HDFS_BASE}/raw/sac_booking_age/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo "[UPLOAD] 예술의전당 전시정보..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/sac_exhibitions/* ${HDFS_BASE}/raw/sac_exhibitions/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo "[UPLOAD] 전국 문화기반시설 총람..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/culture_facilities/* ${HDFS_BASE}/raw/culture_facilities/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo "[UPLOAD] 지역별 인구통계..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/population/* ${HDFS_BASE}/raw/population/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo "[UPLOAD] 공연예술 인덱스..."
hdfs dfs -put -f ${LOCAL_DATA_DIR}/performance_index/* ${HDFS_BASE}/raw/performance_index/ 2>/dev/null || echo "  -> 파일 없음 (수집 후 재실행)"

echo ""
echo "============================================================"
echo "[DONE] HDFS 업로드 완료. 적재 현황:"
echo "============================================================"
hdfs dfs -du -s -h ${HDFS_BASE}/raw/* 2>/dev/null || echo "  (HDFS 접속 불가 - HDP Sandbox 환경에서 실행하세요)"
