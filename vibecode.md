Add festival-target ingestion, fix backup fallback recursion, fix primary
trends bug, bring primary sources back online with festival coverage,
collapse festival queries to cut API/token usage 4x

FEATURES
- Add backup_google_flights_festival() and backup_google_hotels_festival():
  re-query fixed Oct 9-12 dates every run (not just "tomorrow"), so
  travel_lead_time / hotel_lead_time / *_price_velocity can actually be
  computed. Each of the 4 festival dates is wrapped in its own try/except
  so one bad day doesn't kill the other three.
- Add primary_google_flights_festival() and primary_google_hotels_festival()
  now that SerpApi credits have reset. Mirrors the backup_*_festival()
  loop-over-dates pattern. Fallback on failure is COARSE: any exception
  mid-loop falls back to re-running the entire backup_google_*_festival()
  sweep, not just the date that failed.
- write_to_jsonl() now takes an explicit collection_mode param:
  "rolling" (existing day-ahead baseline queries) vs "festival_target"
  (fixed-date queries). Both still land in the SAME file per category
  (google_hotels.jsonl / google_flights.jsonl / google_trends.jsonl) per
  your call to keep one JSONL per category — collection_mode is the field
  Phase 3 should filter/group on before doing anything with the data.
  Festival rows also carry a target_date field.
- main() flipped back to primary-first now that credits are available.
  primary_google_hotels() / primary_google_flights() / primary_google_trends()
  / primary_google_flights_festival() / primary_google_hotels_festival()
  are the active calls; each already falls back to its backup_*
  counterpart internally on exception, so the backup_* calls in main()
  are commented out (NOT deleted) rather than removed — do not uncomment
  both primary and backup for the same category, that double-writes
  rolling/festival data every run. Flip back to backup-only if SerpApi
  credits run out again before Oct 11.

QUERY VOLUME REDUCTION (latest change)
- FESTIVAL_DATES (a 4-date list: Oct 9, 10, 11, 12) replaced with two
  single-value constants:
    FESTIVAL_FLIGHT_ARRIVAL = "2026-10-09"
    FESTIVAL_HOTEL_CHECKIN  = "2026-10-09"
    FESTIVAL_HOTEL_CHECKOUT = "2026-10-13"
- backup_google_flights_festival() / primary_google_flights_festival():
  collapsed from a 4-iteration loop (1 call per festival date) to a
  single call querying only FESTIVAL_FLIGHT_ARRIVAL.
- backup_google_hotels_festival() / primary_google_hotels_festival():
  collapsed from 4 one-night stay queries (Oct 9->10, 10->11, 11->12,
  12->13) to a single 4-night stay query (Oct 9->13).
- Net effect: festival-target calls per run dropped from 8 (4 flights +
  4 hotels) to 2 (1 flight + 1 hotel) — a 4x cut in that portion of
  Apify/SerpApi usage per run. Was necessary: Apify flight actor budget
  was already sitting around $4.15/$5 free tier after only a couple of
  runs at the old volume, nowhere near enough runway to reach Oct 11 on
  a daily cron.
