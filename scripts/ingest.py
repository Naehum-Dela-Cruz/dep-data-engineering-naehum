"""
Phase 2 — Data Ingestion
Replace this template with your own ingestion logic.
"""

import os
import json
import serpapi
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

dateTimeNow = datetime.now().strftime("%Y-%m-%d")
dateTimeTommorow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
dateTimeTommorow2 = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

client = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
client_Apify = ApifyClient(os.getenv('APIFY_API_KEY'))


def write_to_json(title, results):

    with open(os.path.join(RAW_DATA_DIR, title), 'w', encoding="utf-8") as f:
        json.dump(results.as_dict(), f, indent=4, ensure_ascii=False)

def write_to_jsonl(status, primary_source, title, results):
    data_to_write = {"status" : status, "primary_source" : primary_source, **results}
    with open(os.path.join(RAW_DATA_DIR, title), 'a', encoding="utf-8") as f:
        f.write(json.dumps(data_to_write, ensure_ascii=False) + "\n")

def backup_google_hotels():
    run_input = {
        "adults": 1,
        "currency": "PHP",
        "rooms": 1,
        "searches": [
            {
                "location": "Bacolod",
                "checkInDate": dateTimeNow,
                "checkOutDate": dateTimeTommorow
            }
        ],
        "sortBy": "relevance",
        "type": "hotels"
    }
    
    run = client_Apify.actor("H1scmbaCSREtaQDQU").call(run_input=run_input)

    dataset_id = run.default_dataset_id
    hasResults = False
    if dataset_id:
        for results in client_Apify.dataset(dataset_id).iterate_items():
            hasResults = True
            write_to_jsonl("success", False, f'google_hotel_{dateTimeNow}.jsonl', results)
    if not hasResults:
        write_to_jsonl("noResults", False, f'google_hotel_{dateTimeNow}.jsonl', 
            {
                "checkInDate": dateTimeNow,
                "checkOutDate": dateTimeTommorow
            }
        )
        
def backup_google_flights():
    run_input = {
        "arrival_id": "BCD",
        "currency": "PHP",
        "departure_id": "MNL",
        "exclude_basic": False,
        "fetch_booking_options": False,
        "gl": "ph",
        "hl": "en",
        "outbound_date": dateTimeNow,
    }
    
    run = client_Apify.actor("1dYHRKkEBHBPd0JM7").call(run_input=run_input)

    dataset_id = run.default_dataset_id
    hasResults = False
    if dataset_id:
        for results in client_Apify.dataset(dataset_id).iterate_items():
            hasResults = True
            write_to_jsonl("success", False, f'google_flights_{dateTimeNow}.jsonl', results)
    if not hasResults:
        write_to_jsonl("noResults", False, f'google_flights_{dateTimeNow}.jsonl', 
            {
                "outbound_date": dateTimeNow,
            }
        )
 
def primary_google_trends():
    results = client.search({
        "engine": "google_trends",
        "q": "masskara",
        "data_type": "TIMESERIES",
        "hl": "en",
        "geo": "PH",
        "tz": "-480",
        "date": "now 1-d"
    })

    write_to_json(f'google_trends_{dateTimeNow}.json', results)

def primary_google_hotels():
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

    write_to_json(f'google_hotel_{dateTimeNow}.json', results)

def primary_google_flights():
    try:
        data = client.search({
            "engine": "google_flights",
            "hl": "en",
            "gl": "ph",
            "departure_id": "MNL",
            "arrival_id": "BCD",
            "outbound_date": dateTimeNow,
            "currency": "PHP",
            "type": "2",
            "travel_class": "1",
            "adults": "1",
            "sort_by": "2"
        })

        # write_to_json(f'google_flights_{dateTimeNow}.json', results)

        if not "error" in data:
            for results in data:   
                write_to_jsonl("success", True, f'google_flights_{dateTimeNow}.jsonl', results)
        else:
            write_to_jsonl("noResults", True, f'google_flights_{dateTimeNow}.jsonl', 
                {
                    "outbound_date": dateTimeNow,
                }
            )
    except:
        backup_google_flights()

        


if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    # primary_google_trends()
    # primary_google_hotels()
    # primary_google_flights()
    # backup_google_hotels()
    backup_google_flights()
    print("Ingestion complete. Check data/raw/ for output.")