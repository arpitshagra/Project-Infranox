"""
Infranox Map & Route Navigation Service
Integrates OpenStreetMap, OSRM (Open Source Routing Machine), and Geopy
to visualize road pavement quality ratings, pothole hazard pins, and safe route planning.
Supports persistent community road survey registry.
"""

import os
import json
import math
import datetime
import requests
import folium
from folium import plugins
from geopy.geocoders import Nominatim

COMMUNITY_DB_PATH = "community_road_network.json"

# Default reference roads with realistic coordinates and pavement quality ratings
DEFAULT_ROAD_SEGMENTS = [
    {
        "road_name": "NH-44 Expressway (Southbound)",
        "start_point": "Civil Lines, Delhi",
        "end_point": "India Gate, Delhi",
        "rating": "Good",
        "health_score": 82.5,
        "color": "#22C55E",  # Green
        "urgency": "Routine Monitoring",
        "survey_date": "2026-10-28",
        "potholes_count": 2,
        "coordinates": [
            [28.6450, 77.2100],
            [28.6380, 77.2150],
            [28.6300, 77.2200],
            [28.6220, 77.2240],
            [28.6140, 77.2280]
        ],
        "potholes": [
            {"id": 101, "lat": 28.6350, "lon": 77.2165, "severity": "Minor", "conf": 0.74, "area": 1420},
            {"id": 102, "lat": 28.6190, "lon": 77.2255, "severity": "Moderate", "conf": 0.81, "area": 2680}
        ]
    },
    {
        "road_name": "MG Road Urban Corridor",
        "start_point": "Connaught Place, Delhi",
        "end_point": "Pragati Maidan, Delhi",
        "rating": "Fair (Moderate)",
        "health_score": 58.0,
        "color": "#EAB308",  # Yellow
        "urgency": "Scheduled Repair (30 Days)",
        "survey_date": "2026-10-29",
        "potholes_count": 5,
        "coordinates": [
            [28.6328, 77.2197],
            [28.6310, 77.2300],
            [28.6280, 77.2400],
            [28.6250, 77.2500]
        ],
        "potholes": [
            {"id": 201, "lat": 28.6320, "lon": 77.2250, "severity": "Minor", "conf": 0.68, "area": 1150},
            {"id": 202, "lat": 28.6300, "lon": 77.2330, "severity": "Moderate", "conf": 0.79, "area": 3100},
            {"id": 203, "lat": 28.6265, "lon": 77.2450, "severity": "Moderate", "conf": 0.72, "area": 2900}
        ]
    },
    {
        "road_name": "Industrial Ring Bypass Road",
        "start_point": "Kashmere Gate, Delhi",
        "end_point": "ITO Crossing, Delhi",
        "rating": "Critical (Hazardous)",
        "health_score": 24.0,
        "color": "#EF4444",  # Red
        "urgency": "Emergency Intervention",
        "survey_date": "2026-10-30",
        "potholes_count": 9,
        "coordinates": [
            [28.6500, 77.2300],
            [28.6450, 77.2400],
            [28.6390, 77.2500],
            [28.6320, 77.2580],
            [28.6220, 77.2650]
        ],
        "potholes": [
            {"id": 301, "lat": 28.6470, "lon": 77.2350, "severity": "Severe", "conf": 0.88, "area": 6200},
            {"id": 302, "lat": 28.6420, "lon": 77.2440, "severity": "Severe", "conf": 0.84, "area": 5800},
            {"id": 303, "lat": 28.6360, "lon": 77.2530, "severity": "Moderate", "conf": 0.75, "area": 3400},
            {"id": 304, "lat": 28.6280, "lon": 77.2600, "severity": "Severe", "conf": 0.91, "area": 7100}
        ]
    }
]


