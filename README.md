# MassKara Festival Social Media Buzz & MNL-BCD Travel Price Surge Tracker

## Problem Statement
I want to answer: "Is there a correlation between online buzz and MNL-BCD flight/BCD hotel price surges leading up to the Bacolod MassKara Festival in October?"

## Audience
This project is for budget-conscious travelers looking to be able to get ahead of the prices; business owners wanting to take advantage of a potential surge in tourism; and other researchers looking into a similar or related topic.

## KPIs or Key Metrics
The main metrics I want to track are categorized into four distinct layers:

#### 1. General Analytics
- `buzz_price_correlation`: The year's calculated statistical correlation coefficient ($R$) between online mention velocity and the median pricing of accommodations and flights.

#### 2. Buzz Metrics
- `hype_velocity`: The week-over-week percentage increase/decrease in social media mentions, post volume, and engagement metrics surrounding festival keywords.

#### 3. Flight Metrics
- `travel_lead_time`: The number of days remaining until the festival peak before Manila-to-Bacolod (MNL-BCD) plane ticket prices spike past a dynamic multiplier threshold (e.g., greater than 1.5x of the off-season baseline price).
- `travel_cooldown_time`: The number of days post-festival before MNL-BCD plane ticket prices drop back down below the baseline threshold.
- `travel_price_velocity`: The week-over-week percentage change in minimum and median MNL-BCD flight costs.

#### 4. Hotel Metrics
- `hotel_lead_time`: The number of days remaining until the festival peak before Bacolod City accommodation and hotel booking prices spike past a baseline threshold.
- `hotel_cooldown_time`: The number of days post-festival before BCD hotel booking prices stabilize below the surge threshold.
- `hotel_price_velocity`: The week-over-week percentage change in nightly hotel rates across listed Bacolod city accommodations.

## Likely Data Source
I will explore and integrate the following data endpoints:
*   **Flight Pricing:** Daily snapshots of Manila (MNL) to Bacolod (BCD) routes extracted via the **Amadeus Self-Service Flight Offers API** (or programmatic scraping of Google Flights using Playwright).
*   **Hotel Pricing:** Nightly rates for Bacolod City accommodations sourced using the **Agoda / Booking.com Scraper via Apify** (or a custom BeautifulSoup script targeting local pension houses).
*   **Social Hype/Buzz:** Text data, timestamps, and user engagement metrics extracted from **Reddit (`r/Bacolod`, `r/Philippines`) via the PRAW API** and keyword filtering on local public news RSS feeds (*Digicast Negros*).

## Possible Final Dashboard
The presentation layer will be built as a single-page **Streamlit app** divided into three clear analytical modules:

1. **The Executive Snapshot (Metric Cards)**
   - High-level metric callouts showing current median flight prices (MNL-BCD), current average hotel rates, total weekly social mention volumes, and the overall historical correlation score ($R$).

2. **The Surge Timeline (Interactive Line Chart)**
   - A dual-axis time-series chart mapping `hype_velocity` directly against `travel_price_velocity` and `hotel_price_velocity` across a rolling 90-day window to visually isolate the price lag following an online buzz spike.

3. **The Traveler's Action Center (Summary Data Table)**
   - A structured data table outputting the programmatic results for booking window strategies: `travel_lead_time`, `hotel_lead_time`, `travel_cooldown_time`, and `hotel_cooldown_time`.