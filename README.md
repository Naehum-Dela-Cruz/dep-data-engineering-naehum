# MassKara Festival Google Trends Interest & MNL-BCD Travel Price Surge Tracker

## Problem Statement
This builder wants to answer: "Is there a correlation between an uptick in Google Trends' Interest Over Time metric and MNL-BCD flight/BCD hotel price surges leading up to the Bacolod MassKara Festival in October?"

## Audience
This project is for budget-conscious travelers looking to be able to get ahead of the prices; business owners wanting to make informed data-driven descisions in the face of a potential surge in tourism; and other researchers looking into a similar or related topic.

## How To Run
Run these commands from the repository root.

### 1. Install dependencies
```powershell
pip install -r requirements.txt
```
### 2. Configure API credentials
Create a .env file in the project root:
```
SERPAPI_API_KEY=your_serpapi_key
APIFY_API_KEY=your_apify_key
```
### 3. Run The Full Pipeline
No ingestion (use stored data) (Recommended):
```
python scripts/run_pipeline.py
```
With Ingestion (get latest data):
```
python scripts/run_pipeline.py --with-ingest
```
### (Optional) Run individual scripts
```
python scripts/ingest.py
python scripts/transform.py
python scripts/run_sql_analysis.py
```

## KPIs or Key Metrics
The main metrics this builder wishes to track are categorized into three distinct layers:

#### 1. Public Demand & Search Metrics (Google Trends)
-`Peak Search Index (0-100)`: The maximum search volume score registered leading up to the festival, indicating the highest point of public curiosity. This is NOT the actual number of searches as Google Trends Interest Over Time (IOT) data scales on 0-100 with 100 being the highest number of searches and the rest being scaled relative to that peak.

-`Interest Velocity (Week-over-Week)`: The percentage change in search volume between consecutive weeks to identify sudden inflection points or viral spikes.

-`Cumulative Search Volume`: The area under the curve (total sum of search values) over the pre-festival tracking window to measure total sustained interest.

#### 2. Price Surge & Inflation Metrics (Flights & Hotels)
-`Festival Price Premium`: The percentage difference between average MNL-BCD flight ticket prices or hotel room rates during the festival target dates for October 9-13 versus standard baseline periods gathered beforehand from the rolling price record.

-`Minimum Price Escalation`: Track how the lowest available one-way flight price shifts as the collection date gets closer to October 9, and then past it with rolling dates once the event has ended.

