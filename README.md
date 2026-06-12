# SAC on Screen 지역 장르 추천 지표

예술의전당 일반 공연 예매 패턴과 시군구별 연령 인구구조를 결합해, SAC on Screen 콘텐츠의 지역별 장르 추천 지표를 산출하는 빅데이터 처리 프로젝트입니다.

## 문제 정의

SAC(Seoul Arts Center) on Screen은 예술의전당 공연 콘텐츠를 영상화하여 지역 상영처 등 다양한 채널로 제공하는 공연 영상화 사업입니다. 지역마다 연령 인구구조가 다르고, 연령대별 공연 장르 선호도도 다를 수 있으므로 지역별 특성을 반영한 콘텐츠 편성 기준이 필요합니다.

본 프로젝트는 SAC on Screen의 실제 시청 로그를 직접 분석하지 않습니다. 대신 예술의전당 일반 공연의 나이대별 예매 건수에서 장르별 연령 선호 패턴을 추정하고, 이를 시군구별 연령 인구구조와 결합해 지역별 장르 적합도와 추천 순위를 계산합니다.

핵심 분석 질문은 다음과 같습니다.

1. 연령대별로 어떤 공연 장르 선호 차이가 나타나는가?
2. 시군구별 연령 인구구조를 반영하면 장르별 잠재 수요는 어떻게 달라지는가?
3. 각 시군구에 우선 추천할 SAC on Screen 장르 Top 3는 무엇인가?

## 데이터

| 데이터 | 주요 컬럼 | 활용 목적 |
| --- | --- | --- |
| 예술의전당 종합 공연정보 | `TITLE`, `GENRE`, `PERIOD`, `URL` | 공연 제목과 장르 정보 확보 |
| 예술의전당 나이대별 예매 건수 | `TITLE`, `PERIOD`, `RELATION` | 공연별 연령대 예매 건수 파악 |
| 주민등록 연령별 인구현황 | `행정구역`, 연령대별 인구 컬럼 | 시군구별 연령 인구구조 파악 |

대용량 원본 데이터는 GitHub에 포함하지 않습니다. 전체 분석에 필요한 원본 CSV 파일명, HDFS 업로드 위치, 최소 스키마는 `data/README.md`를 참고하면 됩니다.

저장소에는 실행 구조와 입력 스키마를 확인하기 위한 sample 데이터만 포함되어 있습니다.

```text
data/sample/
├── sac_performances_sample.csv
├── sac_booking_age_sample.csv
└── population_age_sample.csv
```

sample 데이터는 최종 결과 재현용이 아니라 Spark/Hive 처리 흐름을 빠르게 확인하기 위한 소규모 데이터입니다.

## 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| 저장소 | HDFS |
| 분산 처리 | Apache Spark, PySpark |
| 분석 질의 | Apache Hive, HiveQL, Beeline |
| 저장 포맷 | CSV raw, Parquet processed |
| 자동화 | Bash scripts |
| 시각화 | Python, Matplotlib |

## 처리 흐름

```text
HDFS raw CSV
  -> Spark preprocessing
  -> HDFS processed Parquet
  -> Hive External Table
  -> HiveQL analysis
  -> CSV export / visualization / report
```

Spark 처리 결과는 세 가지 주요 산출물로 구성됩니다.

| 산출물 물리명 | 산출물 논리명 | 의미 |
| --- | --- | --- |
| `age_preference_weights` | 연령대 x 장르 선호 가중치 | 예매 데이터를 기반으로 연령대별 장르 선호도를 정량화 |
| `region_demand_index` | 시군구 x 장르 수요지수 | 연령별 인구구조와 장르 선호 가중치를 결합해 지역별 장르 적합도 계산 |
| `region_genre_recommendations` | 시군구별 추천 장르 Top 3 | 수요지수가 높은 순서대로 지역별 추천 장르 순위 부여 |

## 실행 방법

HDP Sandbox 환경에서 HDFS, Spark, HiveServer2가 실행 중인 상태를 기준으로 합니다.

처음 실행하는 환경이라면 HDFS 사용자 디렉터리를 준비합니다.

```bash
sudo -u hdfs hdfs dfs -mkdir -p /user/maria_dev
sudo -u hdfs hdfs dfs -chown -R maria_dev:hdfs /user/maria_dev
```

원본 CSV 3개는 프로젝트 폴더가 아니라 HDFS raw 경로에 업로드합니다. 자세한 파일명과 데이터 설명은 `data/README.md`에 정리되어 있습니다.

