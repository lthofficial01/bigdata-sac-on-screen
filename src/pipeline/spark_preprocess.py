"""
PySpark preprocessing pipeline for SAC on Screen genre recommendations.

This MVP recommends SAC on Screen genres at the Si/Gun/Gu level. It does not
rank individual facilities.

Usage (HDP Sandbox):
    spark-submit --master yarn src/pipeline/spark_preprocess.py

Usage (Local):
    spark-submit --master local[*] src/pipeline/spark_preprocess.py --local
"""

import argparse
from pathlib import Path
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


AGE_GROUPS = [
    "10대 이하",
    "20대",
    "30대",
    "40대",
    "50대",
    "60대",
    "70대 이상",
]

CLASSIC_INSTRUMENTAL_GENRES = [
    "클래식",
    "독주",
    "실내악",
    "교향곡",
]

CLASSIC_VOCAL_GENRES = [
    "성악",
    "합창",
]

POPULAR_COMPLEX_GENRES = [
    "콘서트",
    "재즈",
    "크로스오버",
]

PERFORMANCE_CSV = "sac_performances.csv"
BOOKING_CSV = "sac_booking_age.csv"
POPULATION_CSV = "population_age.csv"


def create_spark_session(app_name: str = "SACOnScreen_GenreRecommendation", local: bool = False):
    """Create a SparkSession with Hive support."""
    builder = SparkSession.builder.appName(app_name)
    if local:
        builder = (
            builder.master("local[1]")
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.sql.shuffle.partitions", "4")
        )
        return builder.getOrCreate()
    return builder.enableHiveSupport().getOrCreate()


def read_csv(spark: SparkSession, path: str):
    """Read CSV files with options that fit the supplied public data files."""
    return (
        spark.read.option("header", True)
        .option("encoding", "UTF-8")
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .option("maxColumns", 10000)
        .csv(path)
    )


def normalize_title(column):
    return F.lower(F.regexp_replace(F.trim(column), r"\s+", " "))


def numeric_string_to_long(column):
    cleaned = F.regexp_replace(F.coalesce(column.cast("string"), F.lit("0")), r"[^0-9]", "")
    return F.when(cleaned == "", F.lit(0)).otherwise(cleaned.cast("long"))


def map_sac_genre(column):
    return (
        F.when(column == "오페라", F.lit("오페라"))
        .when(column == "뮤지컬", F.lit("뮤지컬"))
        .when(column.isin("무용", "발레"), F.lit("무용"))
        .when(column.isin(*CLASSIC_INSTRUMENTAL_GENRES), F.lit("클래식 기악"))
        .when(column.isin(*CLASSIC_VOCAL_GENRES), F.lit("클래식 성악"))
        .when(column.isin(*POPULAR_COMPLEX_GENRES), F.lit("대중/복합"))
    )


def write_outputs(df, parquet_path: str, csv_path: Optional[str] = None):
    df.write.mode("overwrite").parquet(parquet_path)
    if csv_path:
        df.coalesce(1).write.mode("overwrite").option("header", True).csv(csv_path)


def load_performance_genres(spark: SparkSession, performance_path: str):
    df = read_csv(spark, performance_path)
    return (
        df.select(
            normalize_title(F.col("TITLE")).alias("title_key"),
            map_sac_genre(F.trim(F.col("GENRE"))).alias("genre"),
        )
        .filter(F.col("title_key").isNotNull() & F.col("genre").isNotNull())
        .dropDuplicates(["title_key"])
    )