#### 3. Correlation & Timing Metrics
-`Cross-Correlation Coefficient`: A statistical measure (Spearman's) evaluating how closely fluctuations in Google Trends scores track with flight and hotel price jumps. 

-`Lag Time to Surge (Lead Time)`: The time gap (in days) between an initial spike in search interest and the subsequent upward movement in airfares and accommodation rates. Look at it in day-level shifts (e.g., does a spike in Google Trends on Day T trigger a price jump on Day T+2 or T+3?)—people rarely search for a festival term and book a flight within the exact same hour; there is usually a consideration window.

<!-- #### 1. General Analytics
- `trends_price_correlation`: The calculated statistical correlation coefficient between trends velocity and the median pricing of accommodations and flights.

#### 2. Trends Metrics
- `trends_velocity`: The week-over-week percentage increase/decrease in Google Trend's Interest Over Time value for relevant keywords.

#### 3. Flight Metrics
- `travel_lead_time`: The number of days remaining until the festival peak before Manila-to-Bacolod (MNL-BCD) plane ticket prices spike past a dynamic multiplier threshold (e.g., greater than 1.5x of the average off-season rolling price).
- `travel_cooldown_time`: The number of days post-festival before MNL-BCD plane ticket prices drop back down below the baseline threshold.
- `travel_price_velocity`: The week-over-week percentage change in minimum and median MNL-BCD flight costs.

#### 4. Hotel Metrics
- `hotel_lead_time`: The number of days remaining until the festival peak before Bacolod City accommodation and hotel booking prices spike past a baseline threshold.
- `hotel_cooldown_time`: The number of days post-festival before BCD hotel booking prices stabilize below the surge threshold.
- `hotel_price_velocity`: The week-over-week percentage change in nightly hotel rates across listed Bacolod city accommodations. -->

## Data Source Notes

All data ingestion and transformation pipelines are located under `scripts/`:
- **Ingestion**: `python scripts/ingest.py` (pulls raw data into `data/raw/`)
- **Transformation & Mart Building**: `python scripts/transform.py` (cleans raw data and produces the analytical master dataset in `data/processed/masskara/analysis/master.csv`)
- **Automation**: Both pipelines are scheduled via GitHub Actions (`.github/workflows/ingest.yml` daily at 18:20 UTC, and `.github/workflows/transform.yml` at 22:20 UTC).

### Primary Source
- Name: SERP API
- URL: https://serpapi.com/playground
- Format: json
- Coverage: flight prices (by cheapest), hotel prices (by Google Search 'relevance'), interest over time metric
- Why it fits the problem: SERP API directly scrapes Google Flight, Hotel, and Trends search results
- Known limitations: free tier is limited to 250 request per month (should need around 90)

### Fallback Source 1 (Hotel)
- Name: kaix/google-hotels-scraper
- URL: https://console.apify.com/actors/H1scmbaCSREtaQDQU
- Format: JSONL
- Coverage: hotel prices, date
- Why it could still work: directly scrapes Google Hotel
- Known limitations: $5 Free limit. ~$0.1/1k Hotels

### Fallback Source 2 (Flight)
- Name: johnvc/Google-Flights-Data-Scraper-Flight-and-Price-Search
- URL: https://console.apify.com/actors/1dYHRKkEBHBPd0JM7
- Format: JSONL
- Coverage: flight prices, date
- Why it could still work: directly scrapes google flights
- Known limitations: $5 Free limit. ~$30/1000 Pages

### Fallback Source 3 (Trend)
- Name: data_xplorer/google-trends-fast-scraper
- URL: https://console.apify.com/actors/nWhM7vTPu16lcwuIg/
- Format: JSONL
- Coverage: interest over time metric, date
- Why it could still work: directly scrapes Google Trends interest over time results
- Known limitations: $5 Free limit. ~$2/1k Results

<!-- ## Likely Data Source
This builder will explore and integrate the following data endpoints:
*   **Google Flights Pricing:** Timestamps, and price metrics extracted via **https://serpapi.com** free-tier.
*   **Google Hotels Pricing:** Timestamps, and price metrics extracted via **https://serpapi.com** free-tier.
*   **Google Trends Interest Over Time:** Timestamps, and interest metrics extracted via **https://serpapi.com** free-tier. -->

## Processed Data Plan

### Storage Architecture

```text
data/raw/*.jsonl
        |
        v
`transform.py`
        |
        +-- `cleaned_flights.csv`
        +-- `cleaned_hotels.csv`
        +-- `cleaned_trends.csv`
        +-- `master.csv`
```

### Processed Flights

File: `data/processed/cleaned_flights.csv`

- **Grain:** One row per flight option collected on a specific date.
- **Identifier:** The combination of `datetime_collected`, `collection_mode`, `flight_number`, and `departure_time`.
- **Purpose:** Stores cleaned MNL-to-BCD flight quotes.

| Column | Meaning |
|---|---|
| `datetime_collected` | Date the quote was collected |
| `status` | Ingestion result, such as `success` |
| `primary_source` | Whether the quote came from SerpApi |
| `collection_mode` | `rolling` baseline or `festival_target` |
| `total_duration` | Total flight duration in minutes |
| `price` | One-way fare in PHP |
| `type` | Flight type, such as one-way |
| `target_date` | Festival target travel date, when applicable |
| `airline` | Airline name |
| `flight_number` | Flight identifier |
| `airplane` | Aircraft type |
| `travel_class` | Cabin class |
| `departure_airport` | Origin airport code |
| `departure_time` | Scheduled departure timestamp |
| `arrival_airport` | Destination airport code |
| `arrival_time` | Scheduled arrival timestamp |
| `leg_duration` | Duration of the first flight leg |

### Processed Hotels

File: `data/processed/cleaned_hotels.csv`

- **Grain:** One row per hotel quote collected for a specific stay window.
- **Identifier:** The combination of `datetime_collected`, `collection_mode`, `hotel_name`, and `check_in`.
- **Purpose:** Stores cleaned Bacolod hotel rates.

| Column | Meaning |
|---|---|
| `datetime_collected` | Date the quote was collected |
| `status` | Ingestion result |
| `primary_source` | Whether the quote came from SerpApi |
| `collection_mode` | `rolling` baseline or `festival_target` |
| `hotel_name` | Accommodation name |
| `lowest_rate` | Original hotel rate string |
| `check_in` | Stay check-in date |
| `check_out` | Stay check-out date |
| `target_date` | Festival target date, when applicable |
| `price_php` | Cleaned numeric hotel price in PHP |

### Processed Google Trends

File: `data/processed/cleaned_trends.csv`

- **Grain:** One row per Google Trends observation date within an ingestion snapshot.
- **Identifier:** The combination of `datetime_collected`, `timestamp`, and `collection_mode`.
- **Purpose:** Stores cleaned Google Trends interest values for `Masskara`.

| Column | Meaning |
|---|---|
| `datetime_collected` | Date the trends data was collected |
| `status` | Ingestion result |
| `primary_source` | Whether the data came from SerpApi |
| `collection_mode` | Trends collection mode |
| `timestamp` | Date represented by the trends observation |
| `value` | Google Trends interest index from 0 to 100 |

### Analytical Master Dataset

File: `data/processed/masskara/analysis/master.csv`

- **Grain:** One row per observation date.
- **Primary key:** `date_collected`.
- **Purpose:** Combines trends, flight, and hotel metrics for analysis.

The master dataset contains:

- Daily Google Trends search scores
- Festival and rolling flight price summaries
- Festival and rolling hotel price summaries
- Flight and hotel price premiums
- Seven-day trends velocity
- One-, two-, and three-day trends lags
- One-day flight and hotel price changes
- Days remaining until the festival

## Cleaning Decisions

| Raw issue | Cleaning action | Result |
|---|---|---|
| Nested flight legs | Extracted the first flight leg into separate columns | Airline, airports, times, and duration can be analyzed as normal columns |
| Currency strings such as `₱1,211` | Removed currency symbols and commas, then converted to numeric values | Stored as `price_php` |
| Invalid numeric values | Converted with `pd.to_numeric(..., errors="coerce")` | Invalid values become `NaN` and are excluded from aggregate calculations |
| Missing festival target dates in rolling records | Preserved as empty values | Rolling records remain distinguishable from festival-target records |
| Raw flight metadata not needed for price analysis | Removed nested blobs such as `flights`, `booking_token`, and `airline_logo` | Processed files remain smaller and easier to query |
| Different source date ranges | Joined trends with flight observations using an inner join | The master dataset contains dates with active flight and trend observations |

## Validation and Reproducibility

Validation is implemented in `scripts/transform.py`.

The transformation checks that:

- The master dataset is not empty.
- `date_collected` contains no null values.
- `date_collected` is unique in the master dataset.
- Google Trends scores are within the range 0 to 100.
- Festival and rolling prices are positive when present.
- `collection_mode` contains only `rolling` or `festival_target`.
- `days_to_festival` is not negative.
- The same raw input produces the same processed output when the transform script is run repeatedly.

Expected missing values include:

- `target_date` for rolling records
- Initial lag values for the first one to three observation dates
- Initial seven-day velocity values
- Price fields when a source returns no usable quote

## SQL Analysis

SQL analysis is documented in `scripts/queries.sql` and executed by:

```powershell
python run_sql_analysis.py
```

The queries answer these business questions:

1. What is the difference between festival and rolling flight and hotel prices?
2. How do festival flight prices change as the travel date approaches?
3. How does Google Trends search interest align with festival flight prices?
4. Which airline offers the lowest festival flight prices?

The SQL runner refreshes:

```text
`masskara.db`
```

and prints the query results in the terminal.

## Data Quality, Validation & Reproducibility (Week 11)

### Cleaning Decisions Log
| Issue / Raw State | Action Taken | Rationale |
|---|---|---|
| **Nested Flight Legs (`flights`)** | Unnested first flight leg into explicit columns (`airline`, `flight_number`, departure/arrival airport & times). | Tabular models cannot query nested JSON lists; separating legs allows airline pricing breakdowns. |
| **Hotel Rates as Currency Strings (`"₱1,211"`)** | Stripped `₱`, commas, and whitespace using regex `r"[^\d.]"`, then cast to `float`. | Financial metrics (min, mean, median, velocity) require native numeric types. |
| **Missing `target_date` in Rolling Scrapes** | Kept as `NaN` / empty for `rolling` rows, populated only for `festival_target`. | Rolling scrapes measure the next-day baseline and have no fixed October target date. Preserving `NaN` prevents false grouping. |
| **Multi-Leg Flight Blobs (`booking_token`, `airline_logo`)** | Dropped from processed output. | Token payloads and SVG URLs add noise and bloated file size without analytical value for price surge modeling. |
| **Unequal Time Horizons Across Sources** | Merged on `date_collected` using `inner` for flights/trends and `left` for hotels. | Trend data extends back to June, but flight/hotel scrapers only started September 2. Restricting the master mart to active scraper observation dates eliminates 90+ days of empty price rows. |

### Validation Rules in Pipeline (`scripts/transform.py`)
1. **Primary Key Integrity**: `date_collected` has zero nulls (`isna().sum() == 0`) and is 100% unique (`nunique() == len(df)`).
2. **Domain Range Boundaries**:
   - `trend_search_score` is strictly asserted to fall within `[0, 100]`.
   - All flight fares and hotel nightly rates must be strictly positive (`> 0`).
3. **Category Integrity**: `collection_mode` must only ever contain `festival_target` or `rolling`.
4. **Lead Time Sanity**: `days_to_festival` must remain positive (`>= 0`) leading up to October 9, 2026.
5. **Idempotence & Reproducibility**: Running `python scripts/transform.py` multiple times on identical raw inputs produces the exact same deterministic dataset without row duplications or side effects.

## Possible Final Dashboard
The presentation layer will be built as a single-page application divided into three clear analytical modules:

1. **The Executive Snapshot (Metric Cards)**
   - High-level metric callouts showing current median flight prices (MNL-BCD), current median hotel rates, this week's Interest Over Time value, and the overall correlation score.

2. **The Surge Timeline (Interactive Line Chart)**
   - A dual-axis time-series chart mapping `trends_velocity` directly against `travel_price_velocity` and `hotel_price_velocity` across a rolling 90-day window to visually isolate the price lag following an Interest Over Time spike.

3. **The Traveler's Action Center (Summary Data Table)**
   - A structured data table outputting the programmatic results for booking window strategies: `travel_lead_time`, `hotel_lead_time`, `travel_cooldown_time`, and `hotel_cooldown_time`.

## Builder's Notes

- As MassKara is usually held in October, this builder hopes to have already collected (Phase 2) and cleaned (Phase 3) data ranging as far back as August.

- This builder would've liked to do an analysis of the previous MassKara festival to contrast with the upcoming one, but SerpApi's Google Hotels and Google Flights scraper cannot view historical prices. (even tho the `vs. same period previous year` feature is in the page)

<!-- - This builder doesn't like being completely at the mercy of SerpApi. Alternative sources would be appreciated for redundancy. -->