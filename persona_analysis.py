"""
Experiment: persona-based population
-----------------------------------------------------------------------
Every previous experiment drew each attendee's w_time uniformly at
random from [0,1] -- realistic in spread, but with no story behind the
numbers. This replaces that with three named personas, each centred on
a different time-vs-fare weighting with a little noise around it, and
asks two questions using the machinery already built:

  1. Do the three personas actually get routed to different gates
     under naive (congestion-ignoring) advice?
  2. Once a congestion penalty is introduced, do the three personas
     experience different amounts of regret and get redirected at
     different rates?

This reuses outer_routing_demo.py's network and Pareto labels, and the
same congestion-penalty mechanism as congestion_distortion_demo.py, so
the results are directly comparable to the earlier, unstructured
population.
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

import outer_routing_demo as base

rng = np.random.default_rng(2026)

# ---------------------------------------------------------------------
# 1. Persona-based population (instead of uniform random w_time)
# ---------------------------------------------------------------------
PERSONAS = {
    "Budget":       0.15,  # cares mostly about fare
    "Balanced":     0.50,
    "Time-pressed": 0.85,  # cares mostly about time
}
NOISE_STD = 0.06
N_PER_PERSONA = 100

pop_origin = []
pop_w_time = []
pop_persona = []

for persona, center in PERSONAS.items():
    for _ in range(N_PER_PERSONA):
        pop_origin.append(rng.choice(base.origins))
        w = np.clip(rng.normal(center, NOISE_STD), 0.0, 1.0)
        pop_w_time.append(w)
        pop_persona.append(persona)

pop_origin = np.array(pop_origin)
pop_w_time = np.array(pop_w_time)
pop_persona = np.array(pop_persona)
N_TRAVELLERS = len(pop_origin)


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

naive_choice_idx = naive_cost_table.argmin(axis=1)
naive_load = Counter(base.boundary_nodes[jx] for jx in naive_choice_idx)

# ---------------------------------------------------------------------
# 2. Apply a congestion penalty (same mechanism as congestion_distortion_demo.py)
# ---------------------------------------------------------------------
K_SEVERITY = 0.5

g = {b: K_SEVERITY * naive_load.get(b, 0) for b in base.boundary_nodes}
g_vec = np.array([g[b] for b in base.boundary_nodes])

aware_cost_table = naive_cost_table + pop_w_time[:, None] * (g_vec[None, :] / base.TIME_SCALE)
aware_choice_idx = aware_cost_table.argmin(axis=1)

rows = np.arange(N_TRAVELLERS)
cost_if_naive = aware_cost_table[rows, naive_choice_idx]
cost_if_aware = aware_cost_table[rows, aware_choice_idx]
D = np.abs(cost_if_naive - cost_if_aware)
redirected = naive_choice_idx != aware_choice_idx

# ---------------------------------------------------------------------
# 3. Figure: three panels, one story
# ---------------------------------------------------------------------
fig, (ax_gate, ax_regret, ax_redirect) = plt.subplots(1, 3, figsize=(15, 5.5))

# Panel 1: naive gate preference by persona
gate_names = base.boundary_nodes
x = np.arange(len(gate_names))
width = 0.25
for i, persona in enumerate(PERSONAS):
    mask = pop_persona == persona
    counts = [np.sum((naive_choice_idx == jx) & mask) for jx in range(len(gate_names))]
    ax_gate.bar(x + (i - 1) * width, counts, width, label=persona)
ax_gate.set_xticks(x)
ax_gate.set_xticklabels(gate_names)
ax_gate.set_ylabel("attendees choosing this gate (naive)")
ax_gate.set_title("Naive gate preference\nby persona", fontsize=10)
ax_gate.legend(fontsize=8)

# Panel 2: regret distribution by persona
regret_by_persona = [D[pop_persona == p] for p in PERSONAS]
ax_regret.boxplot(regret_by_persona, tick_labels=list(PERSONAS.keys()))
ax_regret.set_ylabel("regret D_i")
ax_regret.set_title(f"Regret of naive advice by persona\n(k={K_SEVERITY})", fontsize=10)

# Panel 3: fraction redirected by persona
redirect_frac = [np.mean(redirected[pop_persona == p]) * 100 for p in PERSONAS]
ax_redirect.bar(list(PERSONAS.keys()), redirect_frac, color=["steelblue", "darkorange", "crimson"])
ax_redirect.set_ylabel("% redirected once congestion-aware")
ax_redirect.set_title(f"Redirection rate by persona\n(k={K_SEVERITY})", fontsize=10)
ax_redirect.set_ylim(0, 100)

fig.suptitle("Suncorp Stadium \u2014 does persona (not just random weight) change the outcome?", fontsize=12)
fig.tight_layout()

if __name__ == "__main__":
    print(f"Population: {N_TRAVELLERS} attendees across {len(PERSONAS)} personas")
    for persona in PERSONAS:
        mask = pop_persona == persona
        print(f"  {persona}: mean regret={D[mask].mean():.3f}, "
              f"redirected={np.mean(redirected[mask])*100:.0f}%")
    plt.show()
