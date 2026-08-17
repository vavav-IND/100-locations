import pandas as pd
import networkx as nx
import requests
import json
import time

def get_road_geometry_osrm(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        data = requests.get(url, timeout=10).json()
        if data["code"] == "Ok":
            # OSRM already returns [lon, lat] format — correct for GeoJSON
            return data["routes"][0]["geometry"]["coordinates"]
        return None
    except:
        return None

# --- Rebuild graph from saved Excel ---
df = pd.read_excel("NetworkX_Routes.xlsx")
coords_df = pd.read_excel("Locations_Google_Coords.xlsx")

G = nx.DiGraph()

# Build coordinates lookup
coords_lookup = {}
for i, row in coords_df.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()
    coords_lookup[src] = (row["src_lat"], row["src_lon"])
    coords_lookup[dst] = (row["dst_lat"], row["dst_lon"])

# Add edges
for i, row in df.iterrows():
    src = row["Source"]
    dst = row["Destination"]
    if src in coords_lookup and dst in coords_lookup:
        lat1, lon1 = coords_lookup[src]
        lat2, lon2 = coords_lookup[dst]
        G.add_node(src, lat=lat1, lon=lon1)
        G.add_node(dst, lat=lat2, lon=lon2)
        G.add_edge(src, dst, weight=row["Road_Distance"])

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# --- GeoJSON structure ---
geojson = {
    "type": "FeatureCollection",
    "features": []
}

# --- Run Dijkstra for all pairs and get road geometry ---
df_pairs = pd.read_excel("Locations_Google_Coords.xlsx")

print(f"\nFetching shortest paths + geometry for {len(df_pairs)} pairs...\n")

for i, row in df_pairs.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()

    if src not in G.nodes or dst not in G.nodes:
        print(f"Row {i+1}: {src} → {dst} ❌ not in graph")
        continue

    try:
        # Get shortest path via Dijkstra
        path = nx.dijkstra_path(G, src, dst, weight="weight")
        distance = nx.dijkstra_path_length(G, src, dst, weight="weight")

        # Get road geometry for each edge in the path
        full_coords = []
        for j in range(len(path) - 1):
            u = path[j]
            v = path[j+1]
            u_lat, u_lon = G.nodes[u]["lat"], G.nodes[u]["lon"]
            v_lat, v_lon = G.nodes[v]["lat"], G.nodes[v]["lon"]

            coords = get_road_geometry_osrm(u_lat, u_lon, v_lat, v_lon)
            if coords:
                full_coords.extend(coords)
            time.sleep(0.3)

        if full_coords:
            feature = {
                "type": "Feature",
                "properties": {
                    "source"         : src,
                    "destination"    : dst,
                    "path"           : " → ".join(path),
                    "road_distance_km": round(distance, 2)
                },
                "geometry": {
                    "type"       : "LineString",
                    "coordinates": full_coords
                }
            }
            geojson["features"].append(feature)
            print(f"Row {i+1}: {src} → {dst} ✅ | Path: {' → '.join(path)} | {round(distance, 2)} km")

    except (nx.NetworkXNoPath, nx.NodeNotFound):
        print(f"Row {i+1}: {src} → {dst} ❌ no path in graph")

# --- Save ---
with open("routes_nx.geojson", "w") as f:
    json.dump(geojson, f, indent=2)

print(f"\nDone! Saved to routes_nx.geojson")
print(f"Total routes: {len(geojson['features'])}")