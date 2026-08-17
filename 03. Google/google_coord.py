import pandas as pd
import requests
import time

# Paste your API key here
API_KEY = "AIzaSyAMu_-BmiqTW6nXbjTyMmzeJOZPtzfsROs"

def get_coordinates(place):
    """
    Calls Google Maps Geocoding API with a place name.
    Returns (latitude, longitude) or (None, None) if not found.
    """
    # Extract just the city name before any comma
    # "Miraj,Kolhapur" → "Miraj"
    city = place.split(",")[0].strip()
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # Parameters sent to the API
    params = {
        "address": city + ", India",  # search query
        "key": API_KEY,               # your API key
        "region": "in",               # bias results toward India
        "language": "en"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] == "OK":
        # Drill into the nested JSON to get lat/lon
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print(f"  Failed: {place} → status: {data['status']}")
        return None, None

# Read existing file
df = pd.read_excel("Locations_With_Coords.xlsx")

print(f"Re-geocoding all {len(df)} rows with Google Maps...\n")

# Re-geocode everything from scratch — Google will be more accurate
for i, row in df.iterrows():
    src_lat, src_lon = get_coordinates(row["Source"])
    dst_lat, dst_lon = get_coordinates(row["Destination"])
    
    df.at[i, "src_lat"] = src_lat
    df.at[i, "src_lon"] = src_lon
    df.at[i, "dst_lat"] = dst_lat
    df.at[i, "dst_lon"] = dst_lon
    
    print(f"Row {i+1}: {row['Source']} → ({src_lat}, {src_lon}) | {row['Destination']} → ({dst_lat}, {dst_lon})")
    
    time.sleep(0.1)  # Google allows 50 requests/sec, 0.1s gap is safe

# Save to new clean file
df.to_excel("Locations_Google_Coords.xlsx", index=False)

# Check for failures
failed = df[df["src_lat"].isna() | df["dst_lat"].isna()]
print(f"\nDone! {len(failed)} rows still failed.")
if len(failed) > 0:
    print(failed[["Source", "Destination"]].to_string())
else:
    print("All rows geocoded successfully!")