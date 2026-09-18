"""
Phase 3 — Data Transformation Pipeline
Processes raw Google Flights, Hotels, and Trends data into clean CSVs
and compiles the analytical master dataset.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "masskara" / "analysis"


def extract_flight_leg_info(row):
    flights_data = row.get("flights")
    if isinstance(flights_data, list) and len(flights_data) > 0:
        leg = flights_data[0]
        dep_airport = leg.get("departure_airport") or {}
        arr_airport = leg.get("arrival_airport") or {}
        return pd.Series({
            "airline": leg.get("airline"),
            "flight_number": leg.get("flight_number"),
            "airplane": leg.get("airplane"),
            "travel_class": leg.get("travel_class"),
            "departure_airport": dep_airport.get("id"),
            "departure_time": dep_airport.get("time"),
            "arrival_airport": arr_airport.get("id"),
            "arrival_time": arr_airport.get("time"),
            "leg_duration": leg.get("duration"),
        })
    return pd.Series({})


def clean_raw_data():
    """Week 9: Load raw JSONL, standardize columns, and save cleaned CSVs."""
    print("Loading and cleaning raw data...")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Flights
    raw_flights = RAW_DIR / "google_flights.jsonl"
    if raw_flights.exists():
        df_flights = pd.read_json(raw_flights, lines=True)
        df_flights.columns = [c.strip().lower().replace(" ", "_") for c in df_flights.columns]
        legs = df_flights.apply(extract_flight_leg_info, axis=1)
        cols_to_drop = list(legs.columns) + ["flights", "booking_token", "airline_logo"]
        df_flights = df_flights.drop(columns=cols_to_drop, errors="ignore")
        df_flights = pd.concat([df_flights, legs], axis=1)
        df_flights["price"] = pd.to_numeric(df_flights["price"], errors="coerce")
        df_flights.to_csv(PROCESSED_DIR / "cleaned_flights.csv", index=False)

    # 2. Hotels
    raw_hotels = RAW_DIR / "google_hotels.jsonl"
    if raw_hotels.exists():
        df_hotels = pd.read_json(raw_hotels, lines=True)
        df_hotels.columns = [c.strip().lower().replace(" ", "_") for c in df_hotels.columns]
        df_hotels["price_php"] = df_hotels["lowest_rate"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        df_hotels["price_php"] = pd.to_numeric(df_hotels["price_php"], errors="coerce")
        df_hotels.to_csv(PROCESSED_DIR / "cleaned_hotels.csv", index=False)

    # 3. Trends
    raw_trends = RAW_DIR / "google_trends.jsonl"
    if raw_trends.exists():
        df_trends = pd.read_json(raw_trends, lines=True)
        df_trends.columns = [c.strip().lower().replace(" ", "_") for c in df_trends.columns]
        df_trends["value"] = pd.to_numeric(df_trends["value"], errors="coerce")
        df_trends.to_csv(PROCESSED_DIR / "cleaned_trends.csv", index=False)


def build_master_dataset():
    """Week 10: Aggregate daily metrics and build master analysis mart."""
    print("Building master analytical dataset...")
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    df_flights = pd.read_csv(PROCESSED_DIR / "cleaned_flights.csv")
    df_hotels = pd.read_csv(PROCESSED_DIR / "cleaned_hotels.csv")
    df_trends = pd.read_csv(PROCESSED_DIR / "cleaned_trends.csv")

    df_flights["date_collected"] = pd.to_datetime(df_flights["datetime_collected"]).dt.date
    df_hotels["date_collected"] = pd.to_datetime(df_hotels["datetime_collected"]).dt.date
    df_trends["date"] = pd.to_datetime(df_trends["timestamp"]).dt.date

    # Aggregate Flights
    fest_flights = df_flights[df_flights["collection_mode"] == "festival_target"]
    rolling_flights = df_flights[df_flights["collection_mode"] == "rolling"]

    daily_fest_flights = fest_flights.groupby("date_collected").agg(
        flight_fest_min_price=("price", "min"),
        flight_fest_max_price=("price", "max"),
        flight_fest_median_price=("price", "median"),
        flight_fest_mean_price=("price", "mean"),
        flight_fest_quote_count=("price", "count"),
    ).reset_index()

    daily_rolling_flights = rolling_flights.groupby("date_collected").agg(
        flight_rolling_min_price=("price", "min"),
        flight_rolling_max_price=("price", "max"),
        flight_rolling_median_price=("price", "median"),
        flight_rolling_mean_price=("price", "mean"),
        flight_rolling_quote_count=("price", "count"),
    ).reset_index()

    daily_flights = daily_fest_flights.merge(daily_rolling_flights, on="date_collected", how="outer")

    # Aggregate Hotels
    fest_hotels = df_hotels[df_hotels["collection_mode"] == "festival_target"]
    rolling_hotels = df_hotels[df_hotels["collection_mode"] == "rolling"]

    daily_fest_hotels = fest_hotels.groupby("date_collected").agg(
        hotel_fest_min_price=("price_php", "min"),
        hotel_fest_max_price=("price_php", "max"),
        hotel_fest_median_price=("price_php", "median"),
        hotel_fest_mean_price=("price_php", "mean"),
        hotel_fest_quote_count=("price_php", "count"),
    ).reset_index()

    daily_rolling_hotels = rolling_hotels.groupby("date_collected").agg(
        hotel_rolling_min_price=("price_php", "min"),
        hotel_rolling_max_price=("price_php", "max"),
        hotel_rolling_median_price=("price_php", "median"),
        hotel_rolling_mean_price=("price_php", "mean"),
        hotel_rolling_quote_count=("price_php", "count"),
    ).reset_index()

    daily_hotels = daily_fest_hotels.merge(daily_rolling_hotels, on="date_collected", how="outer")

    # Aggregate Trends
    daily_trends = df_trends.groupby("date").agg(
        trend_search_score=("value", "max")
    ).reset_index().rename(columns={"date": "date_collected"})

    # Merge into Master Mart
    master_df = daily_trends.merge(daily_flights, on="date_collected", how="inner")
    master_df = master_df.merge(daily_hotels, on="date_collected", how="left")
    master_df = master_df.sort_values("date_collected").reset_index(drop=True)

    # Feature Engineering
    master_df["flight_price_premium"] = master_df["flight_fest_median_price"] / master_df["flight_rolling_median_price"]
    master_df["hotel_price_premium"] = master_df["hotel_fest_median_price"] / master_df["hotel_rolling_median_price"]
    master_df["trend_velocity_7d"] = master_df["trend_search_score"].pct_change(periods=7)

    master_df["trend_score_lag_1d"] = master_df["trend_search_score"].shift(1)
    master_df["trend_score_lag_2d"] = master_df["trend_search_score"].shift(2)
    master_df["trend_score_lag_3d"] = master_df["trend_search_score"].shift(3)

    master_df["flight_median_change_1d"] = master_df["flight_fest_median_price"].diff(1)
    master_df["hotel_median_change_1d"] = master_df["hotel_fest_median_price"].diff(1)

    dates = pd.to_datetime(master_df["date_collected"])
    festival_start = pd.to_datetime("2026-10-09")
    master_df["days_to_festival"] = (festival_start - dates).dt.days

    out_file = ANALYSIS_DIR / "master.csv"
    master_df.to_csv(out_file, index=False)
    print(f"Saved master dataset to {out_file} (Shape: {master_df.shape})")


def transform():
    clean_raw_data()
    build_master_dataset()


if __name__ == "__main__":
    transform()
    print("Transformation complete. Check data/processed/ for output.")
