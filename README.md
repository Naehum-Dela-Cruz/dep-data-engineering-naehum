# MassKara Festival Sentiment & Travel Surge Tracker

## Problem Statement
I want to answer: "Is there a correlation between online buzz and MNL-BCD flight/BCD hotel price surges leading up to the Bacolod MassKara Festival in October?"

## Audience
This project is for budget-conscious travelers looking to be able to get ahead of the prices; business owners wanting to take advantage of a potential surge in tourism; and other researchers looking into a similar or related topic.

## KPIs or Key Metrics
The main metrics I want to track are:
- `buzz_price_correlation` the year's correlation between buzz and price of hotels and flights.
- `travel_lead_time` the year's number of days remaining towards the festival before MNL-BCD plane ticket prices went past a yet-undetermined threshold.
- `hotel_lead_time` the year's number of days remainng towards the festival before BCD hotel prices went past a yet-undetermined threshold.
- `travel_cooldown_time` the year's number of days on or after the festival before MNL-BCD plane ticket prices went below a yet-undetermined threshold.
- `hotel_cooldown_time` the year's number of days on or after the festival before BCD hotel prices went below a yet-undetermined threshold.
- `hype_velocity` the week-over-week percentage increase/decrease in social media buzz over the festival.
- `travel_price_velocity` the week-over-week percentage increase/decrease in MNL-BCD prices.
- `hotel_price_velocity` the week-over-week percentage increase/decrease in BCD Hotel prices.


## Likely Data Source
I will explore the following sources:
*   **Flight Pricing:** Daily snapshots of Manila (MNL) to Bacolod (BCD) routes extracted via the **Amadeus Self-Service Flight Offers API** (or programmatic scraping of Google Flights using Playwright).
*   **Hotel Pricing:** Nightly rates for Bacolod City accommodations sourced using the **Agoda / Booking.com Scraper via Apify** (or a custom BeautifulSoup script targeting local pension houses).
*   **Social Hype/Buzz:** Text, timestamps, and engagement metrics extracted from **Reddit (`r/Bacolod`, `r/Philippines`) via the PRAW API** and keyword filtering on local public news RSS feeds (*Digicast Negros*).

## Possible Final Dashboard
The dashboard should help the audience quickly see `buzz_trend`, `price_trend`, `flight_med_price`, `hotel_med_price`, and `buzz_price_correlation`.