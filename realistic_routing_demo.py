"""
Realistic Routing Demo - Interactive Pareto Routing on Real Brisbane Network
=============================================================================
Takes the realistic network (real coords, real fares) and runs the same
Pareto multi-objective routing as the toy model, but on REAL data.

Drag the w_time slider to see how time vs fare preferences change which
travel mode is recommended.

Run: python3 realistic_routing_demo.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons

# Load the realistic network built by realistic_network_builder.py
try:
    with open("realistic_network.json", "r") as f:
        network_data = json.load(f)
except FileNotFoundError:
    print("Error: realistic_network.json not found.")
    print("Run realistic_network_builder.py first to create it.")
    raise SystemExit(1)

origins = list(network_data["origins"].keys())
modes = list(network_data["modes"].keys())
edges = network_data["edges"]

TIME_SCALE = 60.0
FARE_SCALE = 25.0


def parse_edge_key(key_str):
    """Convert JSON string key back to tuple."""
    # JSON serializes ("CBD0", "Walk") as '("CBD0", "Walk")' - parse it
    key_str = key_str.strip("'\"()")
    parts = key_str.split(", ")
    return (parts[0].strip("'\""), parts[1].strip("'\""))


def get_cost(origin, mode, w_time):
    """Get scalarised cost for an origin-mode combination."""
    w_fare = 1.0 - w_time
    
    # Find the edge
    for key_str, edge_data in edges.items():
        key = parse_edge_key(key_str) if isinstance(key_str, str) else key_str
        if key == (origin, mode):
            time_min = edge_data["time_min"]
            fare_aud = edge_data["fare_aud"]
            cost = w_time * (time_min / TIME_SCALE) + w_fare * (fare_aud / FARE_SCALE)
            return cost, time_min, fare_aud
    
    return None, None, None


def rank_modes(origin, w_time):
    """Rank all modes by cost for a given origin and preference."""
    costs = {}
    for mode in modes:
        cost, time, fare = get_cost(origin, mode, w_time)
        if cost is not None:
            costs[mode] = (cost, time, fare)
    
    return sorted(costs.items(), key=lambda x: x[1][0])


# Create figure
fig, (ax_net, ax_bar) = plt.subplots(1, 2, figsize=(14, 6))
plt.subplots_adjust(bottom=0.35, wspace=0.3)


def update(val):
    """Update plots when slider changes."""
    w_time = slider_w.get_val()
    w_fare = 1.0 - w_time
    origin = radio.value_selected
    
    # Left panel: mode cost comparison
    ax_net.clear()
    
    ranked = rank_modes(origin, w_time)
    mode_names = [m for m, _ in ranked]
    costs = [c for _, (c, _, _) in ranked]
    colors = ["red" if i == 0 else "steelblue" for i in range(len(mode_names))]
    
    ax_net.barh(mode_names, costs, color=colors)
    ax_net.set_xlabel("Scalarised Cost")
    ax_net.set_title(
        f"Mode Ranking for {origin}\n"
        f"w_time={w_time:.2f}, w_fare={w_fare:.2f}",
        fontsize=10,
    )
    ax_net.invert_yaxis()
    
    # Right panel: detailed breakdown
    ax_bar.clear()
    
    x = np.arange(len(ranked))
    times = [t for _, (_, t, _) in ranked]
    fares = [f for _, (_, _, f) in ranked]
    
    width = 0.35
    ax_bar.bar(x - width / 2, times, width, label="Time (min)", color="steelblue")
    ax_bar.bar(x + width / 2, fares, width, label="Fare ($)", color="orange")
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels([m for m, _ in ranked], rotation=45, ha="right")
    ax_bar.set_ylabel("Value")
    ax_bar.set_title("Time vs Fare Breakdown", fontsize=10)
    ax_bar.legend()
    
    fig.canvas.draw_idle()


# Slider for w_time
ax_w = plt.axes([0.15, 0.20, 0.7, 0.03])
slider_w = Slider(
    ax_w,
    "w_time (0=fare-focused, 1=time-focused)",
    0.0,
    1.0,
    valinit=0.5,
    color="steelblue",
)
slider_w.on_changed(update)

# Radio buttons for origin selection
ax_radio = plt.axes([0.15, 0.05, 0.15, 0.12])
radio = RadioButtons(ax_radio, origins, active=0)
radio.on_clicked(lambda label: update(None))

if __name__ == "__main__":
    update(None)
    plt.suptitle("REALISTIC BRISBANE ROUTING: Preference-Sensitive Mode Choice", fontsize=12)
    plt.show()