def compute_age_preference_weights(
    spark: SparkSession,
    performance_path: str,
    booking_path: str,
    output_path: str,
    csv_output_path: Optional[str] = None,
):
    """
    Compute age-group genre preference weights.

    W(age, genre) = booking_count(age, genre) / total_booking_count(age)
    """
    performance_genres = load_performance_genres(spark, performance_path)
    booking = read_csv(spark, booking_path).select(
        normalize_title(F.col("TITLE")).alias("title_key"),
        F.col("RELATION").alias("age_booking_text"),
    )

    age_structs = []
    for age_group in AGE_GROUPS:
        count_expr = numeric_string_to_long(
            F.regexp_extract(
                F.col("age_booking_text"),
                rf"{age_group}\s*:\s*([0-9,]+)건",
                1,
            )
        )
        age_structs.append(
            F.struct(F.lit(age_group).alias("age_group"), count_expr.alias("booking_count"))
        )

    booking_long = (
        booking.select("title_key", F.explode(F.array(*age_structs)).alias("age_booking"))
        .select(
            "title_key",
            F.col("age_booking.age_group").alias("age_group"),
            F.col("age_booking.booking_count").alias("booking_count"),
        )
        .filter(F.col("booking_count") > 0)
    )

    joined = booking_long.join(performance_genres, on="title_key", how="inner")

    genre_age_counts = joined.groupBy("age_group", "genre").agg(
        F.sum("booking_count").alias("booking_count")
    )

    window_age = Window.partitionBy("age_group")
    weights = (
        genre_age_counts.withColumn("total_by_age", F.sum("booking_count").over(window_age))
        .withColumn("preference_weight", F.col("booking_count") / F.col("total_by_age"))
        .select("genre", "age_group", "booking_count", "preference_weight")
        .orderBy("age_group", F.desc("preference_weight"))
    )

    write_outputs(weights, output_path, csv_output_path)
    print(f"[INFO] age preference weights written -> {output_path}")


def compute_region_demand_index(
    spark: SparkSession,
    population_path: str,
    preference_path: str,
    output_path: str,
    csv_output_path: Optional[str] = None,
):
    """
    Compute regional genre demand index.

    Demand(region, genre) = SUM population(region, age) * W(age, genre)
    """
    population = read_csv(spark, population_path)
    # Spark 2 on HDP can mangle the first Korean header character. The region
    # field is the first population CSV column in both sample and raw inputs.
    region_column = F.col(population.columns[0])

    base = (
        population.select(
            F.regexp_extract(region_column, r"\((\d+)\)", 1).alias("region_code"),
            F.trim(F.regexp_replace(region_column, r"\s*\(\d+\)", "")).alias("region_name"),
            (numeric_string_to_long(F.col("2026년04월_계_0~9세")) + numeric_string_to_long(F.col("2026년04월_계_10~19세"))).alias("10대 이하"),
            numeric_string_to_long(F.col("2026년04월_계_20~29세")).alias("20대"),
            numeric_string_to_long(F.col("2026년04월_계_30~39세")).alias("30대"),
            numeric_string_to_long(F.col("2026년04월_계_40~49세")).alias("40대"),
            numeric_string_to_long(F.col("2026년04월_계_50~59세")).alias("50대"),
            numeric_string_to_long(F.col("2026년04월_계_60~69세")).alias("60대"),
            (
                numeric_string_to_long(F.col("2026년04월_계_70~79세"))
                + numeric_string_to_long(F.col("2026년04월_계_80~89세"))
                + numeric_string_to_long(F.col("2026년04월_계_90~99세"))
                + numeric_string_to_long(F.col("2026년04월_계_100세 이상"))
            ).alias("70대 이상"),
        )
        .filter(F.col("region_code") != "")
        .filter((~F.col("region_code").rlike(r"^\d{2}0{8}$")) | F.col("region_name").startswith("세종"))
    )

    age_structs = [
        F.struct(F.lit(age_group).alias("age_group"), F.col(age_group).alias("population"))
        for age_group in AGE_GROUPS
    ]

    population_long = (
        base.select("region_code", "region_name", F.explode(F.array(*age_structs)).alias("age_population"))
        .select(
            "region_code",
            "region_name",
            F.col("age_population.age_group").alias("age_group"),
            F.col("age_population.population").alias("population"),
        )
        .filter(F.col("population") > 0)
    )

    preferences = spark.read.parquet(preference_path).select(
        "age_group", "genre", "preference_weight"
    )

    demand = (
        population_long.join(preferences, on="age_group", how="inner")
        .withColumn("weighted_population", F.col("population") * F.col("preference_weight"))
        .groupBy("region_code", "region_name", "genre")
        .agg(
            F.sum("weighted_population").alias("weighted_population"),
            F.sum("population").alias("total_population"),
        )
        .withColumn("demand_index", F.col("weighted_population") / F.col("total_population"))
        .select("region_code", "region_name", "genre", "demand_index")
        .orderBy("region_name", F.desc("demand_index"))
    )

    write_outputs(demand, output_path, csv_output_path)
    print(f"[INFO] region demand index written -> {output_path}")


