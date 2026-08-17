import pandas as pd

df = pd.read_excel("Locations_Google_Coords.xlsx")

# Find rows where Source or Destination contains "Miraj" or "Walwa"
mask = df["Source"].str.contains("Miraj", na=False) | df["Destination"].str.contains("Walwa", na=False)
print(df[mask][["Source", "Destination", "src_lat", "src_lon", "dst_lat", "dst_lon"]])