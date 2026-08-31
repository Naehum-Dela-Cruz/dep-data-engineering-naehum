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

# MassKara Festival major-event window. Hardcoded for this year's run —
# if you reuse this script next year, update these dates.
FESTIVAL_DATES = ["2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"]

client_serpApi = serpapi.Client(api_key=os.getenv('SERPAPI_API_KEY'))
client_Apify = ApifyClient(os.getenv('APIFY_API_KEY'))


def write_to_jsonl(status, primary_source, collection_mode, title, results):
    """
    One JSONL file per data category (google_hotels.jsonl / google_flights.jsonl /
    google_trends.jsonl), regardless of source (primary vs backup) or purpose
    (rolling baseline vs fixed festival-date target).

    collection_mode distinguishes *why* this row was collected:
      - "rolling"         -> the day-ahead query, used as a moving baseline
      - "festival_target" -> a fixed Oct 9-12 date, used to track lead-time/surge
    Don't blend these two without checking collection_mode first — they answer
    different questions.
    """
    data_to_write = {
        "dateTime_collected": dateTimeToday,
        "status": status,
        "primary_source": primary_source,
        "collection_mode": collection_mode,
        **results,
    }
    with open(os.path.join(RAW_DATA_DIR, title), 'a', encoding="utf-8") as f:
        f.write(json.dumps(data_to_write, ensure_ascii=False) + "\n")


# =========================================================================
# BACKUP SOURCES — ROLLING (day-ahead baseline)
# =========================================================================

def backup_google_hotels():
    """Rolling baseline: always checks in 'tomorrow' for one night."""
    try:
        run_input = {
            "adults": 1,
            "currency": "PHP",
            "rooms": 1,
            "searches": [
                {
                    "location": "Bacolod",
                    "checkInDate": dateTimeTommorow,
                    "checkOutDate": dateTimeDayAfterTommorow,
                }
            ],
            "sortBy": "relevance",
            "type": "hotels",
        }

        run = client_Apify.actor("H1scmbaCSREtaQDQU").call(run_input=run_input)

        dataset_id = run.default_dataset_id
        hasResults = False
        if dataset_id:
            for results in client_Apify.dataset(dataset_id).iterate_items():
                hasResults = True
                write_to_jsonl("success", False, "rolling", "google_hotels.jsonl", results)
        if not hasResults:
            write_to_jsonl(
                "noResults", False, "rolling", "google_hotels.jsonl",
                {"checkInDate": dateTimeTommorow, "checkOutDate": dateTimeDayAfterTommorow},
            )
    except Exception as e:
        # NOTE: previously this called primary_google_flights() (copy-paste bug —
        # wrong function AND wrong category). Removed entirely: this function is
        # already the fallback, so calling a primary here just risks a
        # backup<->primary ping-pong / infinite recursion if both are broken
        # (which they currently are — primary has no SerpApi credits left).
        write_to_jsonl(
            "ingestion_totalFail", False, "rolling", "google_hotels.jsonl",
            {
                "checkInDate": dateTimeTommorow,
                "checkOutDate": dateTimeDayAfterTommorow,
                "error": str(e),
            },
        )


def backup_google_flights():
    """Rolling baseline: always searches a flight departing 'tomorrow'."""
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
                    write_to_jsonl("success", False, "rolling", "google_flights.jsonl", flight)
        if not hasResults:
            write_to_jsonl(
                "noResults", False, "rolling", "google_flights.jsonl",
                {"outbound_date": dateTimeTommorow},
            )
    except Exception as e:
        # NOTE: previously called primary_google_trends() — wrong function AND
        # wrong category (flights backup was falling through to trends primary).
        # Same reasoning as backup_google_hotels(): removed the cross-call.
        write_to_jsonl(
            "ingestion_totalFail", False, "rolling", "google_flights.jsonl",
            {"outbound_date": dateTimeTommorow, "error": str(e)},
        )


