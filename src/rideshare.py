"""
Lightweight scaffold for rideshare (Uber) estimates.

Nothing is wired into the CLI yet—this is just a safe placeholder so we can
hook up the real API calls tomorrow without touching other files today.
"""

from typing import Optional, Tuple
import os

# Rough coords we may use later (UCSD <-> SAN)
UCSD_LAT, UCSD_LNG = 32.8801, -117.2340
SAN_LAT, SAN_LNG = 32.7336, -117.1897


def estimate_via_uber(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> Optional[Tuple[float, int]]:
    """
    Placeholder for Uber Guest Trip Estimates.

    Expected return (when implemented):
        (estimated_cost_usd, estimated_duration_minutes)

    For now, returns None unless an Uber token is present (still None until implemented).
    """
    _token = os.getenv("UBER_BEARER_TOKEN")
    if not _token:
        return None

    # TODO(ishaan): Implement POST https://api.uber.com/v1/guest/trips/estimates
    # using the bearer token with guests.trips scope.
    # Parse fare/ETA and return (cost_usd, duration_minutes).
    return None


def estimate_ucsd_san(is_departing_from_SAN: bool) -> Optional[Tuple[float, int]]:
    """
    Convenience wrapper for UCSD <-> SAN trip.

    When implemented, this will call `estimate_via_uber` (and potentially a
    non-Uber fallback) and return a (cost, minutes) tuple. For now: None.
    """
    origin = (UCSD_LAT, UCSD_LNG) if is_departing_from_SAN else (SAN_LAT, SAN_LNG)
    dest = (SAN_LAT, SAN_LNG) if is_departing_from_SAN else (UCSD_LAT, UCSD_LNG)

    # Future:
    #   result = estimate_via_uber(*origin, *dest) or estimate_via_maps(*origin, *dest)
    #   return result
    return None