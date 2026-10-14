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
    data = sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()

    pages = [data["filings"]["recent"]] #front page
    for extra in data["filings"]["files"]:
        pages.append(sec_get("https://data.sec.gov/submissions/" + extra["name"]).json())

    filings = []
    for page in pages:
        for i in range(len(page["form"])):
            if page["form"][i] == "8-K" and "2.02" in page["items"][i]: #item 2.02 means here are our results
                filings.append({
                    "accession": page["accessionNumber"][i],  # the filing's unique ID
                    "filing_date": page["filingDate"][i],
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
    """Step 4: find the KPI with the regex, return (value, the text it matched).

    Two kinds of pattern are supported:
    - 1 group:  group 1 is the current quarter (e.g. Airbnb)
    - 3 groups: two values in unknown order + the YoY % printed next to them (e.g. Duolingo);
                the YoY % is used to work out which value is the current quarter
    """
    match = re.search(pattern, text) # find the first place the pattern fits
    if match is None:
        return None

    if len(match.groups()) == 1:
        return float(match.group(1)), match.group(0)

    a, b = float(match.group(1)), float(match.group(2))
    yoy = float(match.group(3).strip("()")) / 100 # "16" -> 0.16, "(4)" -> 0.04
    if match.group(3).startswith("("):  # (4)% means -4% in financial reports
        yoy = -yoy
    # whichever order gives growth closest to the printed YoY % is the right one
    current = b if abs(b / a - 1 - yoy) < abs(a/b - 1 - yoy) else a
    return current, match.group(0)

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
    out = COMPANIES / slug / "kpi.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} quarters to {out}\n")

def inspect(slug, word, how_many=2):
    """Show the text around `word` in the newest and oldest filings, to help write a pattern."""
    cfg = json.loads((COMPANIES / slug / "config.json").read_text())
    cik = cfg["cik"]
    filings = get_earnings_filings(cik)
    print(f"{len(filings)} earnings filings found for {slug}\n")

    picks = filings[:how_many] + filings[-how_many:]
    for f in picks:
        quarter = quarter_for(f["filing_date"])
        for url in find_press_release_url(cik, f["accession"]):
            text = get_text(url)
            print(f"=== {quarter}. | {url}")
            for m in re.finditer(word, text):
                print(repr(text[m.start() - 80 : m.end() + 120]))
            print()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 3 and args[1] == "--inspect":
        inspect(args[0], args[2])                 # e.g. airbnb --inspect Booked
    else:
        raise SystemExit("Usage: python3 src/scrape_kpi.py <company> [--inspect <word>]")