def backup_google_trends():
    """
    Rolling/refresh trends pull. Switched from 'now 7-d' back to 'today 3-m'
    per the final plan: run this DAILY, APPEND (don't overwrite), and let
    dateTime_collected mark each day's full-window batch. Each batch is
    self-consistently normalized (0-100) against its own 3-month window —
    do NOT merge rows across different dateTime_collected values as if they
    were one continuous series; pick one batch (usually the latest) per analysis.
    """
    try:
        run_input = {
            "mode": "keyword",
            "keyword": "Masskara",
            "predefinedTimeframe": "today 3-m",
            "geo": "PH",
            "fetchRegionalData": False,
            "proxyConfiguration": {"useApifyProxy": True},
        }

        run = client_Apify.actor("nWhM7vTPu16lcwuIg").call(run_input=run_input)

        dataset_id = run.default_dataset_id
        hasResults = False

        if dataset_id:
            for results in client_Apify.dataset(dataset_id).iterate_items():
                for timestamp, value in results.get("timeline_data", {}).get("Masskara", {}).items():
                    hasResults = True
                    write_to_jsonl(
                        "success", False, "rolling", "google_trends.jsonl",
                        {"timestamp": timestamp, "value": value},
                    )
        if not hasResults:
            write_to_jsonl(
                "noResults", False, "rolling", "google_trends.jsonl",
                {"lookup_date": dateTimeToday},
            )
    except Exception as e:
        write_to_jsonl(
            "ingestion_totalFail", False, "rolling", "google_trends.jsonl",
            {"lookup_date": dateTimeToday, "error": str(e)},
        )


# =========================================================================
# BACKUP SOURCES — FESTIVAL TARGET (fixed Oct 9-12 dates)
# NEWLY IMPLEMENTED. This is what actually lets you compute travel_lead_time /
# hotel_lead_time / *_price_velocity: the rolling functions above only ever
# price a different flight/stay each day, they never re-price the SAME
# festival-window date at shrinking lead times.
# =========================================================================

def backup_google_flights_festival():
    """
    Re-queries each MassKara event date (Oct 9-12) every day this script runs.
    lead_time_days = (target_date - dateTime_collected) can be derived in
    Phase 3 straight from the fields written here.
    Each date's actor call is wrapped individually so one bad day doesn't
    take down the other three.
    """
    for target_date in FESTIVAL_DATES:
        try:
            run_input = {
                "arrival_id": "BCD",
                "currency": "PHP",
                "departure_id": "MNL",
                "exclude_basic": False,
                "fetch_booking_options": False,
                "gl": "ph",
                "hl": "en",
                "outbound_date": target_date,
            }

            run = client_Apify.actor("1dYHRKkEBHBPd0JM7").call(run_input=run_input)

            dataset_id = run.default_dataset_id
            hasResults = False
            if dataset_id:
                for results in client_Apify.dataset(dataset_id).iterate_items():
                    for flight in results.get("all_flights", []):
                        hasResults = True
                        write_to_jsonl(
                            "success", False, "festival_target", "google_flights.jsonl",
                            {**flight, "target_date": target_date},
                        )
            if not hasResults:
                write_to_jsonl(
                    "noResults", False, "festival_target", "google_flights.jsonl",
                    {"outbound_date": target_date, "target_date": target_date},
                )
        except Exception as e:
            write_to_jsonl(
                "ingestion_totalFail", False, "festival_target", "google_flights.jsonl",
                {"outbound_date": target_date, "target_date": target_date, "error": str(e)},
            )


