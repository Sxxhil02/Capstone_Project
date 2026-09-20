"""
Experiment: iterated congestion feedback loop (outer-inner coupling)
-----------------------------------------------------------------------
congestion_distortion_demo.py computes a congestion penalty g_j *once*
from the naive routing and stops there -- a "one-shot" correction. The
write-up's outer-inner iteration idea is stronger: route travellers,
observe the resulting load, update the congestion penalty from that
load, re-route, and repeat -- checking whether g_j settles down to a
fixed point, oscillates, or diverges.

This script implements exactly that loop on the same toy network, and
tests two ways of updating g_j between iterations:

  - "Constant alpha" damping:  g_new = (1-alpha)*g_old + alpha*g_raw
    A fixed blend of the old penalty and the freshly observed one.
    alpha=1 means no damping at all (pure naive iteration).

  - "MSA" (method of successive averages) damping:
    alpha_k = 1/(k+2), i.e. the step size shrinks over iterations.
    This is the classical fix used in the traffic assignment
    literature (Peeta & Ziliaskopoulos, 2001) for exactly this kind
    of oscillation problem, and is worth citing if this is discussed
    in the write-up.

Controls
--------
- Slider: congestion severity k_severity (same meaning as in
  congestion_distortion_demo.py).
- Slider: alpha (only used when "Constant alpha" is selected).
- Radio buttons: choose the damping scheme.
- Left panel: g_j trajectory per gate across iterations.
- Right panel: the largest change in g_j between successive
  iterations (log scale) -- this should trend to zero if and only if
  the loop is actually converging.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from collections import Counter

import outer_routing_demo as base

rng = np.random.default_rng(42)

N_TRAVELLERS = 300
N_ITERS = 25

pop_origin = rng.choice(base.origins, size=N_TRAVELLERS)
pop_w_time = rng.uniform(0.0, 1.0, size=N_TRAVELLERS)


def min_cost(source, j, w_time):
    w_fare = 1.0 - w_time
    labels = base.labels_by_source[source][j]
    return min(
        w_time * (t / base.TIME_SCALE) + w_fare * (f / base.FARE_SCALE)
        for (t, f, _, _) in labels
    )


naive_cost_table = np.zeros((N_TRAVELLERS, len(base.boundary_nodes)))
for i in range(N_TRAVELLERS):
    for jx, b in enumerate(base.boundary_nodes):
        naive_cost_table[i, jx] = min_cost(pop_origin[i], b, pop_w_time[i])


def run_iterated(k_severity, alpha, scheme, n_iters=N_ITERS):
    """Run the outer-inner feedback loop. scheme is 'constant' (use the
    given alpha every iteration) or 'msa' (alpha_k = 1/(k+2), ignoring
    the given alpha). Returns per-gate g trajectories and the max
    per-iteration change (for a convergence check)."""
    g = {b: 0.0 for b in base.boundary_nodes}
    g_history = {b: [0.0] for b in base.boundary_nodes}
    delta_norms = []

    for k in range(n_iters):
        g_vec = np.array([g[b] for b in base.boundary_nodes])
        aware_cost_table = naive_cost_table + pop_w_time[:, None] * (g_vec[None, :] / base.TIME_SCALE)
        choice_idx = aware_cost_table.argmin(axis=1)
        load = Counter(base.boundary_nodes[jx] for jx in choice_idx)

        g_raw = {b: k_severity * load.get(b, 0) for b in base.boundary_nodes}
        a = (1.0 / (k + 2)) if scheme == "msa" else alpha
        g_new = {b: (1 - a) * g[b] + a * g_raw[b] for b in base.boundary_nodes}

        delta = max(abs(g_new[b] - g[b]) for b in base.boundary_nodes)
        delta_norms.append(delta)
        g = g_new
        for b in base.boundary_nodes:
            g_history[b].append(g[b])

    return g_history, delta_norms


# ---------------------------------------------------------------------
# Figure and widgets
# ---------------------------------------------------------------------

fig, (ax_traj, ax_delta) = plt.subplots(1, 2, figsize=(13, 5.5))
plt.subplots_adjust(bottom=0.32, wspace=0.3)

K_INIT = 0.4
ALPHA_INIT = 1.0
SCHEME_INIT = "Constant \u03b1"


def redraw(k_severity, alpha, scheme_label):
    scheme = "msa" if scheme_label.startswith("MSA") else "constant"
    g_history, delta_norms = run_iterated(k_severity, alpha, scheme)

    ax_traj.clear()
    for b in base.boundary_nodes:
        ax_traj.plot(range(len(g_history[b])), g_history[b], marker=".", label=b)
    ax_traj.set_xlabel("iteration")
    ax_traj.set_ylabel("g_j (minutes)")
    ax_traj.set_title("Congestion penalty per gate\nacross iterations", fontsize=10)
    ax_traj.legend(fontsize=8)

    ax_delta.clear()
    ax_delta.plot(range(1, len(delta_norms) + 1), delta_norms, marker="o", color="darkred")
    ax_delta.set_yscale("log")
    ax_delta.set_xlabel("iteration")
    ax_delta.set_ylabel("max |g_new - g_old|  (log scale)")
    ax_delta.set_title("Convergence check\n(should trend to 0 if converging)", fontsize=10)

    scheme_note = "MSA: \u03b1_k = 1/(k+2)" if scheme == "msa" else f"constant \u03b1 = {alpha:.2f}"
    fig.suptitle(
        f"Suncorp Stadium \u2014 iterated congestion feedback  |  k_severity={k_severity:.2f}, {scheme_note}",
        fontsize=11,
    )
    fig.canvas.draw_idle()


ax_k = plt.axes([0.15, 0.16, 0.7, 0.03])
slider_k = Slider(ax_k, "k_severity", 0.0, 1.0, valinit=K_INIT)

ax_alpha = plt.axes([0.15, 0.10, 0.7, 0.03])
slider_alpha = Slider(ax_alpha, "\u03b1 (constant scheme)", 0.05, 1.0, valinit=ALPHA_INIT)

ax_radio = plt.axes([0.4, 0.005, 0.25, 0.08])
radio = RadioButtons(ax_radio, ["Constant \u03b1", "MSA (1/n)"], active=0)


def on_change(_):
    redraw(slider_k.val, slider_alpha.val, radio.value_selected)


slider_k.on_changed(on_change)
slider_alpha.on_changed(on_change)
radio.on_clicked(on_change)

if __name__ == "__main__":
    redraw(K_INIT, ALPHA_INIT, SCHEME_INIT)
    plt.show()
