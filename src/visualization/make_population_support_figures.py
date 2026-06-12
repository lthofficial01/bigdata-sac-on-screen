"""
Create population-composition support figures for Q2 findings.

Default inputs:
    docs/genre_top_regions_excel.csv
    data/raw/population_age.csv

Default outputs:
    docs/figures/11_q2_group_population_age_composition.png
    docs/figures/12_q2_group_population_key_ratio.png
    docs/q2_population_group_summary.csv

Usage:
    python src/visualization/make_population_support_figures.py
"""

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rcParams


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


GROUP_A_GENRES = ["대중/복합", "무용", "뮤지컬"]
GROUP_B_GENRES = ["오페라", "클래식 기악", "클래식 성악"]

AGE_BANDS = {
    "age_0_19": ["2026년04월_계_0~9세", "2026년04월_계_10~19세"],
    "age_20_39": ["2026년04월_계_20~29세", "2026년04월_계_30~39세"],
    "age_40_59": ["2026년04월_계_40~49세", "2026년04월_계_50~59세"],
    "age_60_plus": [
        "2026년04월_계_60~69세",
        "2026년04월_계_70~79세",
        "2026년04월_계_80~89세",
        "2026년04월_계_90~99세",
        "2026년04월_계_100세 이상",
    ],
}

AGE_SHARE_COLUMNS = ["age_0_19_share", "age_20_39_share", "age_40_59_share", "age_60_plus_share"]
AGE_SHARE_LABELS = {
    "age_0_19_share": "0-19",
    "age_20_39_share": "20-39",
    "age_40_59_share": "40-59",
    "age_60_plus_share": "60+",
}


def setup_font() -> None:
    candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for font in candidates:
        if font in available:
            rcParams["font.family"] = font
            break
    rcParams["axes.unicode_minus"] = False


def to_number(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace('"', "", regex=False)
        .replace({"": "0", "nan": "0"})
        .astype(float)
    )


def short_region_name(region_name: str) -> str:
    replacements = {
        "서울특별시 ": "서울 ",
        "부산광역시 ": "부산 ",
        "대구광역시 ": "대구 ",
        "인천광역시 ": "인천 ",
        "광주광역시 ": "광주 ",
        "대전광역시 ": "대전 ",
        "울산광역시 ": "울산 ",
        "세종특별자치시": "세종",
        "경기도 ": "경기 ",
        "강원특별자치도 ": "강원 ",
        "충청북도 ": "충북 ",
        "충청남도 ": "충남 ",
        "전북특별자치도 ": "전북 ",
        "전라남도 ": "전남 ",
        "경상북도 ": "경북 ",
        "경상남도 ": "경남 ",
        "제주특별자치도 ": "제주 ",
    }
    shortened = str(region_name)
    for old, new in replacements.items():
        shortened = shortened.replace(old, new)
    return shortened


