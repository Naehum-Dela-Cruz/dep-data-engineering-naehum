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

dateTimeToday = datetime.now().strftime("%Y-%m-%d")
dateTimeTommorow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
dateTimeDayAfterTommorow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

client_serpApi = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
client_Apify = ApifyClient(os.getenv('APIFY_API_KEY'))



def write_to_jsonl(status, primary_source, title, results):
    data_to_write = {"dateTime_collected" : dateTimeToday, "status" : status, "primary_source" : primary_source, **results}
    with open(os.path.join(RAW_DATA_DIR, title), 'a', encoding="utf-8") as f:
        f.write(json.dumps(data_to_write, ensure_ascii=False) + "\n")



# NOTE: Done for now ☑️ (don't forget to change if needed)
def backup_google_hotels():
    try:
        run_input = {
            "adults": 1,
            "currency": "PHP",
            "rooms": 1,
            "searches": [
                {
                    "location": "Bacolod",
                    "checkInDate": dateTimeTommorow,
                    "checkOutDate": dateTimeDayAfterTommorow
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
                write_to_jsonl("success", False, f'google_hotels.jsonl', results)
        if not hasResults:
            write_to_jsonl("noResults", False, f'google_hotels.jsonl', 
                {
                    "checkInDate": dateTimeTommorow,
                    "checkOutDate": dateTimeDayAfterTommorow
                }
            )
    except:
        write_to_jsonl("ingestion_totalFail", False, f'google_hotels.jsonl', 
                {
                    "checkInDate": dateTimeTommorow,
                    "checkOutDate": dateTimeDayAfterTommorow
                }
            )
        primary_google_flights()



# NOTE: Done for now ☑️ (don't forget to change if needed)
# DONE: have each flight show as a seperate .jsonl        
def backup_google_flights():
    try:
        run_input = {
            "arrival_id": "BCD",
            "currency": "PHP",
            "departure_id": "MNL",
            "exclude_basic": False,
            "fetch_booking_options": False,
            "gl": "ph",
            "hl": "en",
            "outbound_date": dateTimeTommorow,
        }
        
        run = client_Apify.actor("1dYHRKkEBHBPd0JM7").call(run_input=run_input)

        dataset_id = run.default_dataset_id
        hasResults = False
        if dataset_id:
            for results in client_Apify.dataset(dataset_id).iterate_items():
                for flight in results.get("all_flights", []):
                    hasResults = True
                    write_to_jsonl("success", False, f'google_flights.jsonl', flight)                
        if not hasResults:
            write_to_jsonl("noResults", False, f'google_flights.jsonl', 
                {
                    "outbound_date": dateTimeTommorow,
                }
            )
    except:
        write_to_jsonl("ingestion_totalFail", False, f'google_flights.jsonl', 
                {
                    "outbound_date": dateTimeTommorow,
                }
            )
        primary_google_trends()



# NOTE: Done for now ☑️ (don't forget to change if needed)
def backup_google_trends():
    try:
        run_input = {
            "mode": "keyword",
            "keyword": "Masskara",
            "predefinedTimeframe": "now 7-d",
            "geo": "PH",
            "fetchRegionalData": False,
            "proxyConfiguration": { "useApifyProxy": True },
        }

        # Run the Actor and wait for it to finish
        run = client_Apify.actor("nWhM7vTPu16lcwuIg").call(run_input=run_input)

        dataset_id = run.default_dataset_id
        hasResults = False

        if dataset_id:
            for results in client_Apify.dataset(dataset_id).iterate_items():
                # print(results.keys())
                for timestamp, value in results.get("timeline_data", {}).get("Masskara", {}).items():
                    hasResults = True
                    write_to_jsonl("success", False, f'google_trends.jsonl', {"timestamp": timestamp, "value": value})
        if not hasResults:
            write_to_jsonl("noResults", False, f'google_trends.jsonl', 
                {
                    "lookup_date": dateTimeToday,
                }
            )
    except:
        write_to_jsonl("ingestion_totalFail", False, f'google_trends.jsonl', 
                {
                    "lookup_date": dateTimeToday,
                }
            )



# NOTE: LEFT .env EXPOSED, CURRENTLY USELESS—NO CREDITS LEFT
def primary_google_hotels():
    try:
        data = client_serpApi.search({
            "engine": "google_hotels",
            "q": "Bacolod Hotels",
            "hl": "en",
            "gl": "ph",
            "check_in_date": dateTimeTommorow,
            "check_out_date": dateTimeDayAfterTommorow,
            "currency": "PHP",
            "adults": "1"
        })

        has_error = "error" in data
        has_hotels = "properties" in data

        # TODO: finish this hotel shizz 
        # FINISH WHAT EXACTLY? IT SEEMS TO WORK FINE
        if not has_error and has_hotels:
            
            for hotel in data.get("properties" , []):
                write_to_jsonl("success", True,  f'google_hotels.jsonl', {
                        "hotel_name" : hotel.get("name", "Unknown Hotel"),
                        "lowest_Rate" : (hotel.get("rate_per_night") or {}).get("lowest", "N/A"),
                        "check_in" : dateTimeTommorow,
                        "check_out" : dateTimeDayAfterTommorow
                    }
                )

        else:
            write_to_jsonl("error", True, f'google_hotels.jsonl', 
                {                    
                    "check_in_date": dateTimeTommorow,
                    "check_out_date": dateTimeDayAfterTommorow,
                }
            )
    except:
        backup_google_hotels()



# NOTE: DON'T FORGET TO NOT EXPOSE YOUR .ENV AGAIN
# TODO: THIS NEEDS TO OUTPUT EACH FLIGHT TO A JSONL LINE
# CHECK HOTEL EXAMPLE JSONL
# THIS IS THE PRIMARY FUNCTION, DUM
def primary_google_flights():
    try:
        data = client_serpApi.search({
            "engine": "google_flights",
            "hl": "en",
            "gl": "ph",
            "departure_id": "MNL",
            "arrival_id": "BCD",
            "outbound_date": dateTimeTommorow,
            "currency": "PHP",
            "type": "2",
            "travel_class": "1",
            "adults": "1",
            "sort_by": "2"
        })
        
        # TODO: SELECTIVELY INGEST ONLY RESULTS. REFERENCE PRIMARY HOTEL KEEP IN MIND [] and {}
        # THIS IS THE PRIMARY FUNCTION, DUM
        has_error = "error" in data
        # results_state = data.get("search_information", {}).get("flight_results_State")
        has_flights = "best_flights" in data or "other_flights" in data

        if not has_error and has_flights:
            flights = data.get("best_flights", []) + data.get("other_flights", [])
            for flight in flights:
                write_to_jsonl("success", True,  f'google_flights.jsonl', flight)

        else:
            write_to_jsonl("error", True, f'google_flights.jsonl', 
                {
                    "outbound_date": dateTimeTommorow,
                }
            )
    except:
        backup_google_flights()



def primary_google_trends():
    try:
        results = client_serpApi.search({
            "engine": "google_trends",
            "q": "masskara",
            "data_type": "TIMESERIES",
            "hl": "en",
            "geo": "PH",
            "tz": "-480",
            "date": "today 3-m"
        })

        if "error" or "Error" in results:
            write_to_jsonl("noResults", True, f'google_trends.jsonl', 
                {
                    "lookup_date": dateTimeToday,
                }
            )
        else:
            for result in results.iterate_items():
                for timestamp, value in result.get("interest_over_time", {}).get("timeline_Data", []).items():
                    write_to_jsonl("success", True, f'google_trends.jsonl', {"timestamp": timestamp, "value": value})
    except:
        print("!!! primary_google_trends() error, switching to backup !!!")
        backup_google_trends()
    


if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    # primary_google_hotels()
    # primary_google_flights()
    # primary_google_trends()

    # comment these once the primary sources are no longer kaput
    
    # backup_google_hotels()
    # backup_google_flights()
    # backup_google_trends()
    
    print("Ingestion complete. Check data/raw/ for output.")
    print("Make sure you didn't edit the primary ingestions while they're\ncommented out like a dum-dum")