import pandas as pd
import requests
import json
import polyline as pl
import time

API_KEY = "AIzaSyAMu_-BmiqTW6nXbjTyMmzeJOZPtzfsROs"

def get_road_geometry(lat1, lon1, lat2, lon2):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin"      : f"{lat1},{lon1}",
        "destination" : f"{lat2},{lon2}",
        "mode"        : "driving",
        "key"         : API_KEY
    }
    data = requests.get(url, params=params).json()
    if data["status"] == "OK":
        encoded = data["routes"][0]["overview_polyline"]["points"]
        # decode returns (lat, lon) — GeoJSON needs [lon, lat]
        return [[p[1], p[0]] for p in pl.decode(encoded)]
    return None

# --- Read your file ---
df = pd.read_excel("Locations_Google_Coords.xlsx")

# --- GeoJSON structure ---
# GeoJSON is a dict with a list of "features"
# Each feature = one route (one source-destination pair)
geojson = {
    "type": "FeatureCollection",
    "features": []
}

print(f"Fetching road geometry for {len(df)} pairs...\n")

for i, row in df.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()
    lat1, lon1 = row["src_lat"], row["src_lon"]
    lat2, lon2 = row["dst_lat"], row["dst_lon"]

    coords = get_road_geometry(lat1, lon1, lat2, lon2)

    if coords:
        # Each route becomes one GeoJSON feature
        feature = {
            "type": "Feature",
            "properties": {
                "source"     : src,
                "destination": dst,
                "src_lat"    : lat1,
                "src_lon"    : lon1,
                "dst_lat"    : lat2,
                "dst_lon"    : lon2
            },
            "geometry": {
                "type"       : "LineString",
                "coordinates": coords   # list of [lon, lat] points along the road
            }
        }
        geojson["features"].append(feature)
        print(f"Row {i+1}: {src} → {dst} ✅ ({len(coords)} path points)")
    else:
        print(f"Row {i+1}: {src} → {dst} ❌ failed")

    time.sleep(0.1)

# --- Save GeoJSON file ---
with open("routes.geojson", "w") as f:
    json.dump(geojson, f, indent=2)

print(f"\nDone! Saved to routes.geojson")
print(f"Total routes: {len(geojson['features'])}")