def load_community_roads():
    """Load community surveyed roads from disk; fallback to default if missing."""
    if os.path.exists(COMMUNITY_DB_PATH):
        try:
            with open(COMMUNITY_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print(f"Error loading {COMMUNITY_DB_PATH}: {e}")
    # Initialize and save defaults
    save_community_roads(DEFAULT_ROAD_SEGMENTS)
    return list(DEFAULT_ROAD_SEGMENTS)


def save_community_roads(roads_list):
    """Save community surveyed roads to disk."""
    try:
        with open(COMMUNITY_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(roads_list, f, indent=2)
    except Exception as e:
        print(f"Error saving {COMMUNITY_DB_PATH}: {e}")


def geocode_location(query):
    """
    Geocode address/landmark using free OpenStreetMap Nominatim.
    Returns: (latitude, longitude, formatted_address) or None
    """
    if not query or not str(query).strip():
        return None
    
    # Check if direct coordinate "lat, lon"
    q_str = str(query).strip()
    if "," in q_str:
        parts = q_str.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon, f"Coord ({lat:.4f}, {lon:.4f})"
            except ValueError:
                pass

    try:
        geolocator = Nominatim(user_agent="infranox_road_community_monitor_v3", timeout=6)
        loc = geolocator.geocode(q_str)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception as e:
        print(f"Geocoding notice for '{query}': {e}")
    return None


def get_osrm_route(start_lat, start_lon, end_lat, end_lon):
    """
    Fetch turn-by-turn driving route between two points using free OSRM.
    Returns dict with distance_km, duration_min, and list of [lat, lon] coordinates.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    headers = {"User-Agent": "InfranoxRoadMonitoring/2.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and "routes" in data and data["routes"]:
                route = data["routes"][0]
                dist_km = round(route["distance"] / 1000.0, 2)
                dur_min = round(route["duration"] / 60.0, 1)
                geo_coords = [[pt[1], pt[0]] for pt in route["geometry"]["coordinates"]]
                return {
                    "success": True,
                    "distance_km": dist_km,
                    "duration_min": dur_min,
                    "coordinates": geo_coords
                }
    except Exception as e:
        print(f"OSRM routing error: {e}")
    
    # Fallback to straight-line if offline or timeout
    straight_line = [[start_lat, start_lon], [end_lat, end_lon]]
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(d_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist_km = round(6371.0 * c, 2)
    return {
        "success": True,
        "distance_km": dist_km,
        "duration_min": round(dist_km * 2.5, 1),
        "coordinates": straight_line
    }


def register_video_survey_road(road_name, start_query, end_query, health_score, condition_rating, urgency, unique_pothole_records, video_duration_sec):
    """
    Automatically converts a video survey into an OpenStreetMap mapped road with coordinates and pothole pins.
    Saves to the community database so future travelers see it.
    """
    start_res = geocode_location(start_query)
    end_res = geocode_location(end_query)

    if not start_res or not end_res:
        # Fallback coordinates near Delhi central if geocoding fails
        start_lat, start_lon = (28.6328, 77.2197)
        end_lat, end_lon = (28.6129, 77.2295)
        start_addr = start_query or "Survey Origin"
        end_addr = end_query or "Survey Destination"
    else:
        start_lat, start_lon, start_addr = start_res
        end_lat, end_lon, end_addr = end_res

    # Fetch driving route geometry
    route_obj = get_osrm_route(start_lat, start_lon, end_lat, end_lon)
    coords = route_obj["coordinates"] if (route_obj and route_obj.get("coordinates")) else [[start_lat, start_lon], [end_lat, end_lon]]

    # Color code
    if health_score >= 70.0:
        color = "#22C55E"
    elif health_score >= 50.0:
        color = "#EAB308"
    else:
        color = "#EF4444"

    # Distribute detected potholes along route geometry according to their video timestamps
    pothole_pins = []
    num_p = len(unique_pothole_records)
    if coords and num_p > 0:
        p_list = sorted(unique_pothole_records.values(), key=lambda x: x.get("first_sec", 0))
        for p_i, p_rec in enumerate(p_list):
            t_sec = p_rec.get("first_sec", 0)
            ratio = (t_sec / max(1.0, video_duration_sec)) if video_duration_sec > 0 else ((p_i + 1) / (num_p + 1))
            ratio = max(0.02, min(0.98, ratio))
            c_idx = int(ratio * (len(coords) - 1))
            
            pothole_pins.append({
                "id": p_rec["track_id"],
                "lat": round(coords[c_idx][0], 6),
                "lon": round(coords[c_idx][1], 6),
                "severity": p_rec.get("severity", "Moderate"),
                "conf": p_rec.get("max_conf", 0.70),
                "area": p_rec.get("max_area", 2000),
                "first_sec": round(t_sec, 1)
            })

    survey_entry = {
        "road_name": road_name,
        "start_point": start_addr,
        "end_point": end_addr,
        "rating": condition_rating,
        "health_score": round(float(health_score), 1),
        "color": color,
        "urgency": urgency,
        "survey_date": datetime.date.today().isoformat(),
        "potholes_count": num_p,
        "coordinates": coords,
        "potholes": pothole_pins
    }

    # Persist into community registry
    community_roads = load_community_roads()
    # Replace existing with same name if exists, else append
    existing_idx = next((i for i, r in enumerate(community_roads) if r.get("road_name") == road_name), None)
    if existing_idx is not None:
        community_roads[existing_idx] = survey_entry
    else:
        community_roads.append(survey_entry)
    
    save_community_roads(community_roads)
    return survey_entry, community_roads


def compute_route_road_health(route_coords, road_segments):
    """
    Evaluate pavement condition along the planned route by checking proximity to evaluated roads & potholes.
    Returns detailed safety breakdown and community survey match info.
    """
    total_severe_encountered = 0
    total_moderate_encountered = 0
    total_minor_encountered = 0
    surveyed_segments_hit = []

    for road in road_segments:
        r_coords = road.get("coordinates", [])
        if not r_coords:
            continue

        # Check if route is near this road corridor
        is_road_hit = False
        for r_pt in route_coords[::max(1, len(route_coords)//35)]:
            for road_pt in r_coords[::max(1, len(r_coords)//15)]:
                d_km = math.hypot(road_pt[0] - r_pt[0], road_pt[1] - r_pt[1]) * 111.0
                if d_km < 0.75:  # within 750 meters
                    is_road_hit = True
                    break
            if is_road_hit:
                break

        if is_road_hit:
            surveyed_segments_hit.append({
                "road_name": road.get("road_name", "Surveyed Road"),
                "health_score": road.get("health_score", 70.0),
                "rating": road.get("rating", "Good"),
                "potholes_count": len(road.get("potholes", [])),
                "survey_date": road.get("survey_date", "Recent")
            })

            for p in road.get("potholes", []):
                p_lat = p["lat"]
                p_lon = p["lon"]
                for r_pt in route_coords[::max(1, len(route_coords)//35)]:
                    dist = math.hypot(p_lat - r_pt[0], p_lon - r_pt[1]) * 111.0
                    if dist < 0.6:
                        if p["severity"] == "Severe":
                            total_severe_encountered += 1
                        elif p["severity"] == "Moderate":
                            total_moderate_encountered += 1
                        else:
                            total_minor_encountered += 1
                        break

    if total_severe_encountered > 0:
        safety_status = "🔴 High Hazard Route"
        advice = f"Warning: Planned route traverses segments surveyed with {total_severe_encountered} severe potholes. Drive with caution or choose an alternate corridor."
        route_pci = max(20.0, 100.0 - (total_severe_encountered * 16.0 + total_moderate_encountered * 7.0))
    elif total_moderate_encountered > 1:
        safety_status = "🟡 Moderate Surface Roughness"
        advice = f"Notice: Route has {total_moderate_encountered} moderate potholes reported by prior surveys. Expect road bumps."
        route_pci = max(55.0, 100.0 - (total_moderate_encountered * 8.0 + total_minor_encountered * 3.0))
    else:
        safety_status = "🟢 Smooth / Safe Route"
        advice = "Surveyed pavement conditions along this corridor are in good driving condition."
        route_pci = 92.0

    return {
        "safety_status": safety_status,
        "advice": advice,
        "route_pci": round(route_pci, 1),
        "severe_potholes": total_severe_encountered,
        "moderate_potholes": total_moderate_encountered,
        "minor_potholes": total_minor_encountered,
        "surveyed_segments_hit": surveyed_segments_hit
    }


def reverse_geocode(lat, lon):
    """
    Convert clicked lat/lon coordinates back to a human-readable address using Nominatim.
    Returns address string or coordinate string as fallback.
    """
    try:
        geolocator = Nominatim(user_agent="infranox_road_community_monitor_v3", timeout=6)
        loc = geolocator.reverse((lat, lon), language="en")
        if loc and loc.address:
            return loc.address
    except Exception:
        pass
    return f"{lat:.5f}, {lon:.5f}"


def build_road_quality_map(road_segments, route_data=None, origin_info=None, dest_info=None,
                           click_origin=None, click_dest=None,
                           center_lat=28.6328, center_lon=77.2250, zoom=13):
    """
    Generate an interactive Folium map with:
    - Color-coded road polylines by Health Rating
    - Individual pothole pins with popup metadata
    - Planned driving route (if provided)
    - Origin & Destination markers
    - Multiple base map layers
    """
    if route_data and route_data.get("coordinates"):
        c_list = route_data["coordinates"]
        center_lat = sum(p[0] for p in c_list) / len(c_list)
        center_lon = sum(p[1] for p in c_list) / len(c_list)
    elif road_segments:
        first_road = road_segments[-1]  # center on most recently added road
        if first_road.get("coordinates"):
            center_lat = first_road["coordinates"][0][0]
            center_lon = first_road["coordinates"][0][1]

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap"
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Satellite",
        name="Satellite Imagery"
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        attr="OpenStreetMap HOT",
        name="Humanitarian Detail Map"
    ).add_to(m)

    roads_group = folium.FeatureGroup(name="🛣️ Evaluated Roads (Color-Coded Ratings)").add_to(m)
    potholes_group = folium.FeatureGroup(name="⚠️ Detected Pothole Pins").add_to(m)

    for road in road_segments:
        r_name = road.get("road_name", "Road Segment")
        r_score = road.get("health_score", 70.0)
        r_rating = road.get("rating", "Good")
        r_color = road.get("color", "#22C55E")
        r_urgency = road.get("urgency", "Routine Monitoring")
        r_date = road.get("survey_date", "Recent")
        r_start = road.get("start_point", "N/A")
        r_end = road.get("end_point", "N/A")
        r_coords = road.get("coordinates", [])

        if not r_coords:
            continue

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0 0 4px 0; color: #1E293B;">{r_name}</h4>
            <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 6px;">From: {r_start}<br>To: {r_end}</div>
            <div style="margin-bottom: 5px;">
                <b>Pavement Health:</b> <span style="font-size: 1.15rem; font-weight: bold; color: {r_color};">{r_score}/100</span>
            </div>
            <div><b>Rating:</b> {r_rating}</div>
            <div><b>Maintenance:</b> {r_urgency}</div>
            <div><b>Surveyed:</b> {r_date}</div>
            <div style="margin-top: 5px; font-size: 0.85rem; color: #64748B;">Total Potholes: {len(road.get('potholes', []))}</div>
        </div>
        """

        folium.PolyLine(
            locations=r_coords,
            color=r_color,
            weight=6,
            opacity=0.88,
            tooltip=f"{r_name} | Score: {r_score}/100 ({r_rating})",
            popup=folium.Popup(popup_html, max_width=290)
        ).add_to(roads_group)

        for p in road.get("potholes", []):
            p_id = p.get("id", "N/A")
            p_sev = p.get("severity", "Moderate")
            p_conf = p.get("conf", 0.70)
            p_area = p.get("area", 2000)
            p_time = p.get("first_sec", 0.0)

            pin_color = "red" if p_sev == "Severe" else ("orange" if p_sev == "Moderate" else "green")
            icon_name = "exclamation-triangle" if p_sev == "Severe" else "dot-circle"

            p_popup = f"""
            <div style="font-family: Arial, sans-serif; width: 210px;">
                <b style="color: #0F172A; font-size: 1.05rem;">Pothole #{p_id}</b>
                <div style="margin: 4px 0;"><b>Severity:</b> <span style="color: {pin_color}; font-weight: bold;">{p_sev}</span></div>
                <div><b>Road:</b> {r_name}</div>
                <div><b>Seen at:</b> {p_time}s into drive</div>
                <div><b>Confidence:</b> {p_conf:.2f}</div>
                <div><b>Damaged Area:</b> {p_area:,} px²</div>
            </div>
            """

            folium.Marker(
                location=[p["lat"], p["lon"]],
                icon=folium.Icon(color=pin_color, icon=icon_name, prefix="fa"),
                tooltip=f"Pothole #{p_id} [{p_sev}] on {r_name}",
                popup=folium.Popup(p_popup, max_width=240)
            ).add_to(potholes_group)

    if route_data and route_data.get("coordinates"):
        route_group = folium.FeatureGroup(name="🧭 Selected Driving Route").add_to(m)

        folium.PolyLine(
            locations=route_data["coordinates"],
            color="#2563EB",
            weight=5,
            opacity=0.9,
            dash_array="8, 6",
            tooltip=f"Planned Driving Route ({route_data['distance_km']} km, ~{route_data['duration_min']} mins)"
        ).add_to(route_group)

        start_pt = route_data["coordinates"][0]
        start_label = origin_info.get("address", "Boarding Point") if origin_info else "Boarding Point"
        folium.Marker(
            location=start_pt,
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
            tooltip=f"🟢 Boarding: {start_label}",
            popup=f"<b>Boarding Point (Origin)</b><br>{start_label}"
        ).add_to(route_group)

        end_pt = route_data["coordinates"][-1]
        dest_label = dest_info.get("address", "Destination") if dest_info else "Destination"
        folium.Marker(
            location=end_pt,
            icon=folium.Icon(color="black", icon="flag-checkered", prefix="fa"),
            tooltip=f"🏁 Destination: {dest_label}",
            popup=f"<b>Destination Point</b><br>{dest_label}"
        ).add_to(route_group)

    # Click-to-pin temporary markers (shown before route is finalized)
    if click_origin or click_dest:
        click_group = folium.FeatureGroup(name="📍 Click Selection Pins").add_to(m)
        if click_origin:
            folium.Marker(
                location=[click_origin["lat"], click_origin["lon"]],
                icon=folium.Icon(color="green", icon="map-marker", prefix="fa"),
                tooltip=f"🟢 Origin Pin: {click_origin.get('address', 'Boarding Point')}",
                popup=f"<b>🟢 Boarding Point (Origin)</b><br>{click_origin.get('address', '')}"
            ).add_to(click_group)
        if click_dest:
            folium.Marker(
                location=[click_dest["lat"], click_dest["lon"]],
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
                tooltip=f"🏁 Destination Pin: {click_dest.get('address', 'Destination')}",
                popup=f"<b>🏁 Destination Point</b><br>{click_dest.get('address', '')}"
            ).add_to(click_group)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)

    return m
