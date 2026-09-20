"""
Realistic Live Integration - Real TransLink Data on Real Network
================================================================
Fetches LIVE Brisbane TransLink service alerts and applies them to
the realistic routing network.

If transit is disrupted (alerts mention Milton/CBD transit issues),
adds penalty to Transit modes, making Rideshare/Walk more attractive.

Run: python3 realistic_live_integration.py
"""

import json
import requests
from google.transit import gtfs_realtime_pb2
import numpy as np
from collections import Counter

# Load realistic network
try:
    with open("realistic_network.json", "r") as f:
        network_data = json.load(f)
except FileNotFoundError:
    print("Error: realistic_network.json not found.")
    print("Run realistic_network_builder.py first.")
    raise SystemExit(1)

origins = list(network_data["origins"].keys())
modes = list(network_data["modes"].keys())
edges = network_data["edges"]

TIME_SCALE = 60.0
FARE_SCALE = 25.0
N_ATTENDEES = 300

SEQ_ALERTS_URL = "https://gtfsrt.api.translink.com.au/api/realtime/SEQ/alerts"

KEYWORDS = {
    "CBD": ["cbd", "central", "queen street", "brisbane city"],
    "MIL": ["milton", "herston", "ipswich", "rosewood"],
}

rng = np.random.default_rng(42)
pop_origin = rng.choice(origins, size=N_ATTENDEES)
pop_w_time = rng.uniform(0.0, 1.0, size=N_ATTENDEES)


def parse_edge_key(key_str):
    """Convert JSON string key back to tuple."""
    key_str = key_str.strip("'\"()")
    parts = key_str.split(", ")
    return (parts[0].strip("'\""), parts[1].strip("'\""))


def fetch_live_alerts(url=SEQ_ALERTS_URL, timeout=10):
    """Fetch live TransLink alerts."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    
    alerts = []
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        text = alert.header_text.translation[0].text if alert.header_text.translation else ""
        route_ids = [ie.route_id for ie in alert.informed_entity if ie.route_id]
        stop_ids = [ie.stop_id for ie in alert.informed_entity if ie.stop_id]
        alerts.append((text, route_ids, stop_ids))
    
    return alerts


def clusters_affected(alerts):
    """Detect which areas are affected by live alerts."""
    affected = set()
    
    for text, route_ids, stop_ids in alerts:
        haystack = " ".join([text] + route_ids + stop_ids).lower()
        
        for cluster, keywords in KEYWORDS.items():
            if any(kw in haystack for kw in keywords):
                affected.add(cluster)
    
    return affected


def get_cost(origin, mode, w_time, transit_penalty=0.0):
    """Get scalarised cost with transit-specific penalty."""
    w_fare = 1.0 - w_time
    
    for key_str, edge_data in edges.items():
        key = parse_edge_key(key_str) if isinstance(key_str, str) else key_str
        if key == (origin, mode):
            time_min = edge_data["time_min"]
            fare_aud = edge_data["fare_aud"]
            
            # Apply penalty to transit modes only
            if "Transit" in mode:
                time_min = time_min + transit_penalty
            
            cost = w_time * (time_min / TIME_SCALE) + w_fare * (fare_aud / FARE_SCALE)
            return cost, time_min, fare_aud
    
    return None, None, None


def compute_choices(transit_penalty=0.0):
    """Compute mode choices for all attendees."""
    costs = np.zeros((N_ATTENDEES, len(modes)))
    
    for i in range(N_ATTENDEES):
        for j, mode in enumerate(modes):
            cost, _, _ = get_cost(pop_origin[i], mode, pop_w_time[i], transit_penalty)
            costs[i, j] = cost if cost is not None else np.inf
    
    return costs.argmin(axis=1)


if __name__ == "__main__":
    print("=" * 80)
    print("REALISTIC LIVE INTEGRATION: TransLink Alerts → Mode Choice")
    print("=" * 80)
    print()
    
    # Fetch live alerts
    print("Fetching live Brisbane TransLink service alerts (SEQ)...")
    try:
        alerts = fetch_live_alerts()
    except requests.RequestException as e:
        print(f"Network error: {e}")
        print("(This needs normal internet access; sandboxes may be restricted)")
        alerts = []
    
    print(f"Fetched {len(alerts)} live alert(s)")
    print()
    
    # Detect affected areas
    affected = clusters_affected(alerts)
    
    if affected:
        print(f"Live disruptions detected affecting: {sorted(affected)}")
    else:
        print("No live disruptions detected for CBD/Milton")
    
    print()
    
    # Set transit penalty based on live alerts
    if affected:
        transit_penalty = 15.0  # 15 minute penalty if disrupted
        print(f"Applying +{transit_penalty:.0f} min penalty to Transit modes")
    else:
        transit_penalty = 0.0
        print("No penalty (no disruptions)")
    
    print()
    
    # Compute baseline (no disruption)
    baseline_choices = compute_choices(transit_penalty=0.0)
    baseline_load = Counter(modes[j] for j in baseline_choices)
    
    print("BASELINE (no disruption):")
    for mode in modes:
        count = baseline_load.get(mode, 0)
        pct = 100.0 * count / N_ATTENDEES
        print(f"  {mode:20s} {count:3d} attendees ({pct:5.1f}%)")
    
    print()
    
    # Compute live scenario (with disruption penalty if applicable)
    live_choices = compute_choices(transit_penalty=transit_penalty)
    live_load = Counter(modes[j] for j in live_choices)
    
    if transit_penalty > 0:
        print(f"LIVE (with {transit_penalty:.0f} min transit penalty):")
    else:
        print("LIVE (same as baseline, no disruptions):")
    
    for mode in modes:
        count = live_load.get(mode, 0)
        pct = 100.0 * count / N_ATTENDEES
        print(f"  {mode:20s} {count:3d} attendees ({pct:5.1f}%)")
    
    print()
    
    # Show redistribution
    print("MODE SHIFT DUE TO LIVE DISRUPTION:")
    for mode in modes:
        base_count = baseline_load.get(mode, 0)
        live_count = live_load.get(mode, 0)
        shift = live_count - base_count
        if shift != 0:
            direction = "→" if shift > 0 else "←"
            print(f"  {mode:20s} {direction:1s} {abs(shift):3d} attendees")
    
    print()
    print("=" * 80)
    print("INTERPRETATION:")
    print()
    if transit_penalty > 0:
        print("When TransLink alerts disrupt transit, attendees switch to:")
        transit_moved = (baseline_load.get("Transit_Milton", 0) + baseline_load.get("Transit_CBD", 0)) - (live_load.get("Transit_Milton", 0) + live_load.get("Transit_CBD", 0))
        if transit_moved > 0:
            walk_increase = live_load.get("Walk", 0) - baseline_load.get("Walk", 0)
            rideshare_increase = live_load.get("Rideshare", 0) - baseline_load.get("Rideshare", 0)
            print(f"  - {walk_increase} attendees switch to Walking")
            print(f"  - {rideshare_increase} attendees switch to Rideshare")
    else:
        print("No live disruptions detected today.")
        print("Mode preferences remain stable.")
    
    print()
    print("This demonstrates how REAL TransLink data flows into routing recommendations.")
    print("=" * 80)
