"""
Toy model: preference-sensitive gate routing for a Suncorp Stadium concert
-----------------------------------------------------------------------
Companion to "Preference-Sensitive Boundary Routing for Event Travel".

Scenario: attendees of a (fictional) concert at Suncorp Stadium,
Brisbane, are travelling from two starting-point clusters -- the CBD
and Milton -- through a small synthetic outer road/transit network,
towards one of four stadium gates.

This is deliberately crude: a small hand-laid-out DAG stands in for
the outer network, and only two objectives (time, fare) are used so
the whole thing can be shown on a single slider. Congestion at the
gates is NOT modelled here on purpose -- this script tests only the
first half of the research idea, namely how much an attendee's
recommended gate moves as their own preference weights change. It is
Pareto-exact for this toy graph (multi-label DAG shortest paths / a
simplified, heuristic-free NAMOA*), not an approximation.

Controls
--------
- Slider at the bottom: time-weight w_time (fare-weight = 1 - w_time).
- Radio buttons: pick which attendee (origin) to inspect.
- The network panel highlights the recommended path in bold; the bar
  panel shows the scalarised cost to every gate, cheapest highlighted,
  with the resulting ranking printed as a title.
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
import numpy as np

rng = np.random.default_rng(7)

# ---------------------------------------------------------------------
# 1. Build a small synthetic outer network as a layered DAG
# ---------------------------------------------------------------------

positions = {}
edges = {}  # (u, v) -> (time_minutes, fare_dollars)


def add_edge(u, v, t_range, f_range):
    t = rng.uniform(*t_range)
    f = rng.uniform(*f_range)
    edges[(u, v)] = (round(t, 1), round(f, 2))


# CBD cluster (top-left triangle) and Milton cluster (top-right triangle)
positions["CBD0"] = (1.0, 10.0)
positions["CBD1"] = (2.0, 10.7)
positions["CBD2"] = (1.5, 9.3)
positions["MIL0"] = (7.0, 10.0)
positions["MIL1"] = (8.0, 10.7)
positions["MIL2"] = (7.5, 9.3)
origins = ["CBD0", "CBD1", "CBD2", "MIL0", "MIL1", "MIL2"]

# Outer network, two intermediate layers (general road/transit network)
layer1 = [f"O1_{i}" for i in range(4)]
layer2 = [f"O2_{i}" for i in range(4)]
for i, name in enumerate(layer1):
    positions[name] = (1.0 + 2.0 * i, 7.0)
for i, name in enumerate(layer2):
    positions[name] = (1.0 + 2.0 * i, 5.0)

# Boundary nodes = the stadium gates (candidate entry points to the venue)
boundary_nodes = [f"Gate{i+1}" for i in range(4)]
for i, name in enumerate(boundary_nodes):
    positions[name] = (1.0 + 2.0 * i, 3.0)

# Venue (shown for context; not part of the routing decision itself)
positions["SUNCORP"] = (4.0, 0.8)

# Wire the CBD and Milton clusters into the outer network
for o in ["CBD0", "CBD1", "CBD2"]:
    add_edge(o, "O1_0", (4, 12), (1.0, 4.0))
    add_edge(o, "O1_1", (4, 12), (1.0, 4.0))
for o in ["MIL0", "MIL1", "MIL2"]:
    add_edge(o, "O1_2", (4, 12), (1.0, 4.0))
    add_edge(o, "O1_3", (4, 12), (1.0, 4.0))

# Outer layer 1 -> layer 2 (each node feeds its neighbour too, for route choice)
for i, u in enumerate(layer1):
    add_edge(u, layer2[i], (5, 15), (1.0, 5.0))
    add_edge(u, layer2[(i + 1) % 4], (5, 15), (1.0, 5.0))

# Outer layer 2 -> gates
for i, u in enumerate(layer2):
    add_edge(u, boundary_nodes[i], (5, 15), (1.0, 5.0))
    add_edge(u, boundary_nodes[(i + 1) % 4], (5, 15), (1.0, 5.0))

# Gates -> stadium, shown as dashed context edges (not costed / not routed over)
context_edges = [(b, "SUNCORP") for b in boundary_nodes]

# Adjacency for the DP
out_edges = {}
for (u, v), w in edges.items():
    out_edges.setdefault(u, []).append((v, w))

# Topological order: origins, then layer1, then layer2, then gates
topo_order = origins + layer1 + layer2 + boundary_nodes
all_nodes = topo_order + ["WTO"]

# ---------------------------------------------------------------------
# 2. Multi-label (Pareto) shortest paths from a chosen source
# ---------------------------------------------------------------------
# Each label is (time, fare, predecessor_node, predecessor_label_index).


def dominates(a, b):
    """True if label a is at least as good as b on both objectives and
    strictly better on at least one (i.e. a dominates b)."""
    return a[0] <= b[0] and a[1] <= b[1] and (a[0] < b[0] or a[1] < b[1])


def pareto_filter(labels):
    keep = []
    for i, li in enumerate(labels):
        if not any(dominates(lj[:2], li[:2]) for j, lj in enumerate(labels) if j != i):
            keep.append(li)
    return keep


def compute_labels(source):
    labels = {n: [] for n in all_nodes}
    labels[source] = [(0.0, 0.0, None, None)]
    for u in topo_order:
        if u != source:
            labels[u] = pareto_filter(labels[u])
        for v, (dt, df) in out_edges.get(u, []):
            for idx, (t, f, _, _) in enumerate(labels[u]):
                labels[v].append((t + dt, f + df, u, idx))
    return labels


def backtrack(labels, node, idx):
    """Return the list of edges (u, v) on the path achieving labels[node][idx]."""
    path = []
    cur_node, cur_idx = node, idx
    while True:
        t, f, pred_node, pred_idx = labels[cur_node][cur_idx]
        if pred_node is None:
            break
        path.append((pred_node, cur_node))
        cur_node, cur_idx = pred_node, pred_idx
    path.reverse()
    return path


# Normalisation constants so the time/fare tradeoff is visually meaningful
# on a single 0-1 slider (rough scale of a full origin -> boundary journey).
TIME_SCALE = 60.0   # minutes
FARE_SCALE = 25.0   # dollars

# Precompute labels for every possible origin once (graph is tiny)
labels_by_source = {o: compute_labels(o) for o in origins}

# ---------------------------------------------------------------------
# 3. Figure and widgets
# ---------------------------------------------------------------------

fig = None
ax_net = None
ax_bar = None
slider = None
radio = None
selected_source = origins[0]
w_time_init = 0.5


def draw_network(ax, source, w_time):
    ax.clear()
    ax.set_title("Outer network to Suncorp Stadium (toy)", fontsize=11)
    ax.set_xlim(-0.5, 8.5)
    ax.set_ylim(0, 11.5)
    ax.axis("off")

    # base edges
    for (u, v) in edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        ax.plot([x1, x2], [y1, y2], color="lightgray", zorder=1, linewidth=1)

    # context edges to venue (dashed, uncosted)
    for (u, v) in context_edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        ax.plot([x1, x2], [y1, y2], color="lightgray", linestyle="--", zorder=1, linewidth=1)

    labels = labels_by_source[source]
    w_fare = 1.0 - w_time
    best_boundary, best_cost, best_idx = None, None, None
    for b in boundary_nodes:
        if not labels[b]:
            continue
        for idx, (t, f, _, _) in enumerate(labels[b]):
            cost = w_time * (t / TIME_SCALE) + w_fare * (f / FARE_SCALE)
            if best_cost is None or cost < best_cost:
                best_cost, best_boundary, best_idx = cost, b, idx

    # highlight recommended path
    if best_boundary is not None:
        path = backtrack(labels, best_boundary, best_idx)
        for (u, v) in path:
            x1, y1 = positions[u]
            x2, y2 = positions[v]
            ax.plot([x1, x2], [y1, y2], color="crimson", linewidth=2.5, zorder=2)

    # nodes
    for n, (x, y) in positions.items():
        if n == source:
            ax.scatter([x], [y], s=140, color="black", zorder=3)
            ax.annotate("attendee", (x, y), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=8)
        elif n == "SUNCORP":
            ax.scatter([x], [y], s=200, marker="s", color="navy", zorder=3)
            ax.annotate("Suncorp Stadium", (x, y), textcoords="offset points",
                        xytext=(0, -14), ha="center", fontsize=8)
        elif n in boundary_nodes:
            color = "crimson" if n == best_boundary else "steelblue"
            ax.scatter([x], [y], s=110, color=color, zorder=3)
            ax.annotate(n, (x, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8)
        elif n in origins:
            ax.scatter([x], [y], s=60, color="gray", zorder=3)
        else:
            ax.scatter([x], [y], s=40, color="lightsteelblue", zorder=3)

    return best_boundary


def draw_bar(ax, source, w_time):
    ax.clear()
    labels = labels_by_source[source]
    w_fare = 1.0 - w_time
    costs = {}
    for b in boundary_nodes:
        if labels[b]:
            costs[b] = min(
                w_time * (t / TIME_SCALE) + w_fare * (f / FARE_SCALE)
                for (t, f, _, _) in labels[b]
            )
    ranked = sorted(costs.items(), key=lambda kv: kv[1])
    names = [k for k, _ in ranked]
    values = [v for _, v in ranked]
    colors = ["crimson" if i == 0 else "steelblue" for i in range(len(names))]
    ax.bar(names, values, color=colors)
    ax.set_ylabel("scalarised cost  Ci(j) = w_time\u00b7t̂ + w_fare\u00b7f̂")
    ax.set_ylim(0, max(values) * 1.3 if values else 1)
    rank_str = " > ".join(names)
    ax.set_title(
        f"Attendee from {source}   |   w_time={w_time:.2f}, w_fare={w_fare:.2f}\n"
        f"gate ranking (best\u2192worst): {rank_str}",
        fontsize=10,
    )


def redraw():
    draw_network(ax_net, selected_source, slider.val)
    draw_bar(ax_bar, selected_source, slider.val)
    fig.canvas.draw_idle()


def build_figure():
    """Create the interactive figure and widgets, then show it. Only call
    this when running the script directly -- other scripts can import the
    network and routing functions above without triggering this."""
    global fig, ax_net, ax_bar, slider, radio, selected_source

    fig, (ax_net, ax_bar) = plt.subplots(1, 2, figsize=(13, 7))
    plt.subplots_adjust(bottom=0.22, wspace=0.3)

    ax_slider = plt.axes([0.15, 0.08, 0.7, 0.04])
    slider = Slider(ax_slider, "w_time", 0.0, 1.0, valinit=w_time_init)

    def on_slider(val):
        redraw()

    slider.on_changed(on_slider)

    ax_radio = plt.axes([0.02, 0.4, 0.10, 0.3])
    radio = RadioButtons(ax_radio, origins, active=0)

    def on_radio(label):
        global selected_source
        selected_source = label
        redraw()

    radio.on_clicked(on_radio)

    redraw()
    plt.show()


if __name__ == "__main__":
    build_figure()
