import pandas as pd
import networkx as nx
import folium

# --- Rebuild graph from saved Excel ---
df = pd.read_excel("NetworkX_Routes.xlsx")
coords_df = pd.read_excel("Locations_Google_Coords.xlsx")

G = nx.DiGraph()

# Add edges
for i, row in df.iterrows():
    G.add_edge(row["Source"], row["Destination"], weight=row["Road_Distance"])

# Add coordinates to nodes from the coords file
for i, row in coords_df.iterrows():
    src = row["Source"].split(",")[0].strip()
    dst = row["Destination"].split(",")[0].strip()
    if src in G.nodes:
        G.nodes[src]["lat"] = row["src_lat"]
        G.nodes[src]["lon"] = row["src_lon"]
    if dst in G.nodes:
        G.nodes[dst]["lat"] = row["dst_lat"]
        G.nodes[dst]["lon"] = row["dst_lon"]

# --- Create Folium map centered on India ---
m = folium.Map(location=[18.5, 75.5], zoom_start=7)

# --- Plot nodes (cities) as circle markers ---
for node, data in G.nodes(data=True):
    if "lat" in data and "lon" in data:
        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=6,
            color="blue",
            fill=True,
            fill_color="skyblue",
            fill_opacity=0.8,
            popup=node,          # click on node to see city name
            tooltip=node         # hover to see city name
        ).add_to(m)

# --- Plot edges (roads) as lines ---
for u, v, data in G.edges(data=True):
    u_data = G.nodes[u]
    v_data = G.nodes[v]

    # Only draw if both nodes have coordinates
    if "lat" in u_data and "lat" in v_data:
        folium.PolyLine(
            locations=[
                [u_data["lat"], u_data["lon"]],
                [v_data["lat"], v_data["lon"]]
            ],
            color="red",
            weight=2,
            opacity=0.7,
            tooltip=f"{u} → {v} | {data['weight']} km"  # hover to see distance
        ).add_to(m)

# --- Highlight a specific path ---
def highlight_path(graph, source, destination):
    try:
        path = nx.dijkstra_path(graph, source, destination, weight="weight")
        distance = nx.dijkstra_path_length(graph, source, destination, weight="weight")

        # Draw the shortest path in green, thicker
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            folium.PolyLine(
                locations=[
                    [u_data["lat"], u_data["lon"]],
                    [v_data["lat"], v_data["lon"]]
                ],
                color="green",
                weight=5,
                opacity=1,
                tooltip=f"SHORTEST: {u} → {v}"
            ).add_to(m)

        print(f"Shortest path: {' → '.join(path)} | {round(distance, 2)} km")

    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        print(f"No path found: {e}")

# --- Change these to query any two cities ---
highlight_path(G, "Miraj", "Walwa")

# --- Save as HTML ---
m.save("route_map.html")
print("Map saved as route_map.html — open it in your browser!")