def backup_google_hotels_festival():
    """
    Re-queries a one-night stay for each night of the festival window
    (check-in Oct 9, 10, 11, 12 -> check-out the following day) every day
    this script runs, so nightly rate can be tracked at shrinking lead times.
    """
    for check_in in FESTIVAL_DATES:
        check_out = (datetime.strptime(check_in, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            run_input = {
                "adults": 1,
                "currency": "PHP",
                "rooms": 1,
                "searches": [
                    {"location": "Bacolod", "checkInDate": check_in, "checkOutDate": check_out}
                ],
                "sortBy": "relevance",
                "type": "hotels",
            }

            run = client_Apify.actor("H1scmbaCSREtaQDQU").call(run_input=run_input)

            dataset_id = run.default_dataset_id
            hasResults = False
            if dataset_id:
                for results in client_Apify.dataset(dataset_id).iterate_items():
                    hasResults = True
                    write_to_jsonl(
                        "success", False, "festival_target", "google_hotels.jsonl",
                        {**results, "target_date": check_in},
                    )
            if not hasResults:
                write_to_jsonl(
                    "noResults", False, "festival_target", "google_hotels.jsonl",
                    {"checkInDate": check_in, "checkOutDate": check_out, "target_date": check_in},
                )
        except Exception as e:
            write_to_jsonl(
                "ingestion_totalFail", False, "festival_target", "google_hotels.jsonl",
                {"checkInDate": check_in, "checkOutDate": check_out, "target_date": check_in, "error": str(e)},
            )


# =========================================================================
# PRIMARY SOURCES (SerpApi) — currently out of credits, unverified.
# Fixed the bugs I could find by inspection; treat as untested until credits
# are topped up. No primary_*_festival() versions yet — add them later,
# mirroring the backup_*_festival() pattern above, once primary is confirmed
# working again.
# =========================================================================

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
            "adults": "1",
        })

        has_error = "error" in data
        has_hotels = "properties" in data

        if not has_error and has_hotels:
            for hotel in data.get("properties", []):
                write_to_jsonl(
                    "success", True, "rolling", "google_hotels.jsonl",
                    {
                        "hotel_name": hotel.get("name", "Unknown Hotel"),
                        "lowest_Rate": (hotel.get("rate_per_night") or {}).get("lowest", "N/A"),
                        "check_in": dateTimeTommorow,
                        "check_out": dateTimeDayAfterTommorow,
                    },
                )
        else:
            write_to_jsonl(
                "error", True, "rolling", "google_hotels.jsonl",
                {"check_in_date": dateTimeTommorow, "check_out_date": dateTimeDayAfterTommorow},
            )
    except Exception as e:
        print(f"!!! primary_google_hotels() error ({e}), switching to backup !!!")
        backup_google_hotels()


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
            "sort_by": "2",
        })

        has_error = "error" in data
        has_flights = "best_flights" in data or "other_flights" in data

        if not has_error and has_flights:
            flights = data.get("best_flights", []) + data.get("other_flights", [])
            for flight in flights:
                write_to_jsonl("success", True, "rolling", "google_flights.jsonl", flight)
        else:
            write_to_jsonl(
                "error", True, "rolling", "google_flights.jsonl",
                {"outbound_date": dateTimeTommorow},
            )
    except Exception as e:
        print(f"!!! primary_google_flights() error ({e}), switching to backup !!!")
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
            "date": "today 3-m",
        })

        # BUG FIX: original was `if "error" or "Error" in results:` which — due to
        # operator precedence — evaluates to `"error" or ("Error" in results)`.
        # "error" is a non-empty string (always truthy), so this branch was
        # ALWAYS taken regardless of what `results` actually contained. Every
        # primary trends call was silently being logged as noResults even on
        # success. Fixed to check both keys properly.
        if ("error" in results) or ("Error" in results):
            write_to_jsonl("noResults", True, "rolling", "google_trends.jsonl", {"lookup_date": dateTimeToday})
            return

        # BUG FIX: `results.iterate_items()` doesn't exist on SerpApi's search()
        # return value (that's an Apify Client method, copy-pasted from the
        # backup function). SerpApi's TIMESERIES response shape is a dict:
        # results["interest_over_time"]["timeline_data"] -> list of
        # {"date", "timestamp", "values": [{"query", "value", "extracted_value"}]}.
        # This is structurally different from the Apify backup's
        # {timestamp: value} dict shape — that's expected, they're different
        # providers. Parsing below is UNTESTED (no SerpApi credits to verify
        # against a live response) — double check field names once credits
        # are available again.
        timeline = results.get("interest_over_time", {}).get("timeline_data", [])
        hasResults = False
        for point in timeline:
            values = point.get("values", [])
            extracted_value = values[0].get("extracted_value") if values else None
            if extracted_value is not None:
                hasResults = True
                write_to_jsonl(
                    "success", True, "rolling", "google_trends.jsonl",
                    {"timestamp": point.get("timestamp"), "value": extracted_value},
                )
        if not hasResults:
            write_to_jsonl("noResults", True, "rolling", "google_trends.jsonl", {"lookup_date": dateTimeToday})
    except Exception as e:
        print(f"!!! primary_google_trends() error ({e}), switching to backup !!!")
        backup_google_trends()


if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    # primary_google_hotels()
    # primary_google_flights()
    # primary_google_trends()

    # comment these once the primary sources are no longer kaput

    backup_google_hotels()
    backup_google_flights()
    backup_google_trends()

    # newly implemented: fixed festival-date tracking (Oct 9-12)
    backup_google_flights_festival()
    backup_google_hotels_festival()

    print("Ingestion complete. Check data/raw/ for output.")
    print("Make sure you didn't edit the primary ingestions while they're\ncommented out like a dum-dum")