def compute_region_genre_recommendations(
    spark: SparkSession,
    demand_path: str,
    output_path: str,
    csv_output_path: Optional[str] = None,
):
    """
    Rank recommended SAC on Screen genres for each region.

    Expected output columns:
        region_code, region_name, genre, demand_index, recommendation_rank
    """
    df_demand = spark.read.parquet(demand_path)
    window_region = Window.partitionBy("region_code").orderBy(F.desc("demand_index"))
    recommendations = (
        df_demand.withColumn("recommendation_rank", F.row_number().over(window_region))
        .select("region_code", "region_name", "genre", "demand_index", "recommendation_rank")
        .orderBy("region_name", "recommendation_rank")
    )

    write_outputs(recommendations, output_path, csv_output_path)
    print(f"[INFO] region genre recommendations written -> {output_path}")


def main(
    local: bool = False,
    base_path: str = "/user/maria_dev/sac_on_screen",
    performance_path: Optional[str] = None,
    booking_path: Optional[str] = None,
    population_path: Optional[str] = None,
):
    """Run the MVP preprocessing pipeline."""
    spark = create_spark_session(local=local)

    if local:
        raw_path = "data/raw"
        processed_path = "data/processed"
        csv_path = "data/processed_csv"
        performance_path = performance_path or str(Path(raw_path) / PERFORMANCE_CSV)
        booking_path = booking_path or str(Path(raw_path) / BOOKING_CSV)
        population_path = population_path or str(Path(raw_path) / POPULATION_CSV)
    else:
        raw_path = f"{base_path}/raw"
        processed_path = f"{base_path}/processed"
        csv_path = None
        performance_path = performance_path or f"{raw_path}/{PERFORMANCE_CSV}"
        booking_path = booking_path or f"{raw_path}/{BOOKING_CSV}"
        population_path = population_path or f"{raw_path}/{POPULATION_CSV}"

    print("=" * 60)
    print("[STEP 1] Compute age-group genre preference weights")
    print("=" * 60)
    compute_age_preference_weights(
        spark,
        performance_path=performance_path,
        booking_path=booking_path,
        output_path=f"{processed_path}/age_preference_weights/",
        csv_output_path=f"{csv_path}/age_preference_weights/" if csv_path else None,
    )

    print("=" * 60)
    print("[STEP 2] Compute region-level genre demand index")
    print("=" * 60)
    compute_region_demand_index(
        spark,
        population_path=population_path,
        preference_path=f"{processed_path}/age_preference_weights/",
        output_path=f"{processed_path}/region_demand_index/",
        csv_output_path=f"{csv_path}/region_demand_index/" if csv_path else None,
    )

    print("=" * 60)
    print("[STEP 3] Rank recommended genres by region")
    print("=" * 60)
    compute_region_genre_recommendations(
        spark,
        demand_path=f"{processed_path}/region_demand_index/",
        output_path=f"{processed_path}/region_genre_recommendations/",
        csv_output_path=f"{csv_path}/region_genre_recommendations/" if csv_path else None,
    )

    spark.stop()
    print("\n[DONE] Spark preprocessing pipeline finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAC on Screen genre recommendation pipeline")
    parser.add_argument("--local", action="store_true", help="Run in local Spark mode")
    parser.add_argument(
        "--base-path",
        type=str,
        default="/user/maria_dev/sac_on_screen",
        help="HDFS project base path",
    )
    parser.add_argument("--performance-path", type=str, default=None, help="Performance CSV path")
    parser.add_argument("--booking-path", type=str, default=None, help="Age booking CSV path")
    parser.add_argument("--population-path", type=str, default=None, help="Population CSV path")
    args = parser.parse_args()

    main(
        local=args.local,
        base_path=args.base_path,
        performance_path=args.performance_path,
        booking_path=args.booking_path,
        population_path=args.population_path,
    )