- TRADE-OFF, explicit and deliberate, not a bug: you can no longer see
  which single day/night within the festival window drives a price
  surge hardest. Flights now only ever answer "what does the opening-day
  arrival cost." Hotels now answer "what does the whole 4-night stay
  cost" (one blended rate), not a per-night breakdown. If a per-day
  surge question comes up later (e.g. "did the Saturday of the festival
  spike harder than the Thursday lead-in"), this data can't answer it —
  would need to reintroduce a date list and go back to looping, at the
  cost of the credits saved here.

BUG FIXES
- backup_google_hotels() except block called primary_google_flights()
  (wrong function, wrong category — copy/paste leftover). Removed the
  cross-call entirely: this function IS the fallback, so calling into a
  primary here could ping-pong back into backup on primary's own except
  (which also falls back to backup), i.e. unbounded recursion the first
  time both primary and backup have a bad day. Same fix applied to
  backup_google_flights() (was calling primary_google_trends()).
- primary_google_trends(): `if "error" or "Error" in results:` was always
  truthy regardless of results content (operator precedence — evaluates
  to `"error" or (...)`, and "error" is a non-empty string). Every primary
  trends call was being logged as noResults even on success. Fixed to
  `if ("error" in results) or ("Error" in results):`.
- primary_google_trends(): `results.iterate_items()` doesn't exist on
  SerpApi's search() return (that's an Apify Client method, copy-pasted
  from the backup trends function). Replaced with dict access matching
  SerpApi's actual TIMESERIES shape (interest_over_time.timeline_data ->
  list of {timestamp, values: [{extracted_value}]}).
  VERIFIED against a live run: 93/93 rows landed as
  primary_source=true, status=success, with real nonzero interest
  values (up to 100) toward the end of the window. Parsing fix holds.
- backup_google_trends(): predefinedTimeframe was still "now 7-d" from an
  earlier draft. Reverted to "today 3-m" per final plan — run daily,
  APPEND (not overwrite), let dateTime_collected mark each day's full
  3-month batch. Do not merge rows across different dateTime_collected
  values into one series; each batch is independently normalized 0-100
  against its own window.
- All bare `except:` clauses replaced with `except Exception as e:`, and
  the exception string is now written into the failure record. Bare
  except was swallowing everything (including debugging signal) with no
  way to tell why a run failed once this moves to unattended cron on
  the VPS.

NEW FINDING (not fixed — flagging for Phase 3)
- Primary and backup trends do NOT share a timestamp format. Verified
  from live data: primary (SerpApi) writes Unix epoch strings, e.g.
  "timestamp": "1780185600". Backup (Apify) writes human-readable
  strings, e.g. "timestamp": "2026-08-27 20:24". Any Phase 3 code that
  reads google_trends.jsonl and treats "timestamp" as one consistent
  type will break silently on whichever source it wasn't tested against.
  Convert both to a common format (recommend epoch or ISO 8601) during
  cleaning — do not fix this in ingest.py, per the "keep ingestion dumb"
  principle below.

NOT DONE / TODO FOR MANUAL REFACTOR
- primary_google_hotels() error branch previously wrote to
  google_flights.jsonl (separate bug from before) — this was already
  fixed in the version you pasted this session, confirmed it's now
  writing to google_hotels.jsonl correctly, no action needed.
- No dedup/idempotency check if the cron job double-fires on the same
  day (e.g. VPS reboot mid-run) — every run appends, so a double-fire
  double-writes that day's rows. Not fixed here; consider a
  "have I already written today's dateTime_collected for this
  collection_mode?" guard before running the actor call, to save API
  credits if nothing else.
- primary_*_festival() fallback grain is coarse (see FEATURES note above)
  — whole-sweep fallback, not per-date. Less relevant now that each
  festival function is down to a single call anyway, but still worth
  knowing: a failure still falls back to the FULL backup sweep, there's
  no partial-success state to preserve since there's only one call.
- `requests` import is unused.
- Still worth eventually splitting write logic so schema differences
  between primary (SerpApi) and backup (Apify) payloads are reconciled
  in Phase 3, not Phase 2 — this refactor keeps ingestion dumb/raw on
  purpose (see the trends timestamp finding above for a live example of
  why). Don't add field-mapping/normalization logic to ingest.py later
  without moving it to the cleaning step instead.
- Stray leftover file: google_hotel.jsonl (singular) still exists from
  before the filename-consistency fix — dead data, not read by current
  code, safe to archive/delete whenever you're cleaning up the raw dir.
- If per-day/per-night festival granularity is ever needed again,
  reintroduce a FESTIVAL_DATES-style list and loop in the four
  backup/primary festival functions — the collapse to single-query
  constants above is what to revert.