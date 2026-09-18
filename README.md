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
- **Raw Layer (`data/raw/`)**: Append-only JSON Lines (`.jsonl`). Retains raw API responses from SerpApi and Apify fallbacks.
- **Processed Layer (`data/processed/`)**: Structured tabular files (`.parquet` or `.csv`). Columns are strictly typed, unnested, deduplicated, and currency symbols (`₱`) or epochs are parsed into native numbers and dates.

---

### Table 1: Processed Hotels (`processed_hotels`)
- **Grain:** One row = one hotel rate quote scraped on a specific collection date for a specific stay window.
- **Primary Key:** Composite (`date_collected`, `collection_mode`, `hotel_name`, `check_in_date`)

| Column | Meaning | Expected Type | Example |
|---|---|---|---|
| `record_id` | Unique MD5 hash of (date_collected, collection_mode, hotel_name, check_in_date) | `VARCHAR` | `"h_a8f9c12e..."` |
| `date_collected` | Date the data was collected | `DATE` (`YYYY-MM-DD`) | `2026-09-08` |
| `collection_mode` | Mode of scrape: `"rolling"` (baseline) vs `"festival_target"` (MassKara stay) | `VARCHAR` | `"festival_target"` |
| `hotel_name` | Cleaned name of the accommodation | `VARCHAR` | `"Park Inn by Radisson Bacolod"` |
| `check_in_date` | Check-in date for the booking | `DATE` (`YYYY-MM-DD`) | `2026-10-09` |
| `check_out_date` | Check-out date for the booking | `DATE` (`YYYY-MM-DD`) | `2026-10-13` |
| `num_nights` | Length of stay in nights (`check_out_date` - `check_in_date`) | `INTEGER` | `4` |
| `price_php` | Total or nightly quote in Philippine Pesos (numeric, stripped of symbols) | `FLOAT` | `7402.0` |
| `lead_time_days` | Booking lead time (`check_in_date` - `date_collected`) | `INTEGER` | `31` |
| `is_primary_source` | Whether record came from SerpApi (`TRUE`) or Apify (`FALSE`) | `BOOLEAN` | `TRUE` |

---

### Table 2: Processed Flights (`processed_flights`)
- **Grain:** One row = one flight option (MNL -> BCD) scraped on a specific collection date for a specific departure date.
- **Primary Key:** Composite (`date_collected`, `collection_mode`, `flight_number`, `departure_time`)

| Column | Meaning | Expected Type | Example |
|---|---|---|---|
| `record_id` | Unique MD5 hash of (date_collected, collection_mode, flight_number, departure_time) | `VARCHAR` | `"f_c3b8e91d..."` |
| `date_collected` | Date the scraper executed | `DATE` (`YYYY-MM-DD`) | `2026-09-08` |
| `collection_mode` | Mode of scrape: `"rolling"` vs `"festival_target"` | `VARCHAR` | `"festival_target"` |
| `target_travel_date` | Date of departure | `DATE` (`YYYY-MM-DD`) | `2026-10-09` |
| `origin_airport` | Origin IATA airport code | `VARCHAR(3)` | `"MNL"` |
| `destination_airport` | Destination IATA airport code | `VARCHAR(3)` | `"BCD"` |
| `airline` | Operating airline name | `VARCHAR` | `"Cebu Pacific"` |
| `flight_number` | Flight identifier code | `VARCHAR` | `"5J 475"` |
| `departure_time` | Scheduled local departure timestamp | `DATETIME` | `2026-10-09 17:25:00` |
| `arrival_time` | Scheduled local arrival timestamp | `DATETIME` | `2026-10-09 18:50:00` |
| `duration_minutes` | Total flight duration in minutes | `INTEGER` | `85` |
| `price_php` | One-way ticket price in PHP | `FLOAT` | `2396.0` |
| `lead_time_days` | Advance booking lead time (`target_travel_date` - `date_collected`) | `INTEGER` | `31` |
| `is_primary_source` | Whether record came from SerpApi (`TRUE`) or Apify (`FALSE`) | `BOOLEAN` | `TRUE` |

---

### Table 3: Processed Google Trends (`processed_trends`)
- **Grain:** One row = search interest score for a single date within a given collection snapshot.
- **Primary Key:** Composite (`date_collected`, `interest_date`, `keyword`)

| Column | Meaning | Expected Type | Example |
|---|---|---|---|
| `date_collected` | Date this 3-month trend batch was pulled | `DATE` (`YYYY-MM-DD`) | `2026-09-08` |
| `interest_date` | Date the search interest refers to | `DATE` (`YYYY-MM-DD`) | `2026-09-05` |
| `keyword` | Search keyword queried | `VARCHAR` | `"Masskara"` |
| `interest_index` | Normalized search volume index (0–100 scale) | `INTEGER` | `84` |
| `is_primary_source` | SerpApi (`TRUE`) or Apify (`FALSE`) | `BOOLEAN` | `TRUE` |