```text
/user/maria_dev/sac_on_screen/raw/
├── sac_performances.csv
├── sac_booking_age.csv
└── population_age.csv
```

HDFS 업로드 상태를 확인합니다.

```bash
hdfs dfs -ls -h /user/maria_dev/sac_on_screen/raw
```

프로젝트 루트에서 전체 파이프라인을 실행합니다.

```bash
bash scripts/run_pipeline.sh
```

`scripts/run_pipeline.sh`는 원본 CSV 확인, PySpark 전처리, Hive External Table 생성, 분석 쿼리 실행, 결과 CSV 추출을 순서대로 수행합니다.

## Sample 실행

원본 데이터 없이 파이프라인 구조만 확인하려면 sample 실행 스크립트를 사용할 수 있습니다.

```bash
bash scripts/run_hdfs_sample_pipeline.sh
```

sample 실행은 full raw pipeline과 충돌하지 않도록 별도 HDFS 경로와 테이블 prefix를 사용합니다.

```text
HDFS path: /user/maria_dev/sac_on_screen_sample
Hive DB: default
Hive tables:
  sac_sample_age_preference_weights
  sac_sample_region_demand_index
  sac_sample_region_genre_recommendations
```

HDP 환경에서 Python 실행 파일 이름이 다르면 직접 지정해서 실행할 수 있습니다.

```bash
PYSPARK_PYTHON=python3.6 \
PYSPARK_DRIVER_PYTHON=python3.6 \
bash scripts/run_hdfs_sample_pipeline.sh
```

## 주요 파일

```text
scripts/run_pipeline.sh             # full raw HDFS/Spark/Hive pipeline
scripts/run_hdfs_sample_pipeline.sh # sample HDFS/Spark/Hive pipeline
scripts/export_hive_results.sh      # Hive 결과 CSV export
src/pipeline/spark_preprocess.py    # PySpark 전처리 및 추천 지표 계산
hive/create_tables.hql              # Hive External Table DDL
hive/analysis_queries.hql           # 분석 쿼리
src/visualization/                  # 결과 시각화 스크립트
data/README.md                      # 원본 데이터 준비 안내
data/sample/                        # sample CSV
docs/                               # 결과 CSV 및 보고서용 이미지
```

## 결과 CSV

Spark 처리 결과는 HDFS processed 경로에 Parquet 형식으로 저장하고, Hive External Table로 등록해 SQL로 조회합니다. 주요 분석 결과는 Beeline을 통해 CSV로 추출합니다.

| CSV 파일 | 원천 Hive 결과 | 용도 |
| --- | --- | --- |
| `docs/age_preference_weights_excel.csv` | `age_preference_weights` | 연령대별 장르 선호 차이 분석 |
| `docs/genre_top_regions_excel.csv` | `region_demand_index` 기반 분석 쿼리 | 장르별 수요지수 상위 지역 분석 |
| `docs/region_genre_recommendations_excel.csv` | `region_genre_recommendations` | 시군구별 추천 장르 Top 3 최종 결과 |

## 결과 해석

최종 결과인 `region_genre_recommendations`는 각 시군구에서 장르별 `demand_index`를 계산하고, 높은 순서대로 추천 순위를 부여한 데이터입니다.

예시:

| region_name | genre | demand_index | recommendation_rank |
| --- | --- | ---: | ---: |
| 강원특별자치도 강릉시 | 클래식 | 0.6528713859712318 | 1 |
| 강원특별자치도 강릉시 | 무용 | 0.14505042121826417 | 2 |
| 강원특별자치도 강릉시 | 뮤지컬 | 0.13770804611625515 | 3 |

이 결과는 실제 SAC on Screen 시청 수요 예측값이 아니라, 예술의전당 일반 공연 예매 패턴과 지역 인구구조를 결합한 잠재적 장르 적합도 지표입니다.

## 한계와 개선 방향

- SAC on Screen 실제 시청 로그가 없어 일반 공연 예매 데이터를 대리 변수로 사용했습니다.
- 지역별 장르 추천은 연령 인구구조 중심이며, 소득, 교통, 문화시설 접근성은 반영하지 않았습니다.
- 공연 제목 기반 조인은 표기 차이에 민감할 수 있습니다.
- 향후 문화시설 데이터와 결합하면 지역 상영처 단위 추천으로 확장할 수 있습니다.

## AI 도구 사용

- Codex: 코드 디버깅, README/보고서 문서화 보조
- ChatGPT: 아이디어 구체화
- Claude: 보고서 작성 보조, 시각화
