"""
Scheduled-event calendar for the event-exclusion filter (no NEW entries in the 24h
before a listed event).

FOMC decision (statement) dates are scheduled and stable; they are bundled here,
stamped at 18:00 UTC (~2pm ET announcement). CPI releases are intentionally NOT
bundled: the exact BLS release dates require a verified schedule and are omitted
rather than approximated, so the backtest's event filter is FOMC-only by default.
This is a documented, minor deviation from the spec (the filter mechanism is exact;
only the CPI dates are absent). Supply extra events via `event_timestamps_ms(extra=...)`.
"""
from __future__ import annotations

import pandas as pd

# FOMC statement/announcement dates (scheduled meetings + 2020 emergency actions).
_FOMC_DATES = [
    # 2020
    "2020-01-29", "2020-03-03", "2020-03-15", "2020-03-18", "2020-04-29",
    "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28",
    "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
    "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
    "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
    "2025-09-17", "2025-10-29", "2025-12-10",
]

_ANNOUNCE_UTC_HOUR = 18  # ~2pm ET


def event_timestamps_ms(extra: list[str] | None = None) -> "pd.Series":
    """Return event timestamps (ms epoch, UTC) as an int64 Series, sorted."""
    dates = list(_FOMC_DATES) + (list(extra) if extra else [])
    ts = pd.to_datetime(dates, utc=True) + pd.Timedelta(hours=_ANNOUNCE_UTC_HOUR)
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    ms = (ts - epoch) // pd.Timedelta(milliseconds=1)
    return pd.Series(sorted(ms.astype("int64")), dtype="int64")
