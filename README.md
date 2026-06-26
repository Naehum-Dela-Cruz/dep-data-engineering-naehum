# MassKara Festival Google Trends Interest & MNL-BCD Travel Price Surge Tracker

## Problem Statement
This builder wants to answer: "Is there a correlation between an uptick in Google Trends' Interest Over Time metric and MNL-BCD flight/BCD hotel price surges leading up to the Bacolod MassKara Festival in October?"

## Audience
This project is for budget-conscious travelers looking to be able to get ahead of the prices; business owners wanting to make informed data-driven descisions in the face of a potential surge in tourism; and other researchers looking into a similar or related topic.

## KPIs or Key Metrics
The main metrics this builder wishes to track are categorized into four distinct layers:

#### 1. General Analytics
- `trends_price_correlation`: The calculated statistical correlation coefficient between trends velocity and the median pricing of accommodations and flights.

#### 2. Trends Metrics
- `trends_velocity`: The week-over-week percentage increase/decrease in Google Trend's Interest Over Time value for relevant keywords.

#### 3. Flight Metrics
- `travel_lead_time`: The number of days remaining until the festival peak before Manila-to-Bacolod (MNL-BCD) plane ticket prices spike past a dynamic multiplier threshold (e.g., greater than 1.5x of the off-season baseline price).
- `travel_cooldown_time`: The number of days post-festival before MNL-BCD plane ticket prices drop back down below the baseline threshold.
- `travel_price_velocity`: The week-over-week percentage change in minimum and median MNL-BCD flight costs.

#### 4. Hotel Metrics
- `hotel_lead_time`: The number of days remaining until the festival peak before Bacolod City accommodation and hotel booking prices spike past a baseline threshold.
- `hotel_cooldown_time`: The number of days post-festival before BCD hotel booking prices stabilize below the surge threshold.
- `hotel_price_velocity`: The week-over-week percentage change in nightly hotel rates across listed Bacolod city accommodations.

## Likely Data Source
This builder will explore and integrate the following data endpoints:
*   **Google Flights Pricing:** Timestamps, and price metrics extracted via **https://serpapi.com** free-tier.
*   **Google Hotels Pricing:** Timestamps, and price metrics extracted via **https://serpapi.com** free-tier.
*   **Google Trends Interest Over Time:** Timestamps, and interest metrics extracted via **https://serpapi.com** free-tier.

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

- This builder would've liked to do an analysis of the previous MassKara festival to contrast with the upcoming one, but SerpApi's Google Hotels and Google Flights scraper cannot view historical prices. 

- This builder doesn't like being completely at the mercy of SerpApi. Alternative sources would be appreciated for redundancy.