import pandas as pd

# Read the already-generated file (with empty rows)
df = pd.read_excel("Locations_With_Coords.xlsx")

# Filter rows where any coordinate is missing
failed = df[df["src_lat"].isna() | df["dst_lat"].isna()]

print(f"{len(failed)} rows failed geocoding:\n")
print(failed[["Source", "Destination"]].to_string())