"""
Phase 2 — Data Ingestion
This script fetches Google Trends data for a specific query ("Masskara") in the Philippines
using the SerpApi service, and saves the resulting JSON response to the local data/raw directory.
"""
import json
import os
import serpapi
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

dateTimeNow = datetime.now().strftime("%Y-%m-%d")

def primary_google_trends():

    client = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
    results = client.search({
    "engine": "google_trends",
    "q": "masskara",
    "data_type": "TIMESERIES",
    "hl": "en",
    "geo": "PH",
    "tz": "-480",
    "date": "now 1-d"
    })

    with open(os.path.join(RAW_DATA_DIR, f'google_trends_{dateTimeNow}.json'), 'w', encoding="utf-8") as f:
        json.dump(results.as_dict(), f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    primary_google_trends()
    print("Ingestion complete. Check data/raw/ for output.")