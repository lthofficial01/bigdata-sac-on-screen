"""
Create report and presentation figures from exported Hive CSV files.

Default inputs:
    docs/region_genre_recommendations_excel.csv
    docs/age_preference_weights_excel.csv
    docs/genre_top_regions_excel.csv

Default output:
    docs/figures/

Usage:
    python src/visualization/make_report_figures.py
"""

import argparse
from io import StringIO
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rcParams


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


AGE_ORDER = ["10대 이하", "20대", "30대", "40대", "50대", "60대", "70대 이상"]
GROUP_A_GENRES = ["대중/복합", "무용", "뮤지컬"]
GROUP_B_GENRES = ["오페라", "클래식 기악", "클래식 성악"]


def setup_font() -> None:
    candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {font.name for font in font_manager.fontManager.ttflist}
    for font in candidates:
        if font in available:
            rcParams["font.family"] = font
            break
    rcParams["axes.unicode_minus"] = False


def read_beeline_csv(path: Path, required_columns: Iterable[str]) -> pd.DataFrame:
    required = list(required_columns)
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")

    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_index = None
    for idx, line in enumerate(lines):
        columns = [part.strip() for part in line.split(",")]
        if all(column in columns for column in required):
            header_index = idx
            break

    if header_index is None:
        raise ValueError(f"Cannot find CSV header in {path}")

    return pd.read_csv(StringIO("\n".join(lines[header_index:])))


def resolve_csv(input_dir: Path, file_name: str) -> Path:
    path = input_dir / file_name
    if path.exists():
        return path

    stem = Path(file_name).stem
    excel_path = input_dir / f"{stem}_excel.csv"
    if excel_path.exists():
        return excel_path

    return path


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


