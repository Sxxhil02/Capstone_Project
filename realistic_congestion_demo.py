"""
Realistic Congestion Demo - Rideshare Bottleneck
=================================================
Models a realistic congestion scenario: rideshare mode gets congested
(limited Ubers available), while walk/transit modes don't.

Shows how congestion-aware routing redistributes people away from
rideshare to transit/walking.

Run: python3 realistic_congestion_demo.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
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

rng = np.random.default_rng(42)
pop_origin = rng.choice(origins, size=N_ATTENDEES)
pop_w_time = rng.uniform(0.0, 1.0, size=N_ATTENDEES)


def parse_edge_key(key_str):
    """Convert JSON string key back to tuple."""
    key_str = key_str.strip("'\"()")
    parts = key_str.split(", ")
    return (parts[0].strip("'\""), parts[1].strip("'\""))


def get_cost(origin, mode, w_time, rideshare_penalty=0.0):
    """Get scalarised cost, accounting for rideshare-specific congestion."""
    w_fare = 1.0 - w_time
    
    for key_str, edge_data in edges.items():
        key = parse_edge_key(key_str) if isinstance(key_str, str) else key_str
        if key == (origin, mode):
            time_min = edge_data["time_min"]
            fare_aud = edge_data["fare_aud"]
            
            # Apply congestion penalty only to rideshare
            if mode == "Rideshare":
                time_min = time_min + rideshare_penalty
            
            cost = w_time * (time_min / TIME_SCALE) + w_fare * (fare_aud / FARE_SCALE)
            return cost, time_min, fare_aud
    
    return None, None, None


# Pre-compute naive costs (no congestion)
naive_costs = np.zeros((N_ATTENDEES, len(modes)))
for i in range(N_ATTENDEES):
    for j, mode in enumerate(modes):
        cost, _, _ = get_cost(pop_origin[i], mode, pop_w_time[i], rideshare_penalty=0.0)
        naive_costs[i, j] = cost if cost is not None else np.inf

naive_choice_idx = naive_costs.argmin(axis=1)
naive_load = Counter(modes[j] for j in naive_choice_idx)

# Figure setup
fig, (ax_penalty, ax_load, ax_regret) = plt.subplots(1, 3, figsize=(15, 5))
plt.subplots_adjust(bottom=0.25, wspace=0.3)


def redraw(k_severity):
    """Redraw all three panels for a given congestion severity."""
    
    # Compute congestion penalty (minutes) based on naive rideshare load
    rideshare_penalty = k_severity * naive_load.get("Rideshare", 0) / 10.0
    
    # Recompute aware costs with penalty
    aware_costs = np.zeros((N_ATTENDEES, len(modes)))
    for i in range(N_ATTENDEES):
        for j, mode in enumerate(modes):
            cost, _, _ = get_cost(
                pop_origin[i],
                mode,
                pop_w_time[i],
                rideshare_penalty=rideshare_penalty,
            )
            aware_costs[i, j] = cost if cost is not None else np.inf
    
    aware_choice_idx = aware_costs.argmin(axis=1)
    aware_load = Counter(modes[j] for j in aware_choice_idx)
    
    # Compute regret
    rows = np.arange(N_ATTENDEES)
    cost_if_naive = aware_costs[rows, naive_choice_idx]
    cost_if_aware = aware_costs[rows, aware_choice_idx]
    D = np.abs(cost_if_naive - cost_if_aware)
    redirected = naive_choice_idx != aware_choice_idx
    
    # Panel 1: Congestion penalty
    ax_penalty.clear()
    penalties = {mode: 0.0 if mode != "Rideshare" else rideshare_penalty for mode in modes}
    colors = ["orange" if mode == "Rideshare" else "lightblue" for mode in modes]
    ax_penalty.bar(modes, [penalties[m] for m in modes], color=colors)
    ax_penalty.set_ylabel("Penalty (minutes)")
    ax_penalty.set_title("Mode-Specific Congestion Penalty", fontsize=10)
    ax_penalty.tick_params(axis="x", rotation=45)
    
    # Panel 2: Load shift
    ax_load.clear()
    x = np.arange(len(modes))
    width = 0.35
    naive_counts = [naive_load.get(m, 0) for m in modes]
    aware_counts = [aware_load.get(m, 0) for m in modes]
    ax_load.bar(x - width / 2, naive_counts, width, label="Naive", color="steelblue")
    ax_load.bar(x + width / 2, aware_counts, width, label="Aware", color="crimson")
    ax_load.set_xticks(x)
    ax_load.set_xticklabels(modes, rotation=45, ha="right")
    ax_load.set_ylabel("Number of Attendees")
    ax_load.set_title("Load Redistribution", fontsize=10)
    ax_load.legend()
    
    # Panel 3: Regret
    ax_regret.clear()
    ax_regret.hist(D, bins=20, color="slategray", edgecolor="black")
    ax_regret.axvline(D.mean(), color="crimson", linestyle="--", linewidth=1.5)
    changed_pct = np.mean(redirected) * 100
    ax_regret.set_title(
        f"Regret Distribution (mean={D.mean():.3f})\n"
        f"{changed_pct:.0f}% redirected",
        fontsize=10,
    )
    ax_regret.set_xlabel("Regret D_i")
    ax_regret.set_ylabel("Count")
    
    fig.canvas.draw_idle()


# Slider for congestion severity
ax_k = plt.axes([0.15, 0.12, 0.7, 0.03])
slider_k = Slider(
    ax_k,
    "Rideshare Congestion Severity (k)",
    0.0,
    1.0,
    valinit=0.5,
    color="orange",
)
slider_k.on_changed(lambda val: redraw(val))

if __name__ == "__main__":
    redraw(0.5)
    fig.suptitle(
        "REALISTIC BRISBANE: Rideshare Bottleneck Congestion",
        fontsize=12,
    )
    plt.show()