def read_top_regions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing top-region CSV: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    required = {"genre", "region_rank_in_genre", "region_name", "demand_index"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")

    df["region_rank_in_genre"] = pd.to_numeric(df["region_rank_in_genre"])
    df["demand_index"] = pd.to_numeric(df["demand_index"])
    return df.drop_duplicates(["genre", "region_name"], keep="first")


def read_population(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing population CSV: {path}. "
            "Place full raw data in data/raw/population_age.csv or pass --population-csv."
        )

    df = pd.read_csv(path, encoding="utf-8-sig")
    required_columns = {"행정구역", "2026년04월_계_총인구수"}
    for columns in AGE_BANDS.values():
        required_columns.update(columns)
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")

    region = df["행정구역"].astype(str)
    total = to_number(df["2026년04월_계_총인구수"])

    result = pd.DataFrame(
        {
            "region_code": region.str.extract(r"\((\d+)\)", expand=False),
            "region_name": region.str.replace(r"\s*\(\d+\)", "", regex=True).str.strip(),
            "total_population": total,
        }
    )

    for band, columns in AGE_BANDS.items():
        result[band] = sum(to_number(df[column]) for column in columns)
        result[f"{band}_share"] = result[band] / total * 100

    return result.drop_duplicates(["region_name"], keep="first")


def representative_regions(top_regions: pd.DataFrame, genres: list[str], limit: int = 5) -> list[str]:
    subset = top_regions[
        top_regions["genre"].isin(genres) & (top_regions["region_rank_in_genre"] <= 5)
    ].copy()
    ranked = (
        subset.groupby("region_name")
        .agg(
            appearance_count=("genre", "count"),
            best_rank=("region_rank_in_genre", "min"),
            avg_demand_index=("demand_index", "mean"),
        )
        .sort_values(
            ["appearance_count", "best_rank", "avg_demand_index"],
            ascending=[False, True, False],
        )
    )
    return list(ranked.head(limit).index)


def build_summary(
    population: pd.DataFrame,
    group_a_regions: list[str],
    group_b_regions: list[str],
) -> pd.DataFrame:
    rows = []
    for group_name, regions in [
        ("Group A: youth/dynamic genres", group_a_regions),
        ("Group B: senior/classical genres", group_b_regions),
    ]:
        group_pop = population[population["region_name"].isin(regions)].copy()
        missing = sorted(set(regions) - set(group_pop["region_name"]))
        if missing:
            print(f"[WARN] Missing population rows for {group_name}: {missing}")
        group_pop["group"] = group_name
        group_pop["short_region_name"] = group_pop["region_name"].map(short_region_name)
        rows.append(group_pop)

    if not rows:
        return pd.DataFrame()

    summary = pd.concat(rows, ignore_index=True)
    group_order = {"Group A: youth/dynamic genres": 0, "Group B: senior/classical genres": 1}
    summary["group_order"] = summary["group"].map(group_order)
    return summary.sort_values(["group_order", "region_name"]).drop(columns=["group_order"])


def save_population_composition(summary: pd.DataFrame, output_dir: Path) -> None:
    if summary.empty:
        return

    colors = {
        "age_0_19_share": "#6BAED6",
        "age_20_39_share": "#3182BD",
        "age_40_59_share": "#FDBF6F",
        "age_60_plus_share": "#E6550D",
    }

    groups = list(summary["group"].drop_duplicates())
    fig, axes = plt.subplots(1, len(groups), figsize=(7 * len(groups), 5.6), sharex=True)
    axes_list = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for ax, group_name in zip(axes_list, groups):
        subset = summary[summary["group"] == group_name].copy()
        labels = subset["short_region_name"]
        left = pd.Series([0.0] * len(subset), index=subset.index)
        for column in AGE_SHARE_COLUMNS:
            ax.barh(
                labels,
                subset[column],
                left=left,
                color=colors[column],
                label=AGE_SHARE_LABELS[column],
            )
            left += subset[column]

        ax.invert_yaxis()
        ax.set_title(group_name, fontsize=12, weight="bold")
        ax.set_xlabel("Age composition (%)")
        ax.grid(True, axis="x", alpha=0.3)
        ax.set_axisbelow(True)
        ax.set_xlim(0, 100)

    axes_list[-1].legend(title="Age group", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.suptitle("Age Composition of Top Demand Regions", fontsize=15, weight="bold")
    fig.tight_layout()
    fig.savefig(output_dir / "11_q2_group_population_age_composition.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_group_average_ratio(summary: pd.DataFrame, output_dir: Path) -> None:
    if summary.empty:
        return

    avg = summary.groupby("group")[AGE_SHARE_COLUMNS].mean().rename(columns=AGE_SHARE_LABELS)

    fig, ax = plt.subplots(figsize=(10, 5.4))
    avg.plot(kind="bar", ax=ax, color=["#6BAED6", "#3182BD", "#FDBF6F", "#E6550D"])
    ax.set_title("Average Age Composition by Demand Group", fontsize=15, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Average share (%)")
    ax.set_xticklabels(["Group A\nyouth/dynamic", "Group B\nsenior/classical"], rotation=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(title="Age group", bbox_to_anchor=(1.02, 1), loc="upper left")

    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=2, fontsize=8)

    fig.tight_layout()
    fig.savefig(output_dir / "12_q2_group_population_key_ratio.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create population support figures")
    parser.add_argument("--top-regions-csv", default="docs/genre_top_regions_excel.csv")
    parser.add_argument("--population-csv", default="data/raw/population_age.csv")
    parser.add_argument("--output-dir", default="docs/figures")
    parser.add_argument("--summary-csv", default="docs/q2_population_group_summary.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_font()

    output_dir = project_path(args.output_dir)
    summary_csv = project_path(args.summary_csv)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv.parent.mkdir(parents=True, exist_ok=True)

    top_regions = read_top_regions(project_path(args.top_regions_csv))
    population = read_population(project_path(args.population_csv))
    group_a_regions = representative_regions(top_regions, GROUP_A_GENRES)
    group_b_regions = representative_regions(top_regions, GROUP_B_GENRES)
    summary = build_summary(population, group_a_regions, group_b_regions)

    summary.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    save_population_composition(summary, output_dir)
    save_group_average_ratio(summary, output_dir)

    print(f"Figures written to {output_dir}")
    print(f"Summary written to {summary_csv}")


if __name__ == "__main__":
    main()
