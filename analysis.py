"""
COVID-19 country-level data analysis
------------------------------------
Reads the raw CSV, checks data quality, builds summary tables and saves charts.

Run:  python analysis.py
Outputs:
  images/*.png                 charts used in the README
  outputs/*.csv                summary tables
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "COVID-19_Coronavirus.csv"
IMG_DIR = BASE / "images"
OUT_DIR = BASE / "outputs"
IMG_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

MIN_POP_FOR_RANKING = 1_000_000     # avoids tiny territories dominating per-capita rankings
MIN_CASES_FOR_CFR = 10_000          # avoids unstable fatality rates on tiny case counts

sns.set_theme(style="whitegrid", context="notebook")
CONTINENT_COLORS = {
    "Africa": "#e07a1f",
    "Asia": "#c0392b",
    "Europe": "#2e6fb7",
    "Latin America and the Caribbean": "#2a9d6f",
    "Northern America": "#7d4fb0",
    "Oceania": "#8a8f98",
}


# ----------------------------------------------------------------------------
# 1. Load and clean
# ----------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    # The raw headers contain non-breaking spaces (\xa0); normalise them first
    df.columns = [" ".join(c.replace("\xa0", " ").split()) for c in df.columns]
    df = df.rename(columns={
        "Country": "country",
        "Other names": "other_names",
        "ISO 3166-1 alpha-3 CODE": "iso3",
        "Population": "population",
        "Continent": "continent",
        "Total Cases": "total_cases",
        "Total Deaths": "total_deaths",
        "Tot Cases//1M pop": "cases_per_1m",
        "Tot Deaths/1M pop": "deaths_per_1m",
        "Death percentage": "fatality_pct",
    })
    df["country"] = df["country"].str.strip()
    df["continent"] = df["continent"].str.strip()
    return df


def data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Run simple integrity checks and return them as a table."""
    cases_1m = df["total_cases"] / df["population"] * 1e6
    deaths_1m = df["total_deaths"] / df["population"] * 1e6
    cfr = df["total_deaths"] / df["total_cases"] * 100

    checks = [
        ("Rows (countries/territories)", len(df)),
        ("Columns", df.shape[1]),
        ("Duplicate countries", int(df["country"].duplicated().sum())),
        ("Duplicate ISO codes", int(df["iso3"].duplicated().sum())),
        ("Missing values (all columns)", int(df.isna().sum().sum())),
        ("Largest gap: cases per 1M vs recomputed", round(float((cases_1m - df["cases_per_1m"]).abs().max()), 3)),
        ("Largest gap: deaths per 1M vs recomputed", round(float((deaths_1m - df["deaths_per_1m"]).abs().max()), 3)),
        ("Largest gap: fatality % vs recomputed", f"{(cfr - df['fatality_pct']).abs().max():.1e}"),
        ("Countries with zero reported deaths", int((df["total_deaths"] == 0).sum())),
        ("Countries with under 1,000 cases", int((df["total_cases"] < 1000).sum())),
    ]
    report = pd.DataFrame(checks, columns=["check", "result"])
    report["result"] = report["result"].astype(str)      # keep ints as ints, small gaps readable
    report.to_csv(OUT_DIR / "data_quality_report.csv", index=False)
    return report


