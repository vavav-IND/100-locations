import pandas as pd

# Manually looked up coordinates from Google Maps
# Format: "Source" or "Destination" column value : (latitude, longitude)
manual_coords = {
    "Taloja,Taloja Plant"            : (19.0728, 73.0660),
    "Taloja Railhead,Taloja Railhead": (19.0728, 73.0660),
    "Siddhpur,Ahemdabad"             : (23.9162, 72.3736),
    "Davangere,Davangere"            : (14.4644, 75.9218),
    "Bellary,Davangere"              : (15.1394, 76.9214),
    "Whitefield,Bengaluru"           : (12.9698, 77.7500),

    "Bid,BEED"                       : (18.9890, 75.7601),
    "Pandharpur,SOLAPUR"             : (17.6805, 75.3296),
    "Gangakhed,PARBHANI"             : (18.9524, 76.7493),
    "Junnar,PUNE"                    : (19.2079, 73.8813),
    "CHIKODI,Belgaum"                : (16.4309, 74.5958),
    "Kaij,BEED"                      : (18.8456, 76.0132),
    "Manjlegaon,BEED"                : (19.1543, 76.6537),
    "Pathardi,AHMEDNAGAR"            : (19.1765, 74.7014),
    "Karmala,SOLAPUR"                : (18.0618, 75.2010),
    "Palanpur,Banas Kantha"          : (24.1722, 72.4377),
    "Vijapur,MAHESANA"               : (23.5617, 72.7538),
    "Ahmadabad City,Ahmadabad"       : (23.0225, 72.5714),
    "Chaurai,CHHINDWARA"             : (22.0603, 78.9289),
    "Hadagalli,Vijayanagara"         : (15.0188, 75.9246),
    "GUDIBANDA,Chikballapur"         : (13.8121, 77.8573),
    "SIDLAGHATTA,Chikballapur"       : (13.3869, 77.8623),
    "CHINTAMANI,Chikballapur"        : (13.4005, 78.0530),
    "HONNALI,Davangere"              : (14.2411, 75.6479),
    "CHIKNAYAKANHALLI,TUMKUR"        : (13.4180, 76.6198),
    "Khed,PUNE"                      : (18.8503, 73.9252),
    "Kalamb,OSMANABAD"               : (18.0437, 76.0538),
    "GAURIBIDANUR,Chikballapur"      : (13.6130, 77.5173),
    "GUBBI,TUMKUR"                   : (13.3116, 76.9398),
    "Bhokardan,JALNA"                : (19.8612, 75.7657),
    "Aurangabad,AURANGABAD"          : (19.8762, 75.3433),
}

# Read existing file
df = pd.read_excel("Locations_With_Coords.xlsx")

# Patch coordinates from manual lookup
for i, row in df.iterrows():
    if pd.isna(row["src_lat"]) and row["Source"] in manual_coords:
        df.at[i, "src_lat"], df.at[i, "src_lon"] = manual_coords[row["Source"]]

    if pd.isna(row["dst_lat"]) and row["Destination"] in manual_coords:
        df.at[i, "dst_lat"], df.at[i, "dst_lon"] = manual_coords[row["Destination"]]

# Save
df.to_excel("Locations_With_Coords.xlsx", index=False)

# Check remaining
still_failed = df[df["src_lat"].isna() | df["dst_lat"].isna()]
print(f"Done. {len(still_failed)} rows still empty.")
if len(still_failed) > 0:
    print(still_failed[["Source", "Destination"]].to_string())
else:
    print("All rows have coordinates!")