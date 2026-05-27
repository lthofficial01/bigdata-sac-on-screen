"""
예술의전당 종합 공연정보 수집 스크립트
=============================================
문화데이터광장 (culture.go.kr) API를 통해 예술의전당 공연 메타데이터를 수집합니다.

출처: https://www.culture.go.kr/data/filedat/filedatDtl.do?fileDataNo=00000000000000000428

Usage:
    python collect_sac_performances.py --output_dir ../../data/raw/sac_performances/
"""

import os
import sys
import argparse
import requests
import pandas as pd
from datetime import datetime


def collect_sac_performances(api_key: str, output_dir: str) -> None:
    """
    예술의전당 종합 공연정보를 수집하여 CSV로 저장합니다.

    Parameters
    ----------
    api_key : str
        문화데이터광장 API 인증키
    output_dir : str
        수집 데이터 저장 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # TODO: 실제 API 엔드포인트 및 파라미터 확인 후 구현
    # 현재는 스켈레톤 구조만 제공
    base_url = "https://www.culture.go.kr/data/openapi/openapiView.do"

    params = {
        "seq": "428",
        "key": api_key,
        "type": "json",
    }

    print(f"[INFO] 예술의전당 공연정보 수집 시작: {datetime.now()}")

    # 실제 구현 시 페이지네이션 처리 필요
    # response = requests.get(base_url, params=params)
    # data = response.json()

    # 수집 결과 저장
    # df = pd.DataFrame(data)
    # output_path = os.path.join(output_dir, f"sac_performances_{datetime.now().strftime('%Y%m%d')}.csv")
    # df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[INFO] 수집 완료. 저장 경로: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="예술의전당 종합 공연정보 수집")
    parser.add_argument("--api_key", type=str, default=os.environ.get("CULTURE_API_KEY", ""),
                        help="문화데이터광장 API 인증키")
    parser.add_argument("--output_dir", type=str, default="../../data/raw/sac_performances/",
                        help="수집 데이터 저장 경로")
    args = parser.parse_args()

    collect_sac_performances(args.api_key, args.output_dir)
