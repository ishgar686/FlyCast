# src/rideshare.py
"""
Rideshare estimates with address/miles inputs and time-of-day adjustment.

Order of operations:
- If GOOGLE_MAPS_API_KEY is set AND you provide an address, use Google Distance Matrix
  with departure_time (traffic-aware when available).
- Otherwise, if you provide miles, use a heuristic fare with time-of-day speed factors.
- As a last resort (address w/o key and no miles), we can't estimate.

We support SAN (San Diego Intl) directly. For other airports without a key,
please use the miles option.
"""

from __future__ import annotations
import os
import json
import math
import datetime as dt
from typing import Optional, Tuple

import requests

# --- Fare knobs (uberX-ish defaults; override via env) ---
FARE_BASE = float(os.getenv("FARE_BASE", "2.20"))
FARE_PER_MILE = float(os.getenv("FARE_PER_MILE", "1.25"))
FARE_PER_MIN  = float(os.getenv("FARE_PER_MIN",  "0.30"))
FARE_BOOKING  = float(os.getenv("FARE_BOOKING",  "2.55"))

# --- Heuristic driving speed (base) ---
AVG_SPEED_MPH = float(os.getenv("FALLBACK_SPEED_MPH", "28"))

# --- Optional Google daily cap (safety) ---
MAX_GOOGLE_CALLS_PER_DAY = int(os.getenv("RIDESHARE_MAX_GOOGLE_CALLS_PER_DAY", "100"))
COUNTER_FILE = os.getenv("RIDESHARE_GOOGLE_COUNTER_FILE", "/tmp/flycast_google_counter.json")

# SAN coordinates
SAN_LAT, SAN_LNG = 32.7336, -117.1897

# Airports we know. Extend if needed.
AIRPORTS = {
    "SAN": (SAN_LAT, SAN_LNG),
    "KSAN": (SAN_LAT, SAN_LNG),
}


# ---------- Public API ----------

def estimate_to_from_airport(
    airport_code: str,
    *,
    address: Optional[str] = None,
    miles_override: Optional[float] = None,
    when_hhmm: Optional[str] = None,
    direction: str = "to_airport",  # "to_airport" or "from_airport"
) -> Optional[Tuple[float, int]]:
    """
    Returns (estimated_cost_usd, estimated_duration_minutes) or None if we can't estimate.

    - airport_code: e.g., "SAN" (we support SAN/KSAN out of the box)
    - address: pickup/dropoff address string (use with Google key)
    - miles_override: float miles if you don't have a key (or prefer manual)
    - when_hhmm: "HH:MM" local time; affects traffic (Google) or our heuristic speed factor
    - direction: whether the trip is heading to or from the airport
    """
    airport_code = (airport_code or "").upper()
    airport_coords = AIRPORTS.get(airport_code)
    if not airport_coords:
        # Unknown airport unless we have miles override
        if miles_override is None:
            return None

    # Normalize time
    when_ts = _resolve_timestamp(when_hhmm)

    # Prefer Google if we have address + key + under cap
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key and address and _can_call_google_today():
        try:
            if direction == "to_airport":
                cost, mins = _estimate_via_google(
                    origin=address,
                    dest_coords=airport_coords,
                    departure_time=when_ts,
                    api_key=api_key,
                )
            else:
                cost, mins = _estimate_via_google(
                    origin_coords=airport_coords,
                    dest=address,
                    departure_time=when_ts,
                    api_key=api_key,
                )
            _bump_google_counter()
            return cost, mins
        except Exception:
            # Fall through to heuristic
            pass

    # Heuristic path using miles (either provided or we can't compute)
    if miles_override is None:
        # No miles and no Google => can't estimate
        return None

    speed_factor = _speed_factor_for_hour(_hour_from_ts(when_ts))
    adj_speed = max(8.0, AVG_SPEED_MPH * speed_factor)  # keep sane lower bound
    mins = (miles_override / adj_speed) * 60.0
    cost = FARE_BASE + miles_override * FARE_PER_MILE + mins * FARE_PER_MIN + FARE_BOOKING
    return round(cost, 2), int(round(mins))


# ---------- Google Distance Matrix ----------

def _estimate_via_google(
    *,
    origin: Optional[str] = None,
    dest: Optional[str] = None,
    origin_coords: Optional[Tuple[float, float]] = None,
    dest_coords: Optional[Tuple[float, float]] = None,
    departure_time: Optional[int] = None,
    api_key: str,
) -> Tuple[float, int]:
    """
    Call Distance Matrix with either address strings or lat/lng. Returns (cost, minutes).
    Uses duration_in_traffic when provided by API/plan, else falls back to duration.
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    o = origin if origin is not None else _fmt_coords(origin_coords)
    d = dest if dest is not None else _fmt_coords(dest_coords)

    params = {
        "origins": o,
        "destinations": d,
        "mode": "driving",
        "key": api_key,
    }
    if departure_time is not None:
        params["departure_time"] = str(departure_time)

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    obj = r.json()
    elem = obj["rows"][0]["elements"][0]
    if elem.get("status") != "OK":
        raise RuntimeError(f"DistanceMatrix status={elem.get('status')}")

    dist_m = elem["distance"]["value"]
    dur_s = (elem.get("duration_in_traffic") or elem.get("duration"))["value"]

    miles = dist_m / 1609.344
    mins = dur_s / 60.0
    cost = FARE_BASE + miles * FARE_PER_MILE + mins * FARE_PER_MIN + FARE_BOOKING
    return round(cost, 2), int(round(mins))


# ---------- Helpers ----------

def _fmt_coords(coords: Optional[Tuple[float, float]]) -> str:
    if not coords:
        raise ValueError("Missing coordinates")
    lat, lng = coords
    return f"{lat},{lng}"

def _resolve_timestamp(when_hhmm: Optional[str]) -> int:
    """Return a local epoch timestamp for today at HH:MM, or 'now' if None/invalid."""
    now = dt.datetime.now()
    if not when_hhmm:
        return int(now.timestamp())
    try:
        hh, mm = when_hhmm.strip().split(":")
        hh = int(hh); mm = int(mm)
        at = dt.datetime(now.year, now.month, now.day, hh, mm)
        return int(at.timestamp())
    except Exception:
        return int(now.timestamp())

def _hour_from_ts(ts: int) -> int:
    return dt.datetime.fromtimestamp(ts).hour

def _speed_factor_for_hour(hour: int) -> float:
    """
    Simple time-of-day speed multipliers for heuristic:
    - Late night (22–5): faster highways -> 1.15x speed
    - AM peak (7–9) & PM peak (16–19): slower -> 0.70x speed
    - Shoulder (6,10–15,20–21): slight slowdown -> 0.9x speed
    - Otherwise: 1.0
    """
    if hour in (22, 23, 0, 1, 2, 3, 4, 5):
        return 1.15
    if hour in (7, 8, 9, 16, 17, 18, 19):
        return 0.70
    if hour in (6, 10, 11, 12, 13, 14, 15, 20, 21):
        return 0.90
    return 1.0


# ----- lightweight daily counter (file-based) -----

def _today_str() -> str:
    return dt.date.today().isoformat()

def _load_counter() -> dict:
    try:
        with open(COUNTER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_counter(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)  # type: ignore
    except Exception:
        pass
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)

def _can_call_google_today() -> bool:
    if MAX_GOOGLE_CALLS_PER_DAY <= 0:
        return False
    data = _load_counter()
    if data.get("day") != _today_str():
        return True
    return int(data.get("count", 0)) < MAX_GOOGLE_CALLS_PER_DAY

def _bump_google_counter() -> None:
    data = _load_counter()
    if data.get("day") != _today_str():
        data = {"day": _today_str(), "count": 0}
    data["count"] = int(data.get("count", 0)) + 1
    _save_counter(data)