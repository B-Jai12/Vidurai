import requests
import os
from dotenv import load_dotenv

load_dotenv()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "VidurApp/1.0"}


def query_overpass(lat, lng, amenity, keyword="", radius=5000):
    """Query OpenStreetMap Overpass API. Free, no key needed."""
    try:
        if keyword:
            query = f"""
[out:json][timeout:20];
(
  node["amenity"="{amenity}"]["name"](around:{radius},{lat},{lng});
  way["amenity"="{amenity}"]["name"](around:{radius},{lat},{lng});
  node["amenity"="{amenity}"]["name"~"{keyword}",i](around:{radius},{lat},{lng});
  way["amenity"="{amenity}"]["name"~"{keyword}",i](around:{radius},{lat},{lng});
);
out center tags 15;
"""
        else:
            query = f"""
[out:json][timeout:20];
(
  node["amenity"="{amenity}"]["name"](around:{radius},{lat},{lng});
  way["amenity"="{amenity}"]["name"](around:{radius},{lat},{lng});
);
out center tags 15;
"""
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=25
        )
        data = response.json()
        elements = data.get("elements", [])

        results = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name:
                continue

            # Coordinates
            if el.get("type") == "node":
                elat = el.get("lat", lat)
                elng = el.get("lon", lng)
            else:
                center = el.get("center", {})
                elat = center.get("lat", lat)
                elng = center.get("lon", lng)

            # Build address
            addr_parts = []
            for key in ["addr:housenumber", "addr:street", "addr:suburb", "addr:city"]:
                val = tags.get(key, "")
                if val:
                    addr_parts.append(val)
            address = ", ".join(addr_parts) if addr_parts else tags.get("addr:full", "Nearby")

            results.append({
                "name": name,
                "address": address,
                "phone": tags.get("phone", tags.get("contact:phone", "")),
                "rating": "N/A",
                "open_now": None,
                "lat": elat,
                "lng": elng,
            })

        # Deduplicate by name
        seen = set()
        unique = []
        for r in results:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique.append(r)

        return unique[:10]

    except Exception as e:
        print(f"Overpass error: {e}")
        return []


def get_nearby_hospitals(lat, lng):
    results = query_overpass(lat, lng, "hospital", radius=7000)
    if not results:
        # Broader fallback
        results = query_overpass(lat, lng, "clinic", radius=5000)
    return results


def get_nearby_pharmacies(lat, lng):
    results = query_overpass(lat, lng, "pharmacy", radius=4000)
    if not results:
        results = query_overpass(lat, lng, "chemist", radius=4000)
    return results


def get_specialist_hospitals(lat, lng, specialty):
    return query_overpass(lat, lng, "hospital", keyword=specialty, radius=10000)


def get_ayushman_hospitals(lat, lng):
    return query_overpass(lat, lng, "hospital", keyword="Ayushman", radius=15000)


def find_generic_pharmacies(lat, lng):
    results = query_overpass(lat, lng, "pharmacy", keyword="aushadhi|generic", radius=10000)
    for r in results:
        r["type"] = "Generic / Jan Aushadhi"
    return results


def get_user_location_from_ip():
    """Get approximate location from IP."""
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5, headers=HEADERS)
        data = r.json()
        lat = data.get("latitude")
        lng = data.get("longitude")
        city = data.get("city", "Hyderabad")
        if lat and lng:
            return lat, lng, city
    except Exception as e:
        print(f"IP location error: {e}")
    return 17.3850, 78.4867, "Hyderabad"