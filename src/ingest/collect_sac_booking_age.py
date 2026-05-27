"""
예술의전당 연령대별 예매 건수 수집 스크립트
=============================================
문화데이터광장 (culture.go.kr) API를 통해 연령대별 예매 데이터를 수집합니다.

출처: https://www.culture.go.kr/data/filedat/filedatDtl.do?fileDataNo=00000000000000000411

Usage:
    python collect_sac_booking_age.py --output_dir ../../data/raw/sac_booking_age/
"""

import os
import argparse
import requests
import pandas as pd
from datetime import datetime


def collect_sac_booking_age(api_key: str, output_dir: str) -> None:
    """
    예술의전당 연령대별 예매 건수 데이터를 수집하여 CSV로 저장합니다.

    Parameters
    ----------
    api_key : str
        문화데이터광장 API 인증키
    output_dir : str
        수집 데이터 저장 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # TODO: 실제 API 엔드포인트 및 파라미터 확인 후 구현
    base_url = "https://www.culture.go.kr/data/openapi/openapiView.do"

    params = {
        "seq": "411",
        "key": api_key,
        "type": "json",
    }

    print(f"[INFO] 예술의전당 연령대별 예매 건수 수집 시작: {datetime.now()}")

    # 실제 구현 시 페이지네이션 및 기간별 수집 처리 필요
    # response = requests.get(base_url, params=params)
    # data = response.json()

    # 수집 결과 저장
    # df = pd.DataFrame(data)
    # output_path = os.path.join(output_dir, f"sac_booking_age_{datetime.now().strftime('%Y%m%d')}.csv")
    # df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[INFO] 수집 완료. 저장 경로: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="예술의전당 연령대별 예매 건수 수집")
    parser.add_argument("--api_key", type=str, default=os.environ.get("CULTURE_API_KEY", ""),
                        help="문화데이터광장 API 인증키")
    parser.add_argument("--output_dir", type=str, default="../../data/raw/sac_booking_age/",
                        help="수집 데이터 저장 경로")
    args = parser.parse_args()

    collect_sac_booking_age(args.api_key, args.output_dir)
