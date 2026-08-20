import pandas as pd
from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="route_app")

def get_coordinates(place):
    try:
        location = geolocator.geocode(place + ", India")
        time.sleep(1)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except:
        return None, None

df = pd.read_excel("Locations_File.xlsx")

print(f"Found {len(df)} rows. Starting geocoding... this will take ~{len(df)*2} seconds")

df["src_lat"], df["src_lon"] = zip(*df["Source"].apply(get_coordinates))
df["dst_lat"], df["dst_lon"] = zip(*df["Destination"].apply(get_coordinates))

df.to_excel("Locations_With_Coords.xlsx", index=False)

print("Done! Saved to Locations_With_Coords.xlsx")
    