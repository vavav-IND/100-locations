import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import time
import math
import streamlit.components.v1 as components

# --- Constants ---
TRUCK_SPEED_KMH = 60        # average truck speed
UPDATE_INTERVAL = 5         # seconds between each position update

# --- Haversine to calculate distance between two coordinates ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

# --- Load GeoJSON ---
def load_routes(filepath):
    with open(filepath) as f:
        data = json.load(f)
    routes = {}
    for feature in data["features"]:
        props = feature["properties"]
        src = props["source"]
        dst = props["destination"]
        key = f"{src}||{dst}"
        routes[key] = {
            "source"     : src,
            "destination": dst,
            "coords"     : feature["geometry"]["coordinates"],  # list of [lon, lat]
            "distance_km": props.get("distance_km", None),
            "duration_min": props.get("duration_min", None)
        }
    return routes

# --- Calculate how many points to skip per update ---
def points_to_skip(coords, speed_kmh, interval_sec):
    # Distance covered per update in km
    dist_per_update = (speed_kmh / 3600) * interval_sec  # km

    # TODO: starting from index 0, keep adding haversine distances
    # between consecutive points until you've covered dist_per_update km
    d=0
    for i in range (len(coords)-1):
        a=haversine(coords[i][1], coords[i][0], coords[i+1][1], coords[i+1][0])
        d+=a
    # return how many points that took
        if(d>=dist_per_update):
            return max(1, i)   # never return 0
    return max(1, len(coords) // 10)  # fallback — jump 10% of route

# --- Calculate remaining distance from current index to end ---
def remaining_distance(coords, current_index):
    total = 0
    # TODO: sum haversine distances between all consecutive points
    # from current_index to end of coords list
    for i in range(current_index, len(coords)-1):
        total+=haversine(coords[i][1], coords[i][0], coords[i+1][1], coords[i+1][0])
    return total

# --- Build folium map for current truck position ---
def build_map(coords_latlon, current_index, source, destination):
    # Current truck position
    current_pos = coords_latlon[current_index]

    m = folium.Map(location=current_pos, zoom_start=10, tiles="CartoDB dark_matter")

    # After adding all polylines and markers, fit to remaining route
    remaining = coords_latlon[current_index:]
    if len(remaining) > 1:
        m.fit_bounds([
            [min(c[0] for c in remaining), min(c[1] for c in remaining)],
            [max(c[0] for c in remaining), max(c[1] for c in remaining)]
        ])

    # TODO: draw the already-travelled path in gray
    # hint: coords_latlon[:current_index+1]
    route_color = "#808080"
    folium.PolyLine(
        locations=coords_latlon[:current_index+1],
        color=route_color,
        weight=5,
        opacity=0.9
    ).add_to(m)

    # TODO: draw the remaining path in blue
    # hint: coords_latlon[current_index:]
    folium.PolyLine(
        locations=coords_latlon[current_index:],
        color="#4A90D9",
        weight=5,
        opacity=0.9
    ).add_to(m)

    # TODO: add a marker for the truck's current position
    # use folium.Marker with a truck emoji as icon or CircleMarker in green
    folium.Marker(
        location=current_pos,
        icon=folium.DivIcon(html='<div style="font-size:24px">🚚</div>')
    ).add_to(m)

    # TODO: add a marker for the destination
    # use folium.Marker with a flag icon in red
    folium.Marker(
        location=coords_latlon[-1],
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    return m

# --- Main app ---
st.set_page_config(page_title="GPS Tracker", layout="wide")
st.title("🚛 Truck GPS Simulation")

# Load routes
routes = load_routes("routes.geojson")
all_sources = sorted(set(v["source"] for v in routes.values()))

# Sidebar
with st.sidebar:
    source = st.selectbox("Source", all_sources)
    valid_destinations = [v["destination"] for k, v in routes.items() if v["source"] == source]
    destination = st.selectbox("Destination", sorted(valid_destinations))
    start_btn = st.button("Start Simulation")

# --- Session state ---
# Streamlit loses all variables on every rerun
# st.session_state persists variables across reruns — like a global variable
if "running" not in st.session_state:
    st.session_state.running = False
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "coords" not in st.session_state:
    st.session_state.coords = []
if "skip" not in st.session_state:
    st.session_state.skip = 1
if "source" not in st.session_state:      # ADD THESE TWO
    st.session_state.source = ""
if "destination" not in st.session_state:
    st.session_state.destination = ""

if start_btn:
    key = f"{source}||{destination}"
    data = routes[key]

    # TODO: load coords from data, flip from [lon,lat] to [lat,lon]
    # store in st.session_state.coords
    coords_lonlat=data["coords"]
    coords_latlon=[[c[1], c[0]] for c in coords_lonlat]
    st.session_state.coords=coords_latlon

    # TODO: calculate skip using points_to_skip()
    # store in st.session_state.skip
    st.session_state.skip=points_to_skip(st.session_state.coords, TRUCK_SPEED_KMH, UPDATE_INTERVAL)


    st.session_state.current_index = 0
    st.session_state.running = True
    st.session_state.source = source           
    st.session_state.destination = destination

# --- Simulation loop ---
placeholder = st.empty()

if st.session_state.running:
    coords = st.session_state.coords
    idx    = st.session_state.current_index
    skip   = st.session_state.skip
    src    = st.session_state.source           # USE FROM SESSION STATE
    dst    = st.session_state.destination

    if idx >= len(coords) - 1:
        # TODO: show arrived message, set running to False
        st.success("Truck has arrived at the destination!")
        st.session_state.running = False

    else:
        with placeholder.container():
            st.write(f"Skip: {skip}, Total coords: {len(coords)}")
            # Build and show map
            m = build_map(coords, idx, src, dst)
            map_html = m._repr_html_()
            components.html(map_html, height=500)

            # Info cards
            rem_dist = remaining_distance(coords, idx)
            # TODO: calculate ETA in minutes using rem_dist and TRUCK_SPEED_KMH
            eta_min = 0
            eta_min=round((rem_dist/TRUCK_SPEED_KMH)*60,1)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Stop", f"{idx+1} / {len(coords)}")
            with col2:
                st.metric("Remaining Distance", f"{round(rem_dist, 2)} km")
            with col3:
                # TODO: display ETA
                st.metric("ETA", f"{eta_min} mins")

        # Move truck forward
        # TODO: update st.session_state.current_index by adding skip
        # make sure it doesn't go beyond len(coords) - 1
        st.session_state.current_index=min(idx+skip, len(coords)-1)


        time.sleep(UPDATE_INTERVAL)
        st.rerun()