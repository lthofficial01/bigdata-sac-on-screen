"""
전국 문화기반시설 총람 수집 스크립트
=============================================
공공데이터포털에서 전국 문화기반시설(문화예술회관, 박물관, 미술관 등) 데이터를 수집합니다.

출처: https://www.data.go.kr/data/3075558/fileData.do

Usage:
    python collect_culture_facilities.py --output_dir ../../data/raw/culture_facilities/
"""

import os
import argparse
import requests
import pandas as pd
from datetime import datetime


def collect_culture_facilities(api_key: str, output_dir: str) -> None:
    """
    전국 문화기반시설 총람 데이터를 수집하여 CSV로 저장합니다.

    Parameters
    ----------
    api_key : str
        공공데이터포털 API 인증키
    output_dir : str
        수집 데이터 저장 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # TODO: 실제 API 엔드포인트 확인 후 구현
    # 공공데이터포털 파일 데이터 또는 REST API 활용

    print(f"[INFO] 전국 문화기반시설 총람 수집 시작: {datetime.now()}")

    # 실제 구현 시:
    # 1. 공공데이터포털에서 CSV 파일 다운로드
    # 2. 시설유형(문화예술회관, 공연장 등), 주소, 좌석수, 상영시설 유무 등 추출
    # 3. 시군구코드 매핑 및 정규화

    # output_path = os.path.join(output_dir, f"culture_facilities_{datetime.now().strftime('%Y%m%d')}.csv")
    # df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[INFO] 수집 완료. 저장 경로: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="전국 문화기반시설 총람 수집")
    parser.add_argument("--api_key", type=str, default=os.environ.get("DATA_GO_KR_API_KEY", ""),
                        help="공공데이터포털 API 인증키")
    parser.add_argument("--output_dir", type=str, default="../../data/raw/culture_facilities/",
                        help="수집 데이터 저장 경로")
    args = parser.parse_args()

    collect_culture_facilities(args.api_key, args.output_dir)