---

### Table 4: Analytical Mart / Aggregated Summary (`data/processed/masskara/analysis/master.csv`)
*(Feeds the final dashboard & correlation analysis directly)*
- **Grain:** One row = one observation date (`date_collected`).
- **Primary Key:** `date_collected`

| Column | Meaning | Expected Type | Source / Calculation |
|---|---|---|---|
| `date_collected` | Observation / scrape execution date | `DATE` (`YYYY-MM-DD`) | Join key across daily tables |
| `days_to_festival` | Days remaining until MassKara opening (Oct 9, 2026) | `INTEGER` | `DATE('2026-10-09') - date_collected` |
| `trend_search_score` | Search interest score for MassKara on this day | `INTEGER` | Max value from `cleaned_trends.csv` |
| `trend_velocity_7d` | 7-day week-over-week percentage change in search interest | `FLOAT` | `pct_change(periods=7)` |
| `trend_score_lag_1d` | Search interest score lagged by 1 day | `FLOAT` | `shift(1)` on `trend_search_score` |
| `trend_score_lag_2d` | Search interest score lagged by 2 days | `FLOAT` | `shift(2)` on `trend_search_score` |
| `trend_score_lag_3d` | Search interest score lagged by 3 days | `FLOAT` | `shift(3)` on `trend_search_score` |
| `flight_fest_min_price` | Lowest MNL-BCD opening-day flight fare quoted on this day | `FLOAT` | Min from `cleaned_flights` (`festival_target`) |
| `flight_fest_median_price` | Median MNL-BCD opening-day flight fare quoted on this day | `FLOAT` | Median from `cleaned_flights` (`festival_target`) |
| `flight_fest_mean_price` | Mean MNL-BCD opening-day flight fare quoted on this day | `FLOAT` | Mean from `cleaned_flights` (`festival_target`) |
| `flight_fest_quote_count` | Number of festival flight quotes recorded on this day | `INTEGER` | Count from `cleaned_flights` (`festival_target`) |
| `flight_rolling_min_price` | Lowest off-season baseline flight price quoted on this day | `FLOAT` | Min from `cleaned_flights` (`rolling`) |
| `flight_rolling_median_price` | Median off-season baseline flight price quoted on this day | `FLOAT` | Median from `cleaned_flights` (`rolling`) |
| `flight_rolling_mean_price` | Mean off-season baseline flight price quoted on this day | `FLOAT` | Mean from `cleaned_flights` (`rolling`) |
| `flight_rolling_quote_count` | Number of rolling flight quotes recorded on this day | `INTEGER` | Count from `cleaned_flights` (`rolling`) |
| `flight_price_premium` | Flight surge premium ratio vs rolling baseline | `FLOAT` | `flight_fest_median_price / flight_rolling_median_price` |
| `flight_median_change_1d` | Day-over-day shift in festival median flight price | `FLOAT` | `diff(1)` on `flight_fest_median_price` |
| `hotel_fest_min_price` | Lowest 4-night stay quote recorded on this day | `FLOAT` | Min from `cleaned_hotels` (`festival_target`) |
| `hotel_fest_median_price` | Median 4-night stay quote recorded on this day | `FLOAT` | Median from `cleaned_hotels` (`festival_target`) |
| `hotel_fest_mean_price` | Mean 4-night stay quote recorded on this day | `FLOAT` | Mean from `cleaned_hotels` (`festival_target`) |
| `hotel_fest_quote_count` | Number of festival hotel quotes recorded on this day | `INTEGER` | Count from `cleaned_hotels` (`festival_target`) |
| `hotel_rolling_min_price` | Lowest off-season baseline hotel rate quoted on this day | `FLOAT` | Min from `cleaned_hotels` (`rolling`) |
| `hotel_rolling_median_price` | Median off-season baseline hotel rate quoted on this day | `FLOAT` | Median from `cleaned_hotels` (`rolling`) |
| `hotel_rolling_mean_price` | Mean off-season baseline hotel rate quoted on this day | `FLOAT` | Mean from `cleaned_hotels` (`rolling`) |
| `hotel_rolling_quote_count` | Number of rolling hotel quotes recorded on this day | `INTEGER` | Count from `cleaned_hotels` (`rolling`) |
| `hotel_price_premium` | Hotel surge premium ratio vs rolling baseline | `FLOAT` | `hotel_fest_median_price / hotel_rolling_median_price` |
| `hotel_median_change_1d` | Day-over-day shift in festival median hotel price | `FLOAT` | `diff(1)` on `hotel_fest_median_price` |

### Relationships & Joins
- **Entity Tables to Analytical Summary:** Aggregated by `date_collected`.
- **Target vs. Baseline Comparison:** Join on `date_collected` comparing rows where `collection_mode = 'festival_target'` vs `collection_mode = 'rolling'`.

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