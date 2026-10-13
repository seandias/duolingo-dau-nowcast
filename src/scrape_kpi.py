"""Scrape quarterly KPIs from a company's SEC earnings filings.

Run from the repo root:
    python src/scrape_kpi.py airbnb
"""
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

COMPANIES = Path("companies")
HEADERS = {"User-Agent": "Sean Dias seankdias@gmail.com"} #SEC Requirement

def sec_get(url):
    """Download a URL from the SEC politely: identify ourselves and pause between requests."""
    time.sleep(0.2)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response
    
def get_earnings_filings(cik):
    """Step 1: list the company's 8-K filings tagged Item 2.02 (earnings)."""
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    data = sec_get(url).json()
    recent = data["filings"]["recent"]        # parallel lists: form[i], items[i], ... describe filing i

    filings = []
    for i in range(len(recent["form"])):
        if recent["form"][i] == "8-K" and "2.02" in recent["items"][i]: #item 2.02 means here are our results
            filings.append({
                "accession": recent["accessionNumber"][i],  # the filing's unique ID
                "filing_date": recent["filingDate"][i],
            })
    return filings

def find_press_release_url(cik, accession):
    """Step 2: Return links to the exhibits (EX-99.x) inside one filing."""
    folder = accession.replace("-", "") # the folder name is the ID without dashes
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{accession}-index.htm"
    soup = BeautifulSoup(sec_get(index_url).text, "html.parser")

    urls = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 4 and cells[3].get_text(strip = True).startswith("EX-99"):
            link = cells[2].find("a")
            if link:
                urls.append("https://www.sec.gov" + link["href"])
    return urls

def get_text(url):
     """Step 3: download the press release and strip the HTML down to plain text."""
     soup = BeautifulSoup(sec_get(url).text, "html.parser")
     text = soup.get_text(" ") # drop every HTML tag, keep the words, separate them with spaces
     return re.sub(r"\s+", " ", text) # turn any run of spaces, tabs or newlines into a single space

def extract_kpi(text, pattern):
    """Step 4: use the regex from config.json to find the KPI number."""
    match = re.search(pattern, text) # find the first place the pattern fits
    if match is None:
        return None
    return float(match.group(1)), match.group(0)

def quarter_for(filing_date):
    """Step 5: work out which quarter a release covers, from its filing date."""
    filed_in = pd.Period(filing_date, freq="Q") # e.g. "2026-08-06" -> 2026Q3
    return filed_in - 1 # one quarter back -> 2026Q2

def scrape(slug):
    """Step 6: run steps 1-5 on every filing and save companies/<slug>/kpi_scraped.csv."""
    cfg = json.loads((COMPANIES / slug / "config.json").read_text())
    cik, pattern = cfg["cik"], cfg["kpi_pattern"]

    rows = []
    for f in get_earnings_filings(cik):
        quarter = quarter_for(f["filing_date"])
        urls = find_press_release_url(cik, f["accession"])

        result = None
        for url in urls: # some filings have 2 exhibits: try each
            result = extract_kpi(get_text(url), pattern)
            if result:
                break

        if result is None:
            print(f"[{slug}] {quarter}: no match, check this filing ({f['filing_date']})")
            continue

        value, evidence = result
        rows.append({
            "quarter": str(quarter),
            "quarter_end": str(quarter.end_time.date()),
            "value": value,
            "source": url,  # link to the exact document for verification
            "evidence": evidence, # the text it matched
        })
        print(f"[{slug}] {quarter}: {value}")

    df = pd.DataFrame(rows).drop_duplicates("quarter").sort_values("quarter")
    out = COMPANIES / slug / "kpi_scraped.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} quarters to {out}\n")


def compare(slug):
    """Step 6b: check the scraped numbers against the hand-entered kpi.csv."""
    folder = COMPANIES / slug
    scraped = pd.read_csv(folder / "kpi_scraped.csv").set_index("quarter")["value"]
    manual = pd.read_csv(folder / "kpi.csv").set_index("quarter")["value"]

    both = pd.DataFrame({"manual": manual, "scraped": scraped}).dropna()
    both["check"] = ((both["manual"] - both["scraped"]).abs() < 0.05).map({True: "✅", False: "❌"})
    print(both.to_string())
    print(f"\n{(both['check'] == '✅').sum()} of {len(both)} quarters match")

    missing = manual.index.difference(scraped.index)
    if len(missing):
        print("In kpi.csv but not scraped yet:", ", ".join(missing))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 src/scrape_kpi.py <company>")
    slug = sys.argv[1]
    scrape(slug)
    compare(slug)