# Duolingo (DUOL): search interest vs daily active users (daus)

- Quarters with both series (YoY): 15 (2022Q4 to 2026Q2)
- Correlation of YoY growth, search vs DAUs: 0.53
- Out-of-sample quarters tested: 9
- Mean absolute error, naive benchmark: 1.73M
- Mean absolute error, search-change model: 1.78M (+3% vs benchmark)
- Mean absolute error, search-level model: 5.77M (+233% vs benchmark)
- Search-change model called acceleration vs deceleration correctly: 44% of quarters

## Walk-forward detail

| quarter   |   actual |   naive |   change_model |   level_model | actual_yoy   | naive_yoy   | change_yoy   | level_yoy   |
|:----------|---------:|--------:|---------------:|--------------:|:-------------|:------------|:-------------|:------------|
| 2024Q2    |     34.1 |    33.1 |           33.1 |          34.2 | 59.3%        | 54.7%       | 54.7%        | 60.0%       |
| 2024Q3    |     37.2 |    38.6 |           38.6 |          38.7 | 53.7%        | 59.3%       | 59.6%        | 60.0%       |
| 2024Q4    |     40.5 |    41.4 |           41.2 |          42.8 | 50.6%        | 53.7%       | 53.3%        | 59.2%       |
| 2025Q1    |     46.6 |    47.3 |           47   |          49.9 | 48.4%        | 50.6%       | 49.8%        | 58.9%       |
| 2025Q2    |     47.7 |    50.6 |           50.9 |          53.4 | 39.9%        | 48.4%       | 49.2%        | 56.7%       |
| 2025Q3    |     50.5 |    52   |           52   |          57.7 | 35.8%        | 39.9%       | 39.8%        | 55.1%       |
| 2025Q4    |     52.7 |    55   |           55   |          61.8 | 30.1%        | 35.8%       | 35.9%        | 52.6%       |
| 2026Q1    |     56.5 |    60.6 |           61   |          68.3 | 21.2%        | 30.1%       | 31.0%        | 46.5%       |
| 2026Q2    |     58.7 |    57.8 |           57.9 |          69.5 | 23.1%        | 21.2%       | 21.3%        | 45.8%       |

## Nowcast for 2026Q3 (not yet reported)

- Search interest YoY: -12.8%
- Naive benchmark: 62.1M (23.1% YoY)
- Search-change model: 61.7M (22.2% YoY)
- Search-level model: 69.3M (37.2% YoY)