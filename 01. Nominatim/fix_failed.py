import pandas as pd
from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="route_fixer")

# Map messy names → clean searchable names
name_fixes = {
    # Sources
    "Taloja,Taloja Plant"           : "Taloja, Navi Mumbai",
    "Taloja Railhead,Taloja Railhead": "Taloja, Navi Mumbai",
    "Kolhapur,Kolhapur"             : "Kolhapur, Maharashtra",
    "Siddhpur,Ahemdabad"            : "Siddhapur, Gujarat",
    "Hingoli,Aurangabad"            : "Hingoli, Maharashtra",
    "Solapur,Solapur"               : "Solapur, Maharashtra",
    "Bardoli,Surat"                 : "Bardoli, Surat, Gujarat",
    "Davangere,Davangere"           : "Davangere, Karnataka",
    "Whitefield,Bengaluru"          : "Whitefield, Bangalore",
    "Bellary,Davangere"             : "Ballari, Karnataka",
    "Salem,Salem"                   : "Salem, Tamil Nadu",
    "Manmad,Nashik"                 : "Manmad, Nashik, Maharashtra",

    # Destinations
    "Bid,BEED"                      : "Beed, Maharashtra",
    "Pandharpur,SOLAPUR"            : "Pandharpur, Maharashtra",
    "Ratnagiri,RATNAGIRI"           : "Ratnagiri, Maharashtra",
    "Gangakhed,PARBHANI"            : "Gangakhed, Maharashtra",
    "Junnar,PUNE"                   : "Junnar, Pune, Maharashtra",
    "CHIKODI,Belgaum"               : "Chikodi, Belagavi, Karnataka",
    "Kaij,BEED"                     : "Kaij, Beed, Maharashtra",
    "Manjlegaon,BEED"               : "Manjlegaon, Beed, Maharashtra",
    "Palus,SANGLI"                  : "Palus, Sangli, Maharashtra",
    "Aundha (Nagnath),HINGOLI"      : "Aundha Nagnath, Hingoli, Maharashtra",
    "Pathardi,AHMEDNAGAR"           : "Pathardi, Ahmednagar, Maharashtra",
    "Kalamb,OSMANABAD"              : "Kalamb, Osmanabad, Maharashtra",
    "Bardoli,SURAT"                 : "Bardoli, Surat, Gujarat",
    "Karmala,SOLAPUR"               : "Karmala, Solapur, Maharashtra",
    "Palanpur,Banas Kantha"         : "Palanpur, Banaskantha, Gujarat",
    "Vijapur,MAHESANA"              : "Vijapur, Mehsana, Gujarat",
    "Ahmadabad City,Ahmadabad"      : "Ahmedabad, Gujarat",
    "Chaurai,CHHINDWARA"            : "Chhindwara, Madhya Pradesh",
    "DEVANAHALLI,BANGALORE RURAL"   : "Devanahalli, Karnataka",
    "Hadagalli,Vijayanagara"        : "Hadagalli, Vijayanagara, Karnataka",
    "BANGALORE NORTH,Bengaluru Urban": "Bangalore North, Karnataka",
    "GUDIBANDA,Chikballapur"        : "Gudibanda, Chikballapur, Karnataka",
    "SIDLAGHATTA,Chikballapur"      : "Sidlaghatta, Chikballapur, Karnataka",
    "CHINTAMANI,Chikballapur"       : "Chintamani, Chikballapur, Karnataka",
    "CHIK BALLAPUR,Chikballapur"    : "Chikballapur, Karnataka",
    "DOD BALLAPUR,BANGALORE RURAL"  : "Doddaballapur, Karnataka",
    "HONNALI,Davangere"             : "Honnali, Davangere, Karnataka",
    "MOLAKALMURU,CHITRADURGA"       : "Molakalmuru, Chitradurga, Karnataka",
    "CHIKNAYAKANHALLI,TUMKUR"       : "Chiknayakanhalli, Tumkur, Karnataka",
    "Khed,PUNE"                     : "Khed, Pune, Maharashtra",
    "TIRUMAKUDAL NARSIPUR,Mysore"   : "T Narasipura, Mysore, Karnataka",
    "GAURIBIDANUR,Chikballapur"     : "Gauribidanur, Chikballapur, Karnataka",
    "HASSAN,HASSAN"                 : "Hassan, Karnataka",
    "GUBBI,TUMKUR"                  : "Gubbi, Tumkur, Karnataka",
    "Bhokardan,JALNA"               : "Bhokardan, Jalna, Maharashtra",
    "RASIPURAM,NAMAKKAL"            : "Rasipuram, Namakkal, Tamil Nadu",
    "Baglan,NASHIK"                 : "Baglan, Nashik, Maharashtra",
    "Aurangabad,AURANGABAD"         : "Aurangabad, Maharashtra",
}

def clean(name):
    # If name is in our fix dictionary, use the clean version
    # Otherwise use as-is
    return name_fixes.get(name, name)

def get_coordinates(place):
    try:
        location = geolocator.geocode(clean(place) + ", India")
        time.sleep(1)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

# Read the existing file
df = pd.read_excel("Locations_With_Coords.xlsx")

# Find only the failed rows (where lat is missing)
failed_mask = df["src_lat"].isna() | df["dst_lat"].isna()
failed_indices = df[failed_mask].index

print(f"Re-geocoding {len(failed_indices)} failed rows...\n")

# Only re-geocode the failed rows — don't touch the ones that already worked
for i in failed_indices:
    src = df.at[i, "Source"]
    dst = df.at[i, "Destination"]

    # Only re-geocode if that specific coordinate is missing
    if pd.isna(df.at[i, "src_lat"]):
        df.at[i, "src_lat"], df.at[i, "src_lon"] = get_coordinates(src)
        print(f"Source fixed : {src}")

    if pd.isna(df.at[i, "dst_lat"]):
        df.at[i, "dst_lat"], df.at[i, "dst_lon"] = get_coordinates(dst)
        print(f"Dest fixed   : {dst}")

# Save back to the SAME file — overwrites with fixed data
df.to_excel("Locations_With_Coords.xlsx", index=False)

# Check if anything still failed
still_failed = df[df["src_lat"].isna() | df["dst_lat"].isna()]
print(f"\nDone. {len(still_failed)} rows still empty after fix.")
if len(still_failed) > 0:
    print(still_failed[["Source", "Destination"]].to_string())