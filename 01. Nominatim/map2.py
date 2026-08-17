import pandas as pd
import networkx as nx
import folium
import requests

# --- Get actual road geometry from OSRM ---
def get_road_geometry(lat1, lon1, lat2, lon2):
    """
    overview=full    → give us the complete route shape
    geometries=geojson → coordinates in [lon, lat] format
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        data = requests.get(url, timeout=10).json()
        if data["code"] == "Ok":
            # Returns list of [lon, lat] points along the actual road
            coordinates = data["routes"][0]["geometry"]["coordinates"]
            # Folium needs [lat, lon] not [lon, lat] — so we flip each pair
            return [[coord[1], coord[0]] for coord in coordinates]
        return None
    except:
        return None

# --- Rebuild graph ---
df = pd.read_excel("NetworkX_Routes.xlsx")
coords_df = pd.read_excel("Locations_Google_Coords.xlsx")

G = nx.DiGraph()

for i, row in df.iterrows():
    G.add_edge(row["Source"], row["Destination"], weight=row["Road_Distance"])

for i, row in coords_df.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()
    if src in G.nodes:
        G.nodes[src]["lat"] = row["src_lat"]
        G.nodes[src]["lon"] = row["src_lon"]
    if dst in G.nodes:
        G.nodes[dst]["lat"] = row["dst_lat"]
        G.nodes[dst]["lon"] = row["dst_lon"]

# --- Create map ---
m = folium.Map(location=[18.5, 75.5], zoom_start=7)

# --- Plot all edges as actual roads ---
print("Fetching road geometry for all edges...")
for u, v, data in G.edges(data=True):
    u_data = G.nodes[u]
    v_data = G.nodes[v]

    if "lat" in u_data and "lat" in v_data:
        road_points = get_road_geometry(
            u_data["lat"], u_data["lon"],
            v_data["lat"], v_data["lon"]
        )
        if road_points:
            folium.PolyLine(
                locations=road_points,
                color="red",
                weight=2,
                opacity=0.5,
                tooltip=f"{u} → {v} | {data['weight']} km"
            ).add_to(m)

# --- Plot nodes ---
for node, data in G.nodes(data=True):
    if "lat" in data and "lon" in data:
        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=6,
            color="blue",
            fill=True,
            fill_color="skyblue",
            fill_opacity=0.8,
            tooltip=node
        ).add_to(m)

# --- Highlight shortest path as actual road ---
def highlight_path(graph, source, destination):
    try:
        path = nx.dijkstra_path(graph, source, destination, weight="weight")
        distance = nx.dijkstra_path_length(graph, source, destination, weight="weight")

        print(f"\nShortest path: {' → '.join(path)} | {round(distance, 2)} km")

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]

            road_points = get_road_geometry(
                u_data["lat"], u_data["lon"],
                v_data["lat"], v_data["lon"]
            )

            if road_points:
                folium.PolyLine(
                    locations=road_points,
                    color="green",
                    weight=6,
                    opacity=1,
                    tooltip=f"SHORTEST: {u} → {v}"
                ).add_to(m)

                # Add start and end markers
                folium.Marker(
                    location=[u_data["lat"], u_data["lon"]],
                    popup=f"Start: {u}",
                    icon=folium.Icon(color="green", icon="play")
                ).add_to(m)

                folium.Marker(
                    location=[v_data["lat"], v_data["lon"]],
                    popup=f"End: {v}",
                    icon=folium.Icon(color="red", icon="stop")
                ).add_to(m)

    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        print(f"No path found: {e}")

# --- Change these to your cities ---
highlight_path(G, "Miraj", "Walwa")

m.save("route_map.html")
print("\nMap saved! Open route_map.html in your browser.")