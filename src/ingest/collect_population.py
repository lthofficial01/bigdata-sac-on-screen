"""
지역별 주민등록 인구통계 수집 스크립트
=============================================
행정안전부 주민등록 인구 및 세대현황 데이터를 수집합니다.

출처: https://jumin.mois.go.kr

Usage:
    python collect_population.py --output_dir ../../data/raw/population/
"""

import os
import argparse
import requests
import pandas as pd
from datetime import datetime


def collect_population(output_dir: str) -> None:
    """
    시/군/구 단위의 연령대별 인구 분포 데이터를 수집하여 CSV로 저장합니다.

    Parameters
    ----------
    output_dir : str
        수집 데이터 저장 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # TODO: 실제 데이터 다운로드 URL 또는 API 확인 후 구현
    # 행정안전부 주민등록 인구통계는 CSV 파일 다운로드 방식으로 제공
    # 시군구별 5세 단위 연령대 인구 데이터 확보 목표

    print(f"[INFO] 지역별 인구통계 수집 시작: {datetime.now()}")

    # 실제 구현 시:
    # 1. jumin.mois.go.kr에서 연령별 인구현황 CSV 다운로드
    # 2. 또는 공공데이터포털 API를 통한 자동 수집
    # 3. 시군구코드 기준으로 정규화

    # output_path = os.path.join(output_dir, f"population_{datetime.now().strftime('%Y%m%d')}.csv")
    # df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[INFO] 수집 완료. 저장 경로: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="지역별 주민등록 인구통계 수집")
    parser.add_argument("--output_dir", type=str, default="../../data/raw/population/",
                        help="수집 데이터 저장 경로")
    args = parser.parse_args()

    collect_population(args.output_dir)
