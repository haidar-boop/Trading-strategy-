"""
Download free historical Binance USDT-M perpetual-futures data from
data.binance.vision (the public bulk-dump host; the fapi.* REST API is
geo-restricted and NOT used here).

Three feeds, exactly as the Coil-Break spec requires:
  * 1m klines            -> OHLCV, aggregated to daily bars at 00:00 UTC
  * fundingRate (8h)     -> funding charged bar-by-bar at realized sign
  * metrics (5m)         -> open interest (sum_open_interest); OI-filter variant only

Real on-disk schemas (verified against live dumps 2024-06):
  klines  : open_time[ms],open,high,low,close,volume,close_time,quote_volume,
            count,taker_buy_volume,taker_buy_quote_volume,ignore     (header present in recent files)
  funding : calc_time[ms],funding_interval_hours,last_funding_rate
  metrics : create_time[str 'YYYY-MM-DD HH:MM:SS'],symbol,sum_open_interest,
            sum_open_interest_value,count_toptrader_long_short_ratio,...

Coverage note (verified): klines/funding reach back to ~2020; metrics/OI only to ~2021.
The loader tolerates missing OI by disabling the OI filter for uncovered spans.
"""
from __future__ import annotations

import io
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.binance.vision/data/futures/um"
DEFAULT_RAW = Path(__file__).resolve().parents[2] / "artifacts" / "raw"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "coilbreak-phase2/1.0"})


def _get(url: str, timeout: int = 60, retries: int = 4) -> bytes | None:
    """GET with exponential backoff. Returns None on a genuine 404 (data absent)."""
    delay = 2.0
    for attempt in range(retries):
        try:
            r = _SESSION.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    return None


def _read_zip_csv(content: bytes) -> pd.DataFrame:
    """Extract the single CSV from a Binance dump zip. Detects header presence."""
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            head = fh.read(64)
    # Header detection: if the first byte-run before a comma is non-numeric, there's a header.
    first_cell = head.split(b",", 1)[0].strip()
    has_header = not _looks_numeric(first_cell)
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            return pd.read_csv(fh, header=0 if has_header else None)


def _looks_numeric(b: bytes) -> bool:
    try:
        float(b)
        return True
    except ValueError:
        return False


# ----- klines ---------------------------------------------------------------
_KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]


def _month_range(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def download_klines(symbol: str, start: date, end: date,
                    raw_dir: Path = DEFAULT_RAW) -> pd.DataFrame:
    """Monthly 1m klines for [start, end], concatenated. Caches per-month parquet."""
    out_dir = raw_dir / "klines" / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for y, m in _month_range(start, end):
        cache = out_dir / f"{symbol}-1m-{y:04d}-{m:02d}.parquet"
        if cache.exists():
            frames.append(pd.read_parquet(cache))
            continue
        url = f"{BASE}/monthly/klines/{symbol}/1m/{symbol}-1m-{y:04d}-{m:02d}.zip"
        content = _get(url)
        if content is None:
            continue  # month not yet published or before listing
        df = _read_zip_csv(content)
        df.columns = _KLINE_COLS[: df.shape[1]]
        df = df[["open_time", "open", "high", "low", "close", "volume", "quote_volume"]].copy()
        for c in ["open", "high", "low", "close", "volume", "quote_volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["open_time"] = pd.to_numeric(df["open_time"], errors="coerce").astype("int64")
        df = df.dropna(subset=["open", "high", "low", "close"])
        df.to_parquet(cache, index=False)
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["open_time", "open", "high", "low", "close", "volume", "quote_volume"])
    out = pd.concat(frames, ignore_index=True).drop_duplicates("open_time").sort_values("open_time")
    return out.reset_index(drop=True)


# ----- funding --------------------------------------------------------------
def download_funding(symbol: str, start: date, end: date,
                     raw_dir: Path = DEFAULT_RAW) -> pd.DataFrame:
    """Monthly 8h funding prints. Columns: calc_time[ms], funding_interval_hours, last_funding_rate."""
    out_dir = raw_dir / "funding" / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for y, m in _month_range(start, end):
        cache = out_dir / f"{symbol}-fundingRate-{y:04d}-{m:02d}.parquet"
        if cache.exists():
            frames.append(pd.read_parquet(cache))
            continue
        url = f"{BASE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{y:04d}-{m:02d}.zip"
        content = _get(url)
        if content is None:
            continue
        df = _read_zip_csv(content)
        df.columns = ["calc_time", "funding_interval_hours", "last_funding_rate"][: df.shape[1]]
        df["calc_time"] = pd.to_numeric(df["calc_time"], errors="coerce").astype("int64")
        df["last_funding_rate"] = pd.to_numeric(df["last_funding_rate"], errors="coerce")
        df["funding_interval_hours"] = pd.to_numeric(df.get("funding_interval_hours", 8), errors="coerce")
        df = df.dropna(subset=["calc_time", "last_funding_rate"])
        df.to_parquet(cache, index=False)
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["calc_time", "funding_interval_hours", "last_funding_rate"])
    out = pd.concat(frames, ignore_index=True).drop_duplicates("calc_time").sort_values("calc_time")
    return out.reset_index(drop=True)


