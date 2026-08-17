import pandas as pd
import networkx as nx
import math
import requests
import time

# --- Haversine (straight line distance) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

# --- OSRM road distance ---
def get_road_distance(lat1, lon1, lat2, lon2):
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

# --- Read your coordinates file ---
df = pd.read_excel("Locations_Google_Coords.xlsx")

# --- Build the NetworkX graph ---
# DiGraph = directed graph (A→B is different from B→A)
# We use directed because road distances can differ by direction
G = nx.DiGraph()

print(f"Building graph from {len(df)} rows...\n")

for i, row in df.iterrows():
    src = row["Source"].split(",")[0].strip()   # "Miraj,Kolhapur" → "Miraj"
    dst = row["Destination"].split(",")[0].strip()

    src_lat, src_lon = row["src_lat"], row["src_lon"]
    dst_lat, dst_lon = row["dst_lat"], row["dst_lon"]

    # Skip rows with missing coordinates
    if pd.isna(src_lat) or pd.isna(dst_lat):
        print(f"  Skipping row {i+1} — missing coordinates")
        continue

    # Add nodes with coordinate attributes
    # This stores lat/lon on each node for later use
    G.add_node(src, lat=src_lat, lon=src_lon)
    G.add_node(dst, lat=dst_lat, lon=dst_lon)

    # Get road distance for this pair
    road_dist, road_dur = get_road_distance(src_lat, src_lon, dst_lat, dst_lon)
    straight_dist = haversine(src_lat, src_lon, dst_lat, dst_lon)

    if road_dist:
        # Add edge with multiple attributes
        G.add_edge(src, dst,
                   road_distance=road_dist,
                   straight_distance=straight_dist,
                   duration_min=road_dur,
                   weight=road_dist)   # weight = what Dijkstra uses
        print(f"  Edge added: {src} → {dst} | {road_dist} km | {road_dur} mins")
    else:
        print(f"  Road route failed: {src} → {dst}")

    time.sleep(0.5)

print(f"\nGraph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# --- Query the graph ---
def find_shortest_path(graph, source, destination):
    source = source.split(",")[0].strip()
    destination = destination.split(",")[0].strip()

    if source not in graph or destination not in graph:
        return None, None, None

    try:
        path = nx.dijkstra_path(graph, source, destination, weight="weight")
        distance = nx.dijkstra_path_length(graph, source, destination, weight="weight")
        return path, round(distance, 2), " → ".join(path)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, None, None

# --- Run Dijkstra for all source-destination pairs and save to Excel ---
results = []

for i, row in df.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()

    path, distance, path_str = find_shortest_path(G, src, dst)

    results.append({
        "Source"           : src,
        "Destination"      : dst,
        "Shortest_Path"    : path_str if path_str else "No path found",
        "Road_Distance_km" : distance if distance else "N/A",
    })

    print(f"Row {i+1}: {src} → {dst} | {distance} km | {path_str}")

# Save to Excel
results_df = pd.DataFrame(results)
results_df.to_excel("Shortest_Paths.xlsx", index=False)
print(f"\nDone! Saved to Shortest_Paths.xlsx")
