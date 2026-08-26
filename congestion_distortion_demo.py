"""
Toy model: congestion-naive vs. congestion-aware boundary routing
-----------------------------------------------------------------------
Companion to "Preference-Sensitive Boundary Routing for Event Travel"
and to outer_routing_demo.py, which this script imports and reuses.

Idea
----
outer_routing_demo.py ranks boundary nodes for a traveller using only
their own path attributes (time, fare) -- congestion near the venue is
ignored entirely, on the assumption that the outer network is what
matters and the inner network can be dealt with separately.

This script tests how costly that simplification is. It:

  1. Routes a synthetic population of travellers "congestion-naively"
     (exactly as in outer_routing_demo.py) and tallies how many pick
     each boundary node -- this is the naive load.
  2. Turns that naive load into a simple congestion penalty g_j per
     boundary node (more people converging on a node -> more delay
     near the venue). This is a crude stand-in for a real inner-network
     assignment, not one -- see the write-up for the honest version of
     that caveat.
  3. Re-routes the same travellers "congestion-aware", i.e. using
     Ci_aware(j) = Ci(j) + w_time * g_j, and tallies the new load.
  4. For every traveller, computes the distortion of having followed
     the naive recommendation instead of the aware one:
         D_i = | Ci_aware(j_naive) - Ci_aware(j_aware) |
     evaluated under the *true* (aware) cost, i.e. the realised
     regret of ignoring congestion.

Controls
--------
- Slider: congestion severity k (minutes of extra delay per traveller
  converging on a boundary node). k=0 recovers the naive-only case.
- The three panels update live: the congestion penalty per boundary
  node, how load redistributes from naive to aware routing, and the
  distribution of regret D_i across the population.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from collections import Counter

import outer_routing_demo as base  # reuses the network, Pareto labels, scales

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------
# 1. Synthetic traveller population
# ---------------------------------------------------------------------
N_TRAVELLERS = 300
pop_origin = rng.choice(base.origins, size=N_TRAVELLERS)
pop_w_time = rng.uniform(0.0, 1.0, size=N_TRAVELLERS)


def min_cost(source, j, w_time):
    """Scalarised cost of the cheapest Pareto-optimal path from source to
    boundary node j, under weight w_time (fare weight = 1 - w_time)."""
    w_fare = 1.0 - w_time
    labels = base.labels_by_source[source][j]
    return min(
        w_time * (t / base.TIME_SCALE) + w_fare * (f / base.FARE_SCALE)
        for (t, f, _, _) in labels
    )


# Pre-tabulate naive cost for every (traveller, boundary node) -- cheap,
# graph and population are both tiny.
naive_cost_table = np.zeros((N_TRAVELLERS, len(base.boundary_nodes)))
for i in range(N_TRAVELLERS):
    for jx, b in enumerate(base.boundary_nodes):
        naive_cost_table[i, jx] = min_cost(pop_origin[i], b, pop_w_time[i])

naive_choice_idx = naive_cost_table.argmin(axis=1)
naive_load = Counter(base.boundary_nodes[jx] for jx in naive_choice_idx)


def run_congestion_analysis(k):
    """Given congestion severity k (minutes of delay per traveller
    converging on a boundary node, derived from the naive load), compute
    the congestion-aware recommendation and per-traveller regret."""
    g = {b: k * naive_load.get(b, 0) for b in base.boundary_nodes}
    g_vec = np.array([g[b] for b in base.boundary_nodes])

    aware_cost_table = naive_cost_table + pop_w_time[:, None] * (g_vec[None, :] / base.TIME_SCALE)
    aware_choice_idx = aware_cost_table.argmin(axis=1)
    aware_load = Counter(base.boundary_nodes[jx] for jx in aware_choice_idx)

    # regret of following the naive choice, judged under the true (aware) cost
    rows = np.arange(N_TRAVELLERS)
    cost_if_naive = aware_cost_table[rows, naive_choice_idx]
    cost_if_aware = aware_cost_table[rows, aware_choice_idx]
    D = np.abs(cost_if_naive - cost_if_aware)

    changed_frac = np.mean(naive_choice_idx != aware_choice_idx)
    return g, aware_load, D, changed_frac


# ---------------------------------------------------------------------
# 2. Figure and widgets
# ---------------------------------------------------------------------

fig, (ax_g, ax_load, ax_hist) = plt.subplots(1, 3, figsize=(15, 5.5))
plt.subplots_adjust(bottom=0.25, wspace=0.35)

K_INIT = 0.4


def redraw(k):
    g, aware_load, D, changed_frac = run_congestion_analysis(k)

    ax_g.clear()
    names = base.boundary_nodes
    ax_g.bar(names, [g[b] for b in names], color="darkorange")
    ax_g.set_title("Congestion penalty g_j\n(minutes, derived from naive load)", fontsize=10)
    ax_g.set_ylim(0, max(K_INIT * N_TRAVELLERS, 1) * 1.1)

    ax_load.clear()
    x = np.arange(len(names))
    width = 0.35
    naive_counts = [naive_load.get(b, 0) for b in names]
    aware_counts = [aware_load.get(b, 0) for b in names]
    ax_load.bar(x - width / 2, naive_counts, width, label="naive", color="steelblue")
    ax_load.bar(x + width / 2, aware_counts, width, label="aware", color="crimson")
    ax_load.set_xticks(x)
    ax_load.set_xticklabels(names)
    ax_load.set_title("Traveller load per boundary node\n(naive vs. congestion-aware)", fontsize=10)
    ax_load.legend(fontsize=8)

    ax_hist.clear()
    ax_hist.hist(D, bins=20, color="slategray")
    ax_hist.axvline(D.mean(), color="crimson", linestyle="--", linewidth=1.5)
    ax_hist.set_title(
        f"Regret D_i of following naive advice\nmean={D.mean():.3f}, "
        f"{changed_frac * 100:.0f}% of travellers redirected",
        fontsize=10,
    )
    ax_hist.set_xlabel("D_i")

    fig.suptitle(
        f"Congestion severity k = {k:.2f} min/traveller"
        + ("  (k=0: congestion has no effect, aware = naive)" if k == 0 else ""),
        fontsize=11,
    )
    fig.canvas.draw_idle()


ax_slider = plt.axes([0.2, 0.08, 0.6, 0.04])
slider = Slider(ax_slider, "k (congestion severity)", 0.0, 1.0, valinit=K_INIT)


def on_slider(val):
    redraw(val)


slider.on_changed(on_slider)

if __name__ == "__main__":
    redraw(K_INIT)
    plt.show()
