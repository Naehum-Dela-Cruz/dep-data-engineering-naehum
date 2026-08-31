Add festival-target ingestion, fix backup fallback recursion, fix primary trends bug

FEATURES
- Add backup_google_flights_festival() and backup_google_hotels_festival():
  re-query fixed Oct 9-12 dates every run (not just "tomorrow"), so
  travel_lead_time / hotel_lead_time / *_price_velocity can actually be
  computed. Each of the 4 festival dates is wrapped in its own try/except
  so one bad day doesn't kill the other three.
- write_to_jsonl() now takes an explicit collection_mode param:
  "rolling" (existing day-ahead baseline queries) vs "festival_target"
  (new fixed-date queries). Both still land in the SAME file per category
  (google_hotels.jsonl / google_flights.jsonl / google_trends.jsonl) per
  your call to keep one JSONL per category — collection_mode is the field
  Phase 3 should filter/group on before doing anything with the data.
  Festival rows also carry a target_date field.
- Primary functions are NOT mirrored with festival versions yet — primary
  has no SerpApi credits to test against, low value to build blind. Add
  primary_*_festival() later mirroring the backup pattern once credits
  are confirmed working.

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
  list of {timestamp, values: [{extracted_value}]}). UNTESTED — no
  credits to verify against a live response, double-check field names
  once credits are restored.
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

NOT DONE / TODO FOR MANUAL REFACTOR
- primary_google_hotels() error branch previously wrote to
  google_flights.jsonl (separate bug from before) — this was already
  fixed in the version you pasted this session, confirmed it's now
  writing to google_hotels.jsonl correctly, no action needed.
- No dedup/idempotency check if the cron job double-fires on the same
  day (e.g. VPS reboot mid-run) — every run appends, so a double-fire
  double-writes that day's rows. Not fixed here; consider a
  "have I already written today's dateTime_collected for this
  collection_mode?" guard before running the actor call, to save Apify
  credits if nothing else.
- `requests` import is unused.
- No primary_*_festival() functions (see FEATURES note above).
- Still worth eventually splitting write logic so schema differences
  between primary (SerpApi) and backup (Apify) payloads are reconciled
  in Phase 3, not Phase 2 — this refactor keeps ingestion dumb/raw on
  purpose, don't add field-mapping logic here later without moving it
  to the cleaning step instead.