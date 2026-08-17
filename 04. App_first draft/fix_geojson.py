import json
import requests
import time

API_KEY = "AIzaSyAMu_-BmiqTW6nXbjTyMmzeJOZPtzfsROs"

def get_osrm_duration(coords_lonlat):
    """Get duration from OSRM using first and last coordinate of the route"""
    start = coords_lonlat[0]   # [lon, lat]
    end   = coords_lonlat[-1]  # [lon, lat]
    url = f"http://router.project-osrm.org/route/v1/driving/{start[0]},{start[1]};{end[0]},{end[1]}?overview=false"
    try:
        data = requests.get(url, timeout=10).json()
        if data["code"] == "Ok":
            return round(data["routes"][0]["duration"] / 60, 1)  # seconds → minutes
    except:
        pass
    return None

def get_google_distance_duration(coords_lonlat):
    """Get distance + duration from Google using first and last coordinate"""
    start = coords_lonlat[0]   # [lon, lat]
    end   = coords_lonlat[-1]
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins"     : f"{start[1]},{start[0]}",   # lat,lon
        "destinations": f"{end[1]},{end[0]}",
        "mode"        : "driving",
        "key"         : API_KEY
    }
    try:
        data = requests.get(url, params=params).json()
        if data["status"] == "OK":
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                distance_km  = round(element["distance"]["value"] / 1000, 2)
                duration_min = round(element["duration"]["value"] / 60, 1)
                return distance_km, duration_min
    except:
        pass
    return None, None

# --- Fix routes.geojson (Google) ---
print("Fixing routes.geojson...")
with open("routes.geojson") as f:
    google_data = json.load(f)

for i, feature in enumerate(google_data["features"]):
    coords = feature["geometry"]["coordinates"]  # [lon, lat]
    dist, dur = get_google_distance_duration(coords)
    feature["properties"]["distance_km"]  = dist
    feature["properties"]["duration_min"] = dur
    print(f"  {i+1}: {feature['properties']['source']} → {feature['properties']['destination']} | {dist} km | {dur} mins")
    time.sleep(0.1)

with open("routes.geojson", "w") as f:
    json.dump(google_data, f, indent=2)
print("routes.geojson fixed!\n")

#--- Fix routes_nx.geojson (OSRM + NetworkX)
print("Fixing routes_nx.geojson...")
with open("routes_nx.geojson") as f:
    osrm_data = json.load(f)

for i, feature in enumerate(osrm_data["features"]):
    coords = feature["geometry"]["coordinates"]  # [lon, lat]
    dur = get_osrm_duration(coords)
    feature["properties"]["duration_min"] = dur
    print(f"  {i+1}: {feature['properties']['source']} → {feature['properties']['destination']} | {feature['properties']['road_distance_km']} km | {dur} mins")
    time.sleep(0.3)

with open("routes_nx.geojson", "w") as f:
    json.dump(osrm_data, f, indent=2)
print("routes_nx.geojson fixed!")

