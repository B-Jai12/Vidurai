"""
routers/nearby.py — Nearby hospitals, pharmacies, and specialists via OpenStreetMap Overpass API.
"""
from fastapi import APIRouter, HTTPException, Query
from agents.pharmacy_agent import (
    get_nearby_hospitals,
    get_nearby_pharmacies,
    get_specialist_hospitals,
    get_user_location_from_ip,
)

router = APIRouter(prefix="/nearby", tags=["Nearby Places"])


@router.get("/location")
def detect_location():
    """
    Detect approximate user location from their IP address.
    Returns lat, lng, and city name.
    """
    result = get_user_location_from_ip()
    if not result:
        raise HTTPException(status_code=503, detail="Could not determine location from IP")
    lat, lng, city = result
    return {"lat": lat, "lng": lng, "city": city}


@router.get("/hospitals")
def nearby_hospitals(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Find nearby hospitals and clinics (OpenStreetMap, no API key required)."""
    results = get_nearby_hospitals(lat, lng)
    return {"results": results, "count": len(results)}


@router.get("/pharmacies")
def nearby_pharmacies(
    lat: float = Query(...),
    lng: float = Query(...),
):
    """Find nearby pharmacies and chemists."""
    results = get_nearby_pharmacies(lat, lng)
    return {"results": results, "count": len(results)}


@router.get("/specialists")
def nearby_specialists(
    lat: float = Query(...),
    lng: float = Query(...),
    specialty: str = Query(default="cardiology", description="Medical specialty keyword"),
):
    """Find nearby specialist hospitals by specialty type."""
    results = get_specialist_hospitals(lat, lng, specialty)
    return {"results": results, "count": len(results), "specialty": specialty}