# ----- metrics / open interest ---------------------------------------------
def _fetch_one_metric_day(symbol: str, d: date, out_dir: Path) -> None:
    """Fetch + cache a single day's metrics zip (used by the thread pool). Idempotent."""
    cache = out_dir / f"{symbol}-metrics-{d.isoformat()}.parquet"
    if cache.exists():
        return
    url = f"{BASE}/daily/metrics/{symbol}/{symbol}-metrics-{d.isoformat()}.zip"
    content = _get(url)
    if content is None:
        pd.DataFrame(columns=["create_time_ms", "sum_open_interest"]).to_parquet(cache, index=False)
        return
    df = _read_zip_csv(content)
    # create_time is 'YYYY-MM-DD HH:MM:SS' (UTC); convert to ms epoch robustly
    # (pandas 3.0 tz-aware .astype('int64') is unreliable — use a Timedelta division).
    ct = pd.to_datetime(df["create_time"], utc=True, errors="coerce")
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    ms = (ct - epoch) // pd.Timedelta(milliseconds=1)
    out = pd.DataFrame({
        "create_time_ms": ms,
        "sum_open_interest": pd.to_numeric(df["sum_open_interest"], errors="coerce"),
    }).dropna()
    out["create_time_ms"] = out["create_time_ms"].astype("int64")
    out.to_parquet(cache, index=False)


def download_metrics(symbol: str, start: date, end: date,
                     raw_dir: Path = DEFAULT_RAW, workers: int = 16) -> pd.DataFrame:
    """Daily 5m metrics dumps (open interest). create_time is a STRING datetime, not ms.

    Daily-partitioned (~730 files/2yr), so uncached days are fetched with a thread pool.
    Only published from ~2021; missing days are cached as empty sentinels and the loader
    disables the OI filter for uncovered spans.
    """
    out_dir = raw_dir / "metrics" / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    all_days = []
    d = start
    while d <= end:
        all_days.append(d)
        d += timedelta(days=1)
    todo = [dd for dd in all_days if not (out_dir / f"{symbol}-metrics-{dd.isoformat()}.parquet").exists()]
    if todo:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(lambda dd: _fetch_one_metric_day(symbol, dd, out_dir), todo))

    frames = []
    for dd in all_days:
        cache = out_dir / f"{symbol}-metrics-{dd.isoformat()}.parquet"
        try:
            cached = pd.read_parquet(cache)
        except Exception:
            continue
        if len(cached):
            frames.append(cached)
    if not frames:
        return pd.DataFrame(columns=["create_time_ms", "sum_open_interest"])
    res = pd.concat(frames, ignore_index=True).drop_duplicates("create_time_ms").sort_values("create_time_ms")
    return res.reset_index(drop=True)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Download Binance USDT-M data from data.binance.vision")
    p.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    p.add_argument("--start", default="2021-01-01")
    p.add_argument("--end", default="2024-12-31")
    args = p.parse_args()
    s = date.fromisoformat(args.start)
    e = date.fromisoformat(args.end)
    for sym in args.symbols:
        k = download_klines(sym, s, e)
        f = download_funding(sym, s, e)
        m = download_metrics(sym, s, e)
        print(f"{sym}: klines={len(k):,} funding={len(f):,} oi={len(m):,}")
