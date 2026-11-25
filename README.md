# COVID-19 Country-Level Data Analysis

An exploratory data analysis of COVID-19 cases and deaths across **225 countries and territories**, built with Python (pandas, matplotlib, seaborn). The project cleans the data, checks its quality, compares continents fairly using population-adjusted rates, and shows where reported numbers can mislead.

## Questions this project answers
1. Which countries have the most confirmed cases and deaths?
2. Once population is taken into account, which countries and regions were hit hardest?
3. How do fatality rates differ across continents and countries?
4. Do countries with more reported cases per person also report more deaths per person?
5. Is the data reliable enough to trust these comparisons?

## Dataset
`data/COVID-19_Coronavirus.csv` has one row per country or territory:

| Column | Meaning |
|---|---|
| Country, Other names, ISO 3166-1 alpha-3 CODE | Name and country code |
| Population, Continent | Population and region |
| Total Cases, Total Deaths | Reported totals |
| Tot Cases/1M pop, Tot Deaths/1M pop | Totals per million people |
| Death percentage | Deaths as a percentage of cases |

The file is a single snapshot and does not include a date, so figures show cumulative totals at the time the data was collected.

## Key findings

**Scale**
- The data covers about 7.89 billion people, 491.6 million confirmed cases and 6.18 million deaths, a pooled fatality rate of **1.26%**.
- Cases are concentrated: the **top 10 countries hold 58.0% of all cases**. The USA alone reports 81.8 million cases and about 1.0 million deaths, the most of any country on both counts.
- By total cases the top 10 are USA, India, Brazil, France, Germany, UK, Russia, Turkey, Italy and South Korea.

**Population-adjusted view (continents)**

| Continent | Cases per 1M | Deaths per 1M | Fatality rate |
|---|---:|---:|---:|
| Northern America | 228,954 | 2,806 | 1.23% |
| Latin America & Caribbean | 102,082 | 2,551 | 2.50% |
| Europe | 240,951 | 2,373 | 0.98% |
| Asia | 30,192 | 301 | 1.00% |
| Oceania | 130,024 | 215 | 0.17% |
| Africa | 8,423 | 181 | 2.15% |

- Northern America, Latin America and Europe each lost roughly 2,400 to 2,800 people per million, about **8 to 16 times** the rate reported in Asia and Africa.
- Latin America combines a high death rate with the highest fatality rate (2.50%). Europe has the most cases per person but a lower fatality rate (0.98%).
- Peru has the highest deaths per million (6,286) among countries above 1 million people. **8 of the top 10** in that ranking are European countries.

**Fatality rates**
- Among countries with at least 10,000 cases, Yemen (18.2%), Sudan (7.9%), Peru (6.0%), Mexico (5.7%) and Syria (5.6%) report the highest rates. Bhutan, New Zealand and Iceland report the lowest, all below 0.06%.
- South Korea has 13.9 million cases but only 17,235 deaths (0.12%), a very different outcome from countries with similar case counts.

**Relationships**
- Cases per million and deaths per million are strongly related (Spearman correlation **0.76**).
- Cases per million and fatality rate move in opposite directions (**-0.46**). Countries that report more cases per person tend to report a lower share of deaths among those cases, which is consistent with differences in testing and reporting, though this data cannot prove that.

## Charts

| | |
|---|---|
| ![Top 10 total cases](images/01_top10_total_cases.png) | ![Top 10 deaths per million](images/02_top10_deaths_per_million.png) |
| ![Continent comparison](images/03_continent_comparison.png) | ![Cases vs deaths scatter](images/04_cases_vs_deaths_per_million.png) |
| ![Highest fatality rates](images/05_highest_fatality_rates.png) | ![Correlation heatmap](images/06_correlation_heatmap.png) |

## Data quality checks
The script verifies the data before analysing it (`outputs/data_quality_report.csv`):
- 225 rows, no duplicate countries or ISO codes.
- 1 missing value in the whole file (the alternative name for Montenegro).
- Per-million figures and the death percentage were recomputed from raw totals and match the file (largest gap under 0.5 per million, caused by rounding).
- 8 countries report zero deaths and 10 report fewer than 1,000 cases, so ranking tables use population and case-count thresholds to avoid tiny territories dominating.
- Column headers contained hidden non-breaking spaces, which the script normalises.

## Limitations
- This is one snapshot, so it cannot show how the pandemic changed over time.
- Confirmed cases depend on how much testing a country did, and countries define COVID deaths differently. Cross-country gaps are partly differences in reporting.
- Fatality percentage is unstable when case counts are small (for example Yemen's 18% is based on 11,806 cases).
- Continent figures are pooled, so large countries influence them most and they hide differences between countries.
- Correlations describe patterns, not causes.

## Project structure
```
covid19-data-analysis/
├── data/
│   └── COVID-19_Coronavirus.csv
├── images/                 charts used in this README
├── outputs/                summary tables (CSV)
├── analysis.py             full analysis pipeline
├── requirements.txt
└── README.md
```

## Run it yourself
```bash
git clone https://github.com/YOUR-USERNAME/covid19-data-analysis.git
cd covid19-data-analysis
pip install -r requirements.txt
python analysis.py
```
The script prints the data quality report and key tables, and regenerates every chart in `images/` and every table in `outputs/`.

## Skills demonstrated
Data cleaning and validation, exploratory analysis, per-capita normalisation, correlation analysis, data visualisation, and writing clear, honest conclusions with stated limitations.

## Ideas for next steps
- Add a time series dataset to study waves and vaccination effects.
- Build an interactive dashboard (Streamlit or Power BI).
- Model fatality rate against income, age structure and healthcare capacity.
