# 데이터 디렉토리 (Data Directory)

본 디렉토리는 프로젝트에서 사용하는 데이터의 구조와 출처를 설명합니다.
대용량 Raw 데이터는 `.gitignore`에 의해 Git 추적에서 제외되며, 실행 시 수집 스크립트를 통해 재생성할 수 있습니다.

## 디렉토리 구조

```
data/
├── README.md              # 본 파일
├── sample/                # Git에 포함되는 소량 샘플 데이터 (100~1000행)
│   ├── sac_performances_sample.csv
│   ├── sac_booking_by_age_sample.csv
│   ├── culture_facilities_sample.csv
│   └── population_by_region_sample.csv
├── raw/                   # (gitignored) 수집된 원본 데이터
│   ├── sac_performances/
│   ├── sac_booking_age/
│   ├── sac_exhibitions/
│   ├── culture_facilities/
│   ├── population/
│   └── performance_index/
└── processed/             # (gitignored) Spark 처리 후 Parquet 결과
    ├── age_preference_weights/
    ├── region_demand_index/
    └── optimal_locations/
```

## 데이터 출처 및 스키마 요약

| 데이터셋 | 출처 URL | 포맷 | 주요 컬럼 |
| :--- | :--- | :--- | :--- |
| 예술의전당 종합 공연정보 | culture.go.kr | CSV/JSON | 공연ID, 공연명, 장르, 키워드, 공연일시, 공연장 |
| 예술의전당 연령대별 예매 건수 | culture.go.kr | CSV/JSON | 공연ID, 연령대, 예매건수, 기간 |
| 예술의전당 전시정보 | culture.go.kr | CSV/JSON | 전시ID, 전시명, 기간, 장소 |
| 전국 문화기반시설 총람 | data.go.kr | CSV | 시설명, 주소, 시군구코드, 시설유형, 좌석수, 스크린유무 |
| 지역별 인구통계 | jumin.mois.go.kr | CSV | 시군구코드, 연령대, 인구수, 남녀비율 |
| 공연예술 인덱스 | bigdata-culture.kr | CSV/JSON | 지역코드, 관람빈도, 선호장르, 지수값 |

## HDFS 적재 경로

```
/user/ubuntu/sac_on_screen/raw/sac_performances/
/user/ubuntu/sac_on_screen/raw/sac_booking_age/
/user/ubuntu/sac_on_screen/raw/sac_exhibitions/
/user/ubuntu/sac_on_screen/raw/culture_facilities/
/user/ubuntu/sac_on_screen/raw/population/
/user/ubuntu/sac_on_screen/raw/performance_index/
/user/ubuntu/sac_on_screen/processed/
```

## 데이터 재수집 방법

```bash
# 전체 데이터 수집 (src/ingest/ 내 스크립트 순차 실행)
bash scripts/run_ingestion.sh

# HDFS 적재
bash scripts/upload_to_hdfs.sh
```
