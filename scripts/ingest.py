"""
Phase 2 — Data Ingestion
Replace this template with your own ingestion logic.
"""

import os
import json
import serpapi
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

dateTimeNow = datetime.now().strftime("%Y-%m-%d")
dateTimeTommorow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

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

def primary_google_hotels():

    client = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
    results = client.search({
        "engine": "google_hotels",
        "q": "Bacolod Hotels",
        "hl": "en",
        "gl": "ph",
        "check_in_date": f"{dateTimeNow}",
        "check_out_date": f"{dateTimeTommorow}",
        "currency": "PHP",
        "adults": "1"
    })

    with open(os.path.join(RAW_DATA_DIR, f'google_hotel_{dateTimeNow}.json'), 'w', encoding='utf=8') as f:
        json.dump(results.as_dict(), f, indent=4, ensure_ascii=False)

def primary_google_flights():

    client = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
    results = client.search({
        "engine": "google_flights",
        "hl": "en",
        "gl": "ph",
        "departure_id": "MNL",
        "arrival_id": "BCD",
        "outbound_date": f"{dateTimeNow}",
        "currency": "PHP",
        "type": "2",
        "travel_class": "1",
        "adults": "1",
        "sort_by": "2"
    })
    

    with open(os.path.join(RAW_DATA_DIR, f'google_flights_{dateTimeNow}.json'), 'w', encoding='utf=8') as f:
        json.dump(results.as_dict(), f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    primary_google_trends()
    primary_google_hotels()
    primary_google_flights()
    print("Ingestion complete. Check data/raw/ for output.")