def save_rank_distribution(recommendations: pd.DataFrame, output_dir: Path) -> None:
    top3 = recommendations[recommendations["recommendation_rank"] <= 3]
    dist = (
        top3.groupby(["recommendation_rank", "genre"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    dist.plot(kind="bar", ax=ax)
    ax.set_title("Genre Distribution by Recommendation Rank")
    ax.set_xlabel("Recommendation rank")
    ax.set_ylabel("Number of regions")
    ax.set_xticklabels([f"Rank {int(rank)}" for rank in dist.index], rotation=0)
    ax.legend(title="Genre", bbox_to_anchor=(1.02, 1), loc="upper left")
    for container in ax.containers:
        ax.bar_label(container, padding=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "01_rank_genre_distribution.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_rank1_distribution(recommendations: pd.DataFrame, output_dir: Path) -> None:
    rank1 = recommendations[recommendations["recommendation_rank"] == 1]
    counts = rank1["genre"].value_counts().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    counts.plot(kind="bar", ax=ax, color="#2F5597")
    ax.set_title("Rank 1 Genre Distribution")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Number of regions")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")
    for idx, value in enumerate(counts.values):
        ax.text(idx, value + max(counts.values) * 0.02, str(value), ha="center")
    ax.set_ylim(0, max(counts.values) * 1.18)
    fig.tight_layout()
    fig.savefig(output_dir / "02_rank1_genre_distribution.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_selected_region_comparison(recommendations: pd.DataFrame, output_dir: Path) -> None:
    rank1 = recommendations[recommendations["recommendation_rank"] == 1].sort_values(
        "demand_index", ascending=False
    )
    if len(rank1) < 3:
        return

    selected_regions = [
        rank1.iloc[0]["region_name"],
        rank1.iloc[len(rank1) // 2]["region_name"],
        rank1.iloc[-1]["region_name"],
    ]
    selected = recommendations[
        recommendations["region_name"].isin(selected_regions)
        & (recommendations["recommendation_rank"] <= 3)
    ]
    pivot = selected.pivot_table(
        index="region_name", columns="genre", values="demand_index", aggfunc="first"
    ).fillna(0)
    pivot = pivot.reindex(selected_regions)

    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Top 3 Genre Demand Index by Selected Region")
    ax.set_xlabel("Region")
    ax.set_ylabel("demand_index")
    ax.set_xticklabels([short_region_name(label.get_text()) for label in ax.get_xticklabels()], rotation=20, ha="right")
    ax.legend(title="Genre", bbox_to_anchor=(1.02, 1), loc="upper left")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", padding=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "03_selected_region_top3_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_top_regions_by_genre(top_regions: pd.DataFrame, output_dir: Path) -> None:
    if top_regions.empty:
        return

    data = top_regions.copy()
    data = data[data["region_rank_in_genre"] <= 10].sort_values(
        ["genre", "region_rank_in_genre"], ascending=[True, False]
    )
    data["label"] = data["genre"] + " | " + data["region_name"].map(short_region_name)

    fig, ax = plt.subplots(figsize=(10, max(5.5, len(data) * 0.22)))
    ax.barh(data["label"], data["demand_index"], color="#4472C4")
    ax.set_title("Top Demand Regions by Genre")
    ax.set_xlabel("demand_index")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(output_dir / "04_top_regions_by_genre.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_age_preference_heatmap(preferences: pd.DataFrame, output_dir: Path) -> None:
    pivot = (
        preferences.pivot_table(
            index="age_group", columns="genre", values="preference_weight", aggfunc="sum"
        )
        .reindex(AGE_ORDER)
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(9, 4.8))
    image = ax.imshow(pivot.values, aspect="auto", cmap="Blues")
    ax.set_title("Age Group Preference Weight by Genre")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=25, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for row_idx in range(pivot.shape[0]):
        for col_idx in range(pivot.shape[1]):
            ax.text(
                col_idx,
                row_idx,
                f"{pivot.iat[row_idx, col_idx]:.3f}",
                ha="center",
                va="center",
                fontsize=8,
            )
    fig.colorbar(image, ax=ax, label="preference_weight")
    fig.tight_layout()
    fig.savefig(output_dir / "05_age_preference_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_top1_region_by_genre(top_regions: pd.DataFrame, output_dir: Path) -> None:
    top1 = top_regions[top_regions["region_rank_in_genre"] == 1].copy()
    if top1.empty:
        return

    top1 = top1.sort_values("demand_index", ascending=False)
    labels = top1["genre"] + "\n" + top1["region_name"].map(short_region_name)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    bars = ax.bar(labels, top1["demand_index"], color="#4472C4")
    ax.set_title("Highest Demand Region by Genre")
    ax.set_xlabel("Genre and top region")
    ax.set_ylabel("demand_index")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.3f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "06_top1_region_by_genre.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_top5_region_panels(top_regions: pd.DataFrame, output_dir: Path) -> None:
    genres = list(top_regions["genre"].drop_duplicates())
    if not genres:
        return

    ncols = 3
    nrows = (len(genres) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 4.2 * nrows))
    axes_list = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for ax, genre in zip(axes_list, genres):
        subset = (
            top_regions[
                (top_regions["genre"] == genre)
                & (top_regions["region_rank_in_genre"] <= 5)
            ]
            .sort_values("region_rank_in_genre", ascending=False)
            .copy()
        )
        ax.barh(subset["region_name"].map(short_region_name), subset["demand_index"], color="#4472C4")
        ax.set_title(genre)
        ax.set_xlabel("demand_index")
        ax.set_ylabel("")
        for idx, value in enumerate(subset["demand_index"]):
            ax.text(value, idx, f"{value:.3f}", va="center", fontsize=8)

    for ax in axes_list[len(genres) :]:
        ax.axis("off")

    fig.suptitle("Top 5 Demand Regions by Genre", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "07_top5_region_panels_by_genre.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_age_preference_line_trend(preferences: pd.DataFrame, output_dir: Path) -> None:
    pivot = (
        preferences.pivot_table(
            index="age_group", columns="genre", values="preference_weight", aggfunc="sum"
        )
        .reindex(AGE_ORDER)
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    for genre in pivot.columns:
        ax.plot(pivot.index, pivot[genre] * 100, marker="o", linewidth=2.0, label=genre)

    ax.set_title("Age Group Preference Trend by Genre")
    ax.set_xlabel("Age group")
    ax.set_ylabel("Preference share (%)")
    ax.grid(True, axis="both", alpha=0.35)
    ax.legend(title="Genre", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(output_dir / "08_age_preference_trend_line.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_group_panels(
    top_regions: pd.DataFrame,
    output_dir: Path,
    genres: list[str],
    title: str,
    output_name: str,
    color: str,
) -> None:
    available = [genre for genre in genres if genre in set(top_regions["genre"])]
    if not available:
        return

    fig, axes = plt.subplots(1, len(available), figsize=(5 * len(available), 4.8))
    axes_list = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for ax, genre in zip(axes_list, available):
        subset = (
            top_regions[
                (top_regions["genre"] == genre)
                & (top_regions["region_rank_in_genre"] <= 5)
            ]
            .sort_values("region_rank_in_genre")
            .copy()
        )
        labels = subset["region_name"].map(short_region_name)
        bars = ax.barh(labels, subset["demand_index"], color=color)
        ax.invert_yaxis()
        ax.set_title(genre, fontsize=12, weight="bold")
        ax.set_xlabel("demand_index")
        ax.grid(True, axis="x", alpha=0.35)
        ax.set_axisbelow(True)
        max_value = subset["demand_index"].max()
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max_value * 0.01, bar.get_y() + bar.get_height() / 2, f"{width:.4f}", va="center", fontsize=8)
        ax.set_xlim(0, max_value * 1.18)

    fig.suptitle(title, fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(output_dir / output_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def load_inputs(input_dir: Path, args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    recommendations = read_beeline_csv(
        resolve_csv(input_dir, args.recommendations_file),
        ["region_name", "genre", "demand_index", "recommendation_rank"],
    )
    recommendations["demand_index"] = pd.to_numeric(recommendations["demand_index"])
    recommendations["recommendation_rank"] = pd.to_numeric(recommendations["recommendation_rank"])

    preferences = read_beeline_csv(
        resolve_csv(input_dir, args.preferences_file),
        ["age_group", "genre", "booking_count", "preference_weight"],
    )
    preferences["preference_weight"] = pd.to_numeric(preferences["preference_weight"])

    top_regions = read_beeline_csv(
        resolve_csv(input_dir, args.top_regions_file),
        ["genre", "region_rank_in_genre", "region_name", "demand_index"],
    )
    top_regions["demand_index"] = pd.to_numeric(top_regions["demand_index"])
    top_regions["region_rank_in_genre"] = pd.to_numeric(top_regions["region_rank_in_genre"])
    top_regions = (
        top_regions.sort_values(["genre", "demand_index"], ascending=[True, False])
        .drop_duplicates(["genre", "region_name"], keep="first")
        .copy()
    )
    top_regions["region_rank_in_genre"] = (
        top_regions.groupby("genre")["demand_index"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    return recommendations, preferences, top_regions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create report figures from Hive CSV exports")
    parser.add_argument("--input-dir", default="docs", help="Directory containing exported CSV files")
    parser.add_argument("--output-dir", default="docs/figures", help="Directory for output PNG files")
    parser.add_argument("--recommendations-file", default="region_genre_recommendations.csv")
    parser.add_argument("--preferences-file", default="age_preference_weights.csv")
    parser.add_argument("--top-regions-file", default="genre_top_regions.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_font()

    input_dir = project_path(args.input_dir)
    output_dir = project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    recommendations, preferences, top_regions = load_inputs(input_dir, args)

    save_rank_distribution(recommendations, output_dir)
    save_rank1_distribution(recommendations, output_dir)
    save_selected_region_comparison(recommendations, output_dir)
    save_top_regions_by_genre(top_regions, output_dir)
    save_age_preference_heatmap(preferences, output_dir)
    save_top1_region_by_genre(top_regions, output_dir)
    save_top5_region_panels(top_regions, output_dir)
    save_age_preference_line_trend(preferences, output_dir)
    save_group_panels(
        top_regions,
        output_dir,
        GROUP_A_GENRES,
        "Group A: Youth and Dynamic Genres - Top 5 Regions",
        "09_q2_group_a_youth_dynamic_top5.png",
        "#4472C4",
    )
    save_group_panels(
        top_regions,
        output_dir,
        GROUP_B_GENRES,
        "Group B: Senior and Classical Genres - Top 5 Regions",
        "10_q2_group_b_silver_pure_arts_top5.png",
        "#A65E2E",
    )

    print(f"Figures written to {output_dir}")


if __name__ == "__main__":
    main()
