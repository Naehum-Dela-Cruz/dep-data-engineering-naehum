Add festival-target ingestion, fix backup fallback recursion, fix primary
trends bug, bring primary sources back online with festival coverage

FEATURES
- Add backup_google_flights_festival() and backup_google_hotels_festival():
  re-query fixed Oct 9-12 dates every run (not just "tomorrow"), so
  travel_lead_time / hotel_lead_time / *_price_velocity can actually be
  computed. Each of the 4 festival dates is wrapped in its own try/except
  so one bad day doesn't kill the other three.
- Add primary_google_flights_festival() and primary_google_hotels_festival()
  now that SerpApi credits have reset. Mirrors the backup_*_festival()
  loop-over-FESTIVAL_DATES pattern. Fallback on failure is COARSE: any
  exception mid-loop falls back to re-running the entire
  backup_google_*_festival() sweep, not just the date that failed — a
  failure on date 3 of 4 wastes the primary credits already spent on
  dates 1-2 and re-queries all 4 dates via backup. Acceptable for
  vibecode phase given call volume; tighten to per-date fallback on
  manual refactor.
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
  — whole-sweep fallback, not per-date. Fine for now, revisit later.
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