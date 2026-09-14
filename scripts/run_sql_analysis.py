"""
Week 8 — SQL Fundamentals Runner
Populates data/masskara.db from data/raw/ and executes the analytical SQL queries.
"""

import json
import os
import re
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "masskara.db")


def clean_price(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_trend_date(raw_ts):
    if not raw_ts:
        return None
    raw_str = str(raw_ts).strip()
    if raw_str.isdigit():
        try:
            return datetime.fromtimestamp(int(raw_str), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None
    if len(raw_str) >= 10:
        return raw_str[:10]
    return raw_str


def build_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS hotels;")
    cur.execute("""
        CREATE TABLE hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_collected TEXT,
            status TEXT,
            is_primary_source INTEGER,
            collection_mode TEXT,
            hotel_name TEXT,
            price_php REAL,
            check_in TEXT,
            check_out TEXT,
            target_date TEXT
        );
    """)

    cur.execute("DROP TABLE IF EXISTS flights;")
    cur.execute("""
        CREATE TABLE flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_collected TEXT,
            status TEXT,
            is_primary_source INTEGER,
            collection_mode TEXT,
            airline TEXT,
            flight_number TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            duration_minutes INTEGER,
            price_php REAL,
            target_date TEXT
        );
    """)

    cur.execute("DROP TABLE IF EXISTS trends;")
    cur.execute("""
        CREATE TABLE trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_collected TEXT,
            status TEXT,
            is_primary_source INTEGER,
            collection_mode TEXT,
            raw_timestamp TEXT,
            interest_date TEXT,
            interest_value INTEGER
        );
    """)

    hotel_file = os.path.join(RAW_DIR, "google_hotels.jsonl")
    if os.path.exists(hotel_file):
        with open(hotel_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                cur.execute("""
                    INSERT INTO hotels (
                        date_collected, status, is_primary_source, collection_mode,
                        hotel_name, price_php, check_in, check_out, target_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("dateTime_collected"),
                    row.get("status"),
                    1 if row.get("primary_source") else 0,
                    row.get("collection_mode"),
                    row.get("hotel_name"),
                    clean_price(row.get("lowest_Rate")),
                    row.get("check_in"),
                    row.get("check_out"),
                    row.get("target_date") or row.get("check_in")
                ))

    flight_file = os.path.join(RAW_DIR, "google_flights.jsonl")
    if os.path.exists(flight_file):
        with open(flight_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                flights_list = row.get("flights", [])
                airline = None
                flight_num = None
                dep_time = None
                arr_time = None
                dur = row.get("total_duration")
                if flights_list and isinstance(flights_list, list):
                    first_leg = flights_list[0]
                    airline = first_leg.get("airline")
                    flight_num = first_leg.get("flight_number")
                    dep_time = (first_leg.get("departure_airport") or {}).get("time")
                    arr_time = (first_leg.get("arrival_airport") or {}).get("time")
                    if dur is None:
                        dur = first_leg.get("duration")

                cur.execute("""
                    INSERT INTO flights (
                        date_collected, status, is_primary_source, collection_mode,
                        airline, flight_number, departure_time, arrival_time,
                        duration_minutes, price_php, target_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("dateTime_collected"),
                    row.get("status"),
                    1 if row.get("primary_source") else 0,
                    row.get("collection_mode"),
                    airline,
                    flight_num,
                    dep_time,
                    arr_time,
                    dur,
                    clean_price(row.get("price")),
                    row.get("target_date")
                ))

    trends_file = os.path.join(RAW_DIR, "google_trends.jsonl")
    if os.path.exists(trends_file):
        with open(trends_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                raw_ts = row.get("timestamp")
                cur.execute("""
                    INSERT INTO trends (
                        date_collected, status, is_primary_source, collection_mode,
                        raw_timestamp, interest_date, interest_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("dateTime_collected"),
                    row.get("status"),
                    1 if row.get("primary_source") else 0,
                    row.get("collection_mode"),
                    str(raw_ts),
                    parse_trend_date(raw_ts),
                    row.get("value")
                ))

    conn.commit()
    conn.close()
    print(f"Database successfully refreshed at: {DB_PATH}")


def execute_queries():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    queries = [
        (
            "Query 1A: Festival vs Rolling Flight Price Comparison",
            """
            SELECT 
                collection_mode,
                COUNT(*) AS total_quotes,
                ROUND(MIN(price_php), 2) AS min_price_php,
                ROUND(AVG(price_php), 2) AS avg_price_php,
                ROUND(MAX(price_php), 2) AS max_price_php
            FROM flights
            WHERE status = 'success' AND price_php IS NOT NULL
            GROUP BY collection_mode;
            """
        ),
        (
            "Query 1B: Festival vs Rolling Hotel Price Comparison",
            """
            SELECT 
                collection_mode,
                COUNT(*) AS total_quotes,
                ROUND(MIN(price_php), 2) AS min_price_php,
                ROUND(AVG(price_php), 2) AS avg_price_php,
                ROUND(MAX(price_php), 2) AS max_price_php
            FROM hotels
            WHERE status = 'success' AND price_php IS NOT NULL
            GROUP BY collection_mode;
            """
        ),
        (
            "Query 2: Daily Festival Flight Escalation Across Collection Dates",
            """
            SELECT 
                date_collected,
                COUNT(*) AS flight_options,
                ROUND(MIN(price_php), 2) AS min_fare_php,
                ROUND(AVG(price_php), 2) AS avg_fare_php,
                ROUND(MAX(price_php), 2) AS max_fare_php
            FROM flights
            WHERE collection_mode = 'festival_target' AND status = 'success' AND price_php IS NOT NULL
            GROUP BY date_collected
            ORDER BY date_collected ASC;
            """
        ),
        (
            "Query 3: Public Search Interest vs Festival Flight Pricing",
            """
            WITH daily_trend AS (
                SELECT 
                    date_collected,
                    MAX(interest_value) AS peak_search_interest,
                    ROUND(AVG(interest_value), 1) AS avg_search_interest
                FROM trends
                WHERE status = 'success'
                GROUP BY date_collected
            ),
            daily_festival_flight AS (
                SELECT 
                    date_collected,
                    MIN(price_php) AS min_festival_fare,
                    ROUND(AVG(price_php), 2) AS avg_festival_fare
                FROM flights
                WHERE collection_mode = 'festival_target' AND status = 'success'
                GROUP BY date_collected
            )
            SELECT 
                f.date_collected,
                t.peak_search_interest,
                t.avg_search_interest,
                f.min_festival_fare,
                f.avg_festival_fare
            FROM daily_festival_flight f
            LEFT JOIN daily_trend t ON f.date_collected = t.date_collected
            ORDER BY f.date_collected ASC;
            """
        ),
        (
            "Query 4: Airline Pricing Breakdown for Festival Target Flights",
            """
            SELECT 
                airline,
                COUNT(*) AS total_flights,
                ROUND(MIN(price_php), 2) AS min_fare_php,
                ROUND(AVG(price_php), 2) AS avg_fare_php,
                ROUND(MAX(price_php), 2) AS max_fare_php
            FROM flights
            WHERE collection_mode = 'festival_target' AND status = 'success' AND airline IS NOT NULL
            GROUP BY airline
            ORDER BY avg_fare_php ASC;
            """
        ),
    ]

    for title, sql in queries:
        print(f"\n=======================================================")
        print(f" {title}")
        print(f"=======================================================")
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        print(" | ".join(f"{c:>18}" for c in cols))
        print("-" * (21 * len(cols)))
        for row in cur.fetchall():
            formatted = []
            for item in row:
                formatted.append(f"{str(item):>18}")
            print(" | ".join(formatted))

    conn.close()


if __name__ == "__main__":
    build_database()
    execute_queries()
