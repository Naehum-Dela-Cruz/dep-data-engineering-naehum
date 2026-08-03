"""
Phase 2 — Data Ingestion
This script fetches Google Trends data for a specific query ("Masskara") in the Philippines
using the SerpApi service, and saves the resulting JSON response to the local data/raw directory.
"""
import json
import os
import serpapi
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Define the absolute path to the data/raw directory, located two levels up from this script.
RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
# Ensure the directory exists. Create it along with any necessary parent directories if it does not.
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def ingest():
    """
    Main function to orchestrate the data ingestion process.
    """
    def serp_google_interestOverTime():
        """
        Fetches Google Trends "Interest Over Time" data via SerpApi.
        The data is saved as a raw JSON file in the data/raw directory.
        """
        print("Fetching Google Trends data via SerpApi...")
        
        # Initialize the SerpApi client using the API key from environment variables
        client = serpapi.Client(api_key=os.environ.get("SERP_API_KEY"))
        
        # Execute the search query to Google Trends
        results = client.search({
            "engine": "google_trends",  # Specify the Google Trends engine
            "q": "Masskara",            # The search query
            "geo": "PH",                # Geographical location (Philippines)
            "data_type": "TIMESERIES",  # Fetch Interest Over Time data
            "hl": "en",                 # Host language
            "tz": "-480",               # Timezone offset
            "date": "now 1-d"           # Date range (Past day)
        })

        # Define the output file path within the raw data directory
        output_file = RAW_DATA_DIR / "masskara_google_trends.json" 
        
        # Open the file in write mode and dump the JSON response
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(results.as_dict(), f, indent=2, ensure_ascii=False)

        print(f"Successfully saved results to {output_file}")

    # Execute the API request function
    serp_google_interestOverTime()

if __name__ == "__main__":
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    ingest()
    print("Ingestion complete. Check data/raw/ for output.")
