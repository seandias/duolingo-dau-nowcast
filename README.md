# Can Google searches predict company KPIs?

Companies report operating metrics (users, bookings) once a quarter, weeks after the quarter ends. Google search interest is free and updates every week. This project tests, company by company, whether search data could have told an investor where a KPI was heading **before** the earnings release, and records a prediction for each company's next quarter ahead of time.

## Results so far

| Company | KPI | Quarters tested | Search-change model vs benchmark | Closer than benchmark | Verdict | Takeaway |
|---|---|---|---|---|---|---|
| [Airbnb](companies/airbnb/README.md) | Nights booked | 13 | 10% better | 6 of 13 | Only on average | The edge rests on one quarter (Q1 2025); without it, search does 5% worse. Q3 2026 call: about 142M nights. |
| [Duolingo](companies/duolingo/README.md) | Daily active users | 10 | 11% better | 7 of 10 | Yes, consistently | Small but steady edge (about 0.2M DAUs a quarter), though an earlier data version showed the opposite. Q3 2026 call: about 62M DAUs. |

**The honest summary: search gives at most a small, fragile edge for both companies.** An earlier version of this project found a clean contrast (search works for travel, fails for a habit app). Adding more data reversed it: Airbnb's edge turned out to depend on a single quarter, and Duolingo's result flipped from slightly worse to slightly better. That sensitivity is the main finding so far, and the reason the analysis now reports how consistent each edge is, not just its average. `outputs/summary.md` holds the full comparison table, regenerated each run.

New here? The [Duolingo walkthrough notebook](walkthrough_duolingo.ipynb) explains the whole method step by step, with charts. It was written on an earlier version of the data, so its numbers differ from the tables above.

## Method (same for every company)

1. **Compare growth, not levels.** KPIs and searches both trend, so their raw levels correlate whether or not one predicts the other. Year-over-year growth removes the trend and seasonality.
2. **Test out-of-sample.** For each quarter, models are fit only on earlier quarters, then predict that quarter, which is what an analyst could actually have known at the time.
3. **Beat a benchmark.** The bar is a naive forecast that assumes KPI growth stays the same as last quarter. A signal that can't beat this isn't useful.
4. **Check consistency, not just the average.** A model can beat the benchmark on average thanks to one lucky quarter. Each company's results also report how many quarters the search model was closer than the benchmark, and its edge with the single best quarter removed. The verdict is "Yes, consistently" only if it wins on average, in most quarters, and without its best quarter.
5. **Two models:**
   - *Search-change model:* last quarter's KPI growth, adjusted by how much search growth moved since then. Asks whether a turn in searches signals a turn in the KPI.
   - *Search-level model:* KPI growth regressed directly on search growth.

## Repo layout

```
companies/<name>/
    config.json         company name, ticker, KPI label, Google search term, SEC cik, KPI pattern
    kpi.csv             quarterly KPI scraped from SEC filings by scrape_kpi.py, with the filing link and matched text per row
    google_trends.csv   monthly search interest since 2004 (created by fetch_trends.py)
    README.md           write-up of that company's results
outputs/<name>/         results.md and charts per company
outputs/summary.md      comparison across companies
src/scrape_kpi.py       scrapes quarterly KPIs from SEC earnings filings (8-K, Item 2.02)
src/fetch_trends.py     downloads Google Trends data
src/analysis.py         runs the tests, charts and nowcast
```

## Run it

```bash
pip install -r requirements.txt
python src/scrape_kpi.py airbnb      # one company at a time; repeat for duolingo
python src/fetch_trends.py --all     # or one company: python src/fetch_trends.py airbnb
python src/analysis.py --all         # or one company: python src/analysis.py airbnb
```

If Google rate-limits the download, save the CSV by hand from trends.google.com (steps at the top of `src/fetch_trends.py`).

## Adding a company

1. Create `companies/<name>/config.json` (copy an existing one and change the fields).
2. Add the company's SEC `cik` to its config, then run `python src/scrape_kpi.py <name> --inspect <word>` to see how its filings word the KPI.
3. Write a `kpi_pattern` in the config (group 1 = current quarter, or 3 groups = two values plus the YoY %), then run `python src/scrape_kpi.py <name>` to build `kpi.csv` automatically.

Good candidates have a consumer-facing KPI that people plausibly search for, and a reason the signal might behave differently from companies already covered.

## Limitations

- **Small samples.** Each company has 10 to 13 tested quarters. Treat results as directional, not as a trading model.
- **Results are sensitive to the data.** Switching from 5 years of weekly search data to the full monthly history changed Duolingo's verdict. Any single result here should be read with that in mind.
- **Searches are not customers.** Search interest mostly reflects discovery and buzz, not repeat usage.
- **Google Trends is relative and sampled.** Values are scaled 0 to 100 within each download and can shift slightly between downloads. Google also changed how it collects Trends data from 1 January 2022, which may affect growth rates across that date.
- **Worldwide search mixes markets.** Region-specific search terms (the `geo` field in `config.json`) are a natural next step.
