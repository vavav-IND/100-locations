import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# --- Page config ---
st.set_page_config(
    page_title="Route Finder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #1a1a2e; color: #eaeaea; }
    
    section[data-testid="stSidebar"] {
        background-color: #16213e;
        border-right: 1px solid #0f3460;
    }
    
    .stSelectbox label, .stRadio label { color: #a8dadc !important; }
    
    .metric-card {
        background: #0f3460;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        border-left: 4px solid #e94560;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #e94560;
    }
    
    .metric-label {
        font-size: 12px;
        color: #a8dadc;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .route-header {
        font-size: 22px;
        font-weight: 700;
        color: #a8dadc;
        margin-bottom: 4px;
    }

    .api-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
    }

    .badge-google { background: #4285F4; color: white; }
    .badge-osrm   { background: #e94560; color: white; }

    div[data-testid="stButton"] button {
        background: #e94560;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Load GeoJSON files ---
@st.cache_data
def load_geojson(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)

    # Convert list of features into a dict keyed by "source||destination"
    # so we can look up routes instantly instead of looping every time
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
            "properties" : props
        }
    return routes

google_routes = load_geojson("routes.geojson")
osrm_routes   = load_geojson("routes_nx.geojson")

# --- Get all unique cities from Google routes ---
all_sources = sorted(set(v["source"] for v in google_routes.values()))

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🗺️ Route Finder")
    st.markdown("---")

    source = st.selectbox("📍 Start", all_sources)

    # Only show destinations that have a route from selected source
    valid_destinations = sorted([
        v["destination"] for k, v in google_routes.items()
        if v["source"] == source
    ])

    destination = st.selectbox("🏁 End", valid_destinations) if valid_destinations else None

    st.markdown("---")

    engine = st.radio(
        "🔀 Routing Engine",
        ["Google Maps", "OSRM + NetworkX"],
        help="Google Maps uses official road data. OSRM + NetworkX uses open-source data with Dijkstra pathfinding."
    )

    find_btn = st.button("Find Route")

# --- Main area ---
st.markdown("## 🗺️ Route Finder")
st.markdown("Select start and end points, choose a routing engine, and click **Find Route**.")

# Base map
m = folium.Map(
    location=[17.5, 75.5],
    zoom_start=7,
    tiles="CartoDB dark_matter"
)

route_found = False

if find_btn and destination:
    key = f"{source}||{destination}"

    # Pick the right dataset based on engine choice
    selected_routes = google_routes if engine == "Google Maps" else osrm_routes

    if key not in selected_routes:
        st.error(f"No route found for {source} → {destination} via {engine}.")
    else:
        data = selected_routes[key]
        coords_lonlat = data["coords"]   # GeoJSON stores [lon, lat]

        # Folium needs [lat, lon] — flip each coordinate pair
        coords_latlon = [[c[1], c[0]] for c in coords_lonlat]

        # Draw route
        route_color = "#4285F4" if engine == "Google Maps" else "#4ade80"
        folium.PolyLine(
            locations=coords_latlon,
            color=route_color,
            weight=5,
            opacity=0.9,
            tooltip=f"{source} → {destination}"
        ).add_to(m)

        # Start marker
        folium.Marker(
            location=coords_latlon[0],
            popup=f"Start: {source}",
            tooltip=source,
            icon=folium.Icon(color="green", icon="play", prefix="fa")
        ).add_to(m)

        # End marker
        folium.Marker(
            location=coords_latlon[-1],
            popup=f"End: {destination}",
            tooltip=destination,
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(m)

        # Auto zoom to fit route
        m.fit_bounds([
            [min(c[0] for c in coords_latlon), min(c[1] for c in coords_latlon)],
            [max(c[0] for c in coords_latlon), max(c[1] for c in coords_latlon)]
        ])

        route_found = True
        props = data["properties"]

# Render map
st_folium(m, width=None, height=570, returned_objects=[])

# --- Info cards ---
if route_found:
    st.markdown("---")
    badge_class = "badge-google" if engine == "Google Maps" else "badge-osrm"
    badge_label = "GOOGLE MAPS" if engine == "Google Maps" else "OSRM + NETWORKX"

    st.markdown(f"""
        <div class="route-header">{source} → {destination}</div>
        <span class="api-badge {badge_class}">{badge_label}</span>
        <br><br>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Pull distance/duration from properties if available
    road_dist = props.get("road_distance_km", props.get("distance_km", "N/A"))
    duration  = props.get("duration_min", "N/A")
    hrs       = round(duration / 60, 1) if isinstance(duration, (int, float)) else "N/A"

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Road Distance</div>
            <div class="metric-value">{road_dist} km</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Est. Duration</div>
            <div class="metric-value">{hrs} hrs</div>
        </div>
        """, unsafe_allow_html=True)