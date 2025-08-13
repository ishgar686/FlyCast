# src/rideshare.py
"""
Simple rideshare estimator with no external keys required.
- Uses haversine distance + average driving speed to estimate minutes
- Uses tunable fare knobs to estimate cost (uberX-ish)
- Later, we can add Google Maps or Uber and keep this as a fallback
"""

from __future__ import annotations
import os, math
from typing import Tuple

# Fare knobs (override via env if you want)
FARE_BASE = float(os.getenv("FARE_BASE", "2.20"))
FARE_PER_MILE = float(os.getenv("FARE_PER_MILE", "1.25"))
FARE_PER_MIN  = float(os.getenv("FARE_PER_MIN",  "0.30"))
FARE_BOOKING  = float(os.getenv("FARE_BOOKING",  "2.55"))

# Defaults for SD driving
AVG_SPEED_MPH = float(os.getenv("FALLBACK_SPEED_MPH", "28"))

# Canonical coords (UCSD <> SAN)
UCSD_LAT, UCSD_LNG = 32.8801, -117.2340
SAN_LAT,  SAN_LNG  = 32.7336, -117.1897


def estimate_ucsd_san(is_departing_from_SAN: bool) -> Tuple[float, int]:
    """
    Estimate (cost_usd, duration_minutes) for UCSD <-> SAN.
    No external API keys needed.
    """
    origin = (UCSD_LAT, UCSD_LNG) if is_departing_from_SAN else (SAN_LAT, SAN_LNG)
    dest   = (SAN_LAT, SAN_LNG)   if is_departing_from_SAN else (UCSD_LAT, UCSD_LNG)
    return _estimate_generic(*origin, *dest)


def _estimate_generic(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, int]:
    miles = _haversine_miles(lat1, lon1, lat2, lon2)
    mins  = (miles / AVG_SPEED_MPH) * 60.0
    cost  = FARE_BASE + miles * FARE_PER_MILE + mins * FARE_PER_MIN + FARE_BOOKING
    return round(cost, 2), int(round(mins))


def _haversine_miles(lat1, lon1, lat2, lon2) -> float:
    R = 3958.7613  # miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c