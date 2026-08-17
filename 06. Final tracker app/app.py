from flask import Flask, render_template, jsonify
from flask_sock import Sock
import json
import math
import time

app = Flask(__name__)
sock = Sock(app)

# --- Load routes ---
with open("routes.geojson") as f:
    geojson = json.load(f)

routes = {}
for feature in geojson["features"]:
    props = feature["properties"]
    src = props["source"]
    dst = props["destination"]
    key = f"{src}||{dst}"
    routes[key] = {
        "source"      : src,
        "destination" : dst,
        "coords"      : feature["geometry"]["coordinates"],  # [lon, lat]
        "distance_km" : props.get("distance_km", 0),
        "duration_min": props.get("duration_min", 0)
    }

TRUCK_SPEED_KMH = 60
UPDATE_INTERVAL = 5

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

def points_to_skip(coords_latlon):
    dist_per_update = (TRUCK_SPEED_KMH / 3600) * UPDATE_INTERVAL
    d = 0
    for i in range(len(coords_latlon) - 1):
        d += haversine(coords_latlon[i][0], coords_latlon[i][1],
                       coords_latlon[i+1][0], coords_latlon[i+1][1])
        if d >= dist_per_update:
            return max(1, i)
    return max(1, len(coords_latlon) // 10)

def remaining_distance(coords_latlon, idx):
    total = 0
    for i in range(idx, len(coords_latlon) - 1):
        total += haversine(coords_latlon[i][0], coords_latlon[i][1],
                           coords_latlon[i+1][0], coords_latlon[i+1][1])
    return round(total, 2)

# --- Routes ---
@app.route("/")
def index():
    # Get unique sources for dropdown
    sources = sorted(set(v["source"] for v in routes.values()))
    return render_template("index.html", sources=sources)

@app.route("/destinations/<source>")
def destinations(source):
    # Return valid destinations for a given source
    dsts = sorted([v["destination"] for k, v in routes.items() if v["source"] == source])
    return jsonify(dsts)

@app.route("/route/<source>/<destination>")
def get_route(source, destination):
    key = f"{source}||{destination}"
    if key not in routes:
        return jsonify({"error": "Route not found"}), 404
    data = routes[key]
    # Flip [lon, lat] → [lat, lon] for Leaflet
    coords_latlon = [[c[1], c[0]] for c in data["coords"]]
    return jsonify({
        "coords"      : coords_latlon,
        "distance_km" : data["distance_km"],
        "duration_min": data["duration_min"]
    })

# --- WebSocket ---
@sock.route("/ws")
def simulate(ws):
    # Receive selected route from browser
    msg = json.loads(ws.receive())
    source = msg["source"]
    destination = msg["destination"]

    key = f"{source}||{destination}"
    if key not in routes:
        ws.send(json.dumps({"error": "Route not found"}))
        return

    data = routes[key]
    coords_latlon = [[c[1], c[0]] for c in data["coords"]]
    skip = points_to_skip(coords_latlon)
    idx = 0

    while idx < len(coords_latlon) - 1:
        rem = remaining_distance(coords_latlon, idx)
        eta = round((rem / TRUCK_SPEED_KMH) * 60, 1)

        # Send current position to browser
        ws.send(json.dumps({
            "lat"         : coords_latlon[idx][0],
            "lon"         : coords_latlon[idx][1],
            "remaining_km": rem,
            "eta_min"     : eta,
            "progress"    : round((idx / len(coords_latlon)) * 100, 1),
            "stop"        : idx + 1,
            "total_stops" : len(coords_latlon)
        }))

        idx = min(idx + skip, len(coords_latlon) - 1)
        time.sleep(UPDATE_INTERVAL)

    # Send arrived message
    ws.send(json.dumps({"arrived": True}))

if __name__ == "__main__":
    app.run(debug=True)