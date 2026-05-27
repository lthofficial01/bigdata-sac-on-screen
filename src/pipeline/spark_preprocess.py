"""
PySpark 전처리 및 피처 엔지니어링 스크립트
=============================================
HDFS에 적재된 Raw 데이터를 로드하여 연령대별 선호도 가중치 계산,
지역별 수요 지수(Demand Index) 산출 등의 핵심 분산 처리를 수행합니다.

Usage (HDP Sandbox):
    spark-submit --master yarn spark_preprocess.py

Usage (Local):
    spark-submit --master local[*] spark_preprocess.py --local
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def create_spark_session(app_name: str = "SACOnScreen_Preprocess", local: bool = False):
    """SparkSession 생성"""
    builder = SparkSession.builder.appName(app_name)
    if local:
        builder = builder.master("local[*]")
    return builder.enableHiveSupport().getOrCreate()


def compute_age_preference_weights(spark: SparkSession, booking_path: str, output_path: str):
    """
    연령대별 콘텐츠 선호도 가중치를 계산합니다.

    - 예술의전당 예매 데이터를 기반으로 장르별 연령대 예매 비중을 산출
    - 결과: (장르, 연령대, 예매비중, 선호도가중치) 형태의 Parquet

    Parameters
    ----------
    spark : SparkSession
    booking_path : str
        HDFS 상의 연령대별 예매 데이터 경로
    output_path : str
        결과 Parquet 저장 경로
    """
    # TODO: 실제 데이터 스키마에 맞춰 구현
    # df_booking = spark.read.csv(booking_path, header=True, inferSchema=True)

    # 장르별 전체 예매 건수 대비 연령대별 비중 계산
    # window_genre = Window.partitionBy("genre")
    # df_weights = df_booking.withColumn(
    #     "total_by_genre", F.sum("booking_count").over(window_genre)
    # ).withColumn(
    #     "preference_weight", F.col("booking_count") / F.col("total_by_genre")
    # )

    # df_weights.select("genre", "age_group", "booking_count", "preference_weight") \
    #     .write.mode("overwrite").parquet(output_path)

    print(f"[INFO] 연령대별 선호도 가중치 계산 완료 -> {output_path}")


def compute_region_demand_index(spark: SparkSession, population_path: str,
                                 preference_path: str, output_path: str):
    """
    지역별 잠재 수요 지수(Demand Index)를 산출합니다.

    - 지역 인구 구조(연령 분포)와 연령대별 콘텐츠 선호도 가중치를 결합
    - 결과: (시군구코드, 장르, demand_index) 형태의 Parquet

    Parameters
    ----------
    spark : SparkSession
    population_path : str
        HDFS 상의 지역별 인구 데이터 경로
    preference_path : str
        연령대별 선호도 가중치 Parquet 경로
    output_path : str
        결과 Parquet 저장 경로
    """
    # TODO: 실제 데이터 스키마에 맞춰 구현
    # df_pop = spark.read.csv(population_path, header=True, inferSchema=True)
    # df_pref = spark.read.parquet(preference_path)

    # 지역 인구 비율 × 선호도 가중치 = 잠재 수요 지수
    # df_joined = df_pop.join(df_pref, on="age_group", how="inner")
    # df_demand = df_joined.groupBy("region_code", "genre").agg(
    #     F.sum(F.col("population") * F.col("preference_weight")).alias("demand_index")
    # )

    # df_demand.write.mode("overwrite").parquet(output_path)

    print(f"[INFO] 지역별 수요 지수 산출 완료 -> {output_path}")


def compute_optimal_locations(spark: SparkSession, demand_path: str,
                               facilities_path: str, output_path: str):
    """
    문화 사각지대 내 최적 상영 입지를 도출합니다.

    - 잠재 수요 지수가 높으면서 기존 문화 시설 접근성이 낮은 지역을 우선 선정
    - 해당 지역 내 상영 가능 시설(스크린, 음향 설비 보유)을 매칭

    Parameters
    ----------
    spark : SparkSession
    demand_path : str
        지역별 수요 지수 Parquet 경로
    facilities_path : str
        HDFS 상의 문화기반시설 데이터 경로
    output_path : str
        결과 Parquet 저장 경로
    """
    # TODO: 실제 데이터 스키마에 맞춰 구현
    # df_demand = spark.read.parquet(demand_path)
    # df_facilities = spark.read.csv(facilities_path, header=True, inferSchema=True)

    # 시설 접근성 점수 계산 (시설 수, 좌석 수 등)
    # 수요 지수 대비 접근성이 낮은 지역 = 문화 사각지대
    # 최적 입지 = 수요 높음 + 접근성 낮음 + 상영 가능 시설 존재

    # df_optimal.write.mode("overwrite").parquet(output_path)

    print(f"[INFO] 최적 상영 입지 도출 완료 -> {output_path}")


def main(local: bool = False):
    """메인 파이프라인 실행"""
    spark = create_spark_session(local=local)

    # HDFS 경로 설정
    base_path = "/user/ubuntu/sac_on_screen"
    raw_path = f"{base_path}/raw"
    processed_path = f"{base_path}/processed"

    print("=" * 60)
    print("[STEP 1] 연령대별 콘텐츠 선호도 가중치 계산")
    print("=" * 60)
    compute_age_preference_weights(
        spark,
        booking_path=f"{raw_path}/sac_booking_age/",
        output_path=f"{processed_path}/age_preference_weights/"
    )

    print("=" * 60)
    print("[STEP 2] 지역별 잠재 수요 지수 산출")
    print("=" * 60)
    compute_region_demand_index(
        spark,
        population_path=f"{raw_path}/population/",
        preference_path=f"{processed_path}/age_preference_weights/",
        output_path=f"{processed_path}/region_demand_index/"
    )

    print("=" * 60)
    print("[STEP 3] 최적 상영 입지 도출")
    print("=" * 60)
    compute_optimal_locations(
        spark,
        demand_path=f"{processed_path}/region_demand_index/",
        facilities_path=f"{raw_path}/culture_facilities/",
        output_path=f"{processed_path}/optimal_locations/"
    )

    spark.stop()
    print("\n[DONE] 전체 Spark 전처리 파이프라인 완료.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAC on Screen Spark 전처리 파이프라인")
    parser.add_argument("--local", action="store_true", help="로컬 모드 실행")
    args = parser.parse_args()

    main(local=args.local)