# ----------------------------------------------------------------------------
# 2. Summary tables
# ----------------------------------------------------------------------------
def continent_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Pooled figures per continent (sums first, then rates, so large countries weigh correctly)."""
    g = df.groupby("continent").agg(
        countries=("country", "count"),
        population=("population", "sum"),
        total_cases=("total_cases", "sum"),
        total_deaths=("total_deaths", "sum"),
    )
    g["cases_per_1m"] = g["total_cases"] / g["population"] * 1e6
    g["deaths_per_1m"] = g["total_deaths"] / g["population"] * 1e6
    g["fatality_pct"] = g["total_deaths"] / g["total_cases"] * 100
    g = g.sort_values("deaths_per_1m", ascending=False).round(2)
    g.to_csv(OUT_DIR / "continent_summary.csv")
    return g


def rankings(df: pd.DataFrame) -> dict:
    big = df[df["population"] >= MIN_POP_FOR_RANKING]
    reliable = df[df["total_cases"] >= MIN_CASES_FOR_CFR]
    tables = {
        "top10_total_cases": df.nlargest(10, "total_cases")[["country", "continent", "total_cases", "total_deaths"]],
        "top10_total_deaths": df.nlargest(10, "total_deaths")[["country", "continent", "total_deaths", "total_cases"]],
        "top10_cases_per_1m": big.nlargest(10, "cases_per_1m")[["country", "continent", "cases_per_1m"]],
        "top10_deaths_per_1m": big.nlargest(10, "deaths_per_1m")[["country", "continent", "deaths_per_1m"]],
        "highest_fatality_pct": reliable.nlargest(10, "fatality_pct")[["country", "continent", "fatality_pct", "total_cases"]],
        "lowest_fatality_pct": reliable.nsmallest(10, "fatality_pct")[["country", "continent", "fatality_pct", "total_cases"]],
    }
    for name, t in tables.items():
        t.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return tables


# ----------------------------------------------------------------------------
# 3. Charts
# ----------------------------------------------------------------------------
def _save(fig, name: str):
    fig.tight_layout()
    fig.savefig(IMG_DIR / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def chart_top_cases(df):
    top = df.nlargest(10, "total_cases").iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(top["country"], top["total_cases"] / 1e6,
                   color=[CONTINENT_COLORS[c] for c in top["continent"]])
    for bar, v in zip(bars, top["total_cases"] / 1e6):
        ax.text(v + 0.8, bar.get_y() + bar.get_height() / 2, f"{v:.1f}M", va="center", fontsize=9)
    ax.set_xlabel("Total confirmed cases (millions)")
    ax.set_title("Top 10 countries by total confirmed cases", fontweight="bold", loc="left")
    ax.set_xlim(0, top["total_cases"].max() / 1e6 * 1.12)
    handles = [plt.Rectangle((0, 0), 1, 1, color=CONTINENT_COLORS[c]) for c in CONTINENT_COLORS if c in set(top["continent"])]
    labels = [c for c in CONTINENT_COLORS if c in set(top["continent"])]
    ax.legend(handles, labels, loc="lower right", frameon=False, fontsize=9)
    _save(fig, "01_top10_total_cases.png")


def chart_top_deaths_per_million(df):
    big = df[df["population"] >= MIN_POP_FOR_RANKING]
    top = big.nlargest(10, "deaths_per_1m").iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(top["country"], top["deaths_per_1m"],
                   color=[CONTINENT_COLORS[c] for c in top["continent"]])
    for bar, v in zip(bars, top["deaths_per_1m"]):
        ax.text(v + 60, bar.get_y() + bar.get_height() / 2, f"{v:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Deaths per 1 million people")
    ax.set_title("Top 10 countries by deaths per million\n(population above 1 million)", fontweight="bold", loc="left")
    ax.set_xlim(0, top["deaths_per_1m"].max() * 1.12)
    handles = [plt.Rectangle((0, 0), 1, 1, color=CONTINENT_COLORS[c]) for c in CONTINENT_COLORS if c in set(top["continent"])]
    labels = [c for c in CONTINENT_COLORS if c in set(top["continent"])]
    ax.legend(handles, labels, loc="lower right", frameon=False, fontsize=9)
    _save(fig, "02_top10_deaths_per_million.png")


def chart_continents(summary):
    s = summary.copy()
    s.index = [i.replace("Latin America and the Caribbean", "Latin America\n& Caribbean") for i in s.index]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))
    metrics = [
        ("cases_per_1m", "Cases per 1M people", "{:,.0f}"),
        ("deaths_per_1m", "Deaths per 1M people", "{:,.0f}"),
        ("fatality_pct", "Fatality rate (% of cases)", "{:.2f}%"),
    ]
    for ax, (col, title, fmt) in zip(axes, metrics):
        order = s.sort_values(col, ascending=False)
        colors = [CONTINENT_COLORS[next(k for k in CONTINENT_COLORS if k.startswith(i.split("\n")[0]))] for i in order.index]
        bars = ax.bar(order.index, order[col], color=colors)
        for b, v in zip(bars, order[col]):
            ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=8)
        ax.set_title(title, fontweight="bold", fontsize=11)
        ax.tick_params(axis="x", rotation=60, labelsize=8)
        ax.set_ylim(0, order[col].max() * 1.15)
    fig.suptitle("Continent comparison (pooled across countries)", fontweight="bold", x=0.01, ha="left")
    _save(fig, "03_continent_comparison.png")


def chart_scatter(df):
    d = df[(df["cases_per_1m"] > 0) & (df["population"] >= MIN_POP_FOR_RANKING)]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for cont, sub in d.groupby("continent"):
        ax.scatter(sub["cases_per_1m"], sub["deaths_per_1m"].clip(lower=1),
                   s=np.sqrt(sub["population"]) / 40, alpha=0.7,
                   color=CONTINENT_COLORS[cont], edgecolor="white", linewidth=0.6)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1.5, 12000)
    ax.set_xlabel("Cases per 1M people (log scale)")
    ax.set_ylabel("Deaths per 1M people (log scale)")
    ax.set_title("Reported cases vs deaths per million\n(bubble size = population)", fontweight="bold", loc="left")

    # (x offset, y offset) in points, chosen so labels do not collide
    labels = {"USA": (8, 8), "India": (8, -12), "Brazil": (-38, 10), "Peru": (8, 4),
              "Bulgaria": (8, 4), "Denmark": (-20, -14), "S. Korea": (8, -4),
              "Mexico": (-40, 8), "Russia": (-42, -14), "China": (8, 6)}
    for name, offset in labels.items():
        r = d[d["country"] == name]
        if len(r):
            r = r.iloc[0]
            ax.annotate(name, (r["cases_per_1m"], max(r["deaths_per_1m"], 1)), xytext=offset,
                        textcoords="offset points", fontsize=8)

    handles = [plt.Line2D([0], [0], marker="o", linestyle="", markersize=8, alpha=0.8,
                          markerfacecolor=col, markeredgecolor="white", label=name)
               for name, col in CONTINENT_COLORS.items()]
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower right")
    _save(fig, "04_cases_vs_deaths_per_million.png")


def chart_fatality(df):
    reliable = df[df["total_cases"] >= MIN_CASES_FOR_CFR]
    top = reliable.nlargest(10, "fatality_pct").iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(top["country"], top["fatality_pct"],
                   color=[CONTINENT_COLORS[c] for c in top["continent"]])
    for bar, v in zip(bars, top["fatality_pct"]):
        ax.text(v + 0.2, bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("Deaths as % of confirmed cases")
    ax.set_title("Highest fatality rates (countries with 10,000+ cases)", fontweight="bold", loc="left")
    ax.set_xlim(0, top["fatality_pct"].max() * 1.12)
    _save(fig, "05_highest_fatality_rates.png")


def chart_correlation(df):
    cols = {
        "population": "Population",
        "total_cases": "Total cases",
        "total_deaths": "Total deaths",
        "cases_per_1m": "Cases / 1M",
        "deaths_per_1m": "Deaths / 1M",
        "fatality_pct": "Fatality %",
    }
    corr = df[list(cols)].rename(columns=cols).corr(method="spearman")
    corr.round(3).to_csv(OUT_DIR / "spearman_correlations.csv")
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True,
                linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title("Spearman rank correlations", fontweight="bold", loc="left")
    ax.tick_params(axis="x", rotation=40)
    _save(fig, "06_correlation_heatmap.png")
    return corr


# ----------------------------------------------------------------------------
# 4. Main
# ----------------------------------------------------------------------------
def main():
    df = load_data()

    print("=== DATA QUALITY ===")
    print(data_quality_report(df).to_string(index=False))

    print("\n=== GLOBAL TOTALS (sum of all rows) ===")
    pop, cases, deaths = df["population"].sum(), df["total_cases"].sum(), df["total_deaths"].sum()
    print(f"Population {pop:,} | Cases {cases:,} | Deaths {deaths:,} | Fatality {deaths / cases * 100:.2f}%")
    top10_share = df.nlargest(10, "total_cases")["total_cases"].sum() / cases * 100
    print(f"Top 10 countries hold {top10_share:.1f}% of all cases")

    print("\n=== CONTINENT SUMMARY ===")
    summary = continent_summary(df)
    print(summary.to_string())

    tables = rankings(df)
    for name, t in tables.items():
        print(f"\n--- {name} ---")
        print(t.to_string(index=False))

    chart_top_cases(df)
    chart_top_deaths_per_million(df)
    chart_continents(summary)
    chart_scatter(df)
    chart_fatality(df)
    corr = chart_correlation(df)
    print("\nSpearman: cases/1M vs deaths/1M =", round(corr.loc["Cases / 1M", "Deaths / 1M"], 2))

    print(f"\nDone. Charts saved in {IMG_DIR}, tables in {OUT_DIR}")


if __name__ == "__main__":
    main()
