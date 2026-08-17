import pandas as pd
import math
import requests
import time

# --- Haversine formula ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

# --- OSRM road route ---
def get_road_route(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        data = requests.get(url, timeout=10).json()
        if data["code"] == "Ok":
            distance_km = round(data["routes"][0]["distance"] / 1000, 2)
            duration_min = round(data["routes"][0]["duration"] / 60, 1)
            return distance_km, duration_min
        return None, None
    except:
        return None, None

# --- Read file ---
df = pd.read_excel("Locations_Google_Coords.xlsx")

# --- New columns to fill ---
df["straight_line_km"] = None
df["road_distance_km"] = None
df["road_duration_min"] = None
df["road_duration_hrs"] = None

print(f"Processing {len(df)} rows...\n")

for i, row in df.iterrows():
    lat1, lon1 = row["src_lat"], row["src_lon"]
    lat2, lon2 = row["dst_lat"], row["dst_lon"]

    # Calculate straight line
    straight = haversine(lat1, lon1, lat2, lon2)
    df.at[i, "straight_line_km"] = straight

    # Get road route
    road_dist, road_dur = get_road_route(lat1, lon1, lat2, lon2)
    df.at[i, "road_distance_km"] = road_dist
    df.at[i, "road_duration_min"] = road_dur
    df.at[i, "road_duration_hrs"] = round(road_dur / 60, 1) if road_dur else None

    print(f"Row {i+1}: {row['Source']} → {row['Destination']} | Straight: {straight} km | Road: {road_dist} km | Time: {road_dur} mins")

    time.sleep(0.5)  # Be polite to OSRM server

# --- Save output ---
df.to_excel("Final_Routes.xlsx", index=False)
print("\nDone! Saved to Final_Routes.xlsx")