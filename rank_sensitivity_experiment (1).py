"""
Experiment: preference-perturbation rank sensitivity (Kendall's tau)
-----------------------------------------------------------------------
This turns the promise in the write-up --

    "the experiment measures how Rank(i) changes as wi is perturbed
    -- using a rank-correlation metric (e.g. Kendall's tau) between
    the ranking at wi and at wi + delta"

-- into an actual result, instead of a single slider demo for one
traveller. It reuses the network and Pareto labels from
outer_routing_demo.py.

Method
------
1. Sample a population of attendees (random origin + random w_time).
2. For each attendee, compute Rank(i, w_time) and Rank(i, w_time + delta)
   -- the ranking of gates by scalarised cost, before and after a small
   nudge to their preference weight. w_time is clipped to stay in [0,1].
3. Compare the two rankings with Kendall's tau (1.0 = identical order,
   -1.0 = fully reversed, 0 = no relationship).
4. Report how tau is distributed across the population, and how the
   average tau falls off as delta grows -- i.e. how much a preference
   has to shift before the recommended ranking meaningfully changes.

This is a static, non-interactive experiment (unlike the two slider
demos) since the point here is a distribution of results across a
population, not a single case to explore live.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kendalltau

import outer_routing_demo as base

rng = np.random.default_rng(123)

N_TRAVELLERS = 500
pop_origin = rng.choice(base.origins, size=N_TRAVELLERS)
pop_w_time = rng.uniform(0.0, 1.0, size=N_TRAVELLERS)


def ranking(source, w_time):
    """Return boundary (gate) names ordered cheapest-to-most-expensive
    under this weight, using the precomputed Pareto label sets."""
    w_fare = 1.0 - w_time
    costs = {}
    for b in base.boundary_nodes:
        labels = base.labels_by_source[source][b]
        costs[b] = min(
            w_time * (t / base.TIME_SCALE) + w_fare * (f / base.FARE_SCALE)
            for (t, f, _, _) in labels
        )
    return sorted(costs, key=costs.get)


def tau_for_delta(delta):
    """Kendall's tau between Rank(i, w) and Rank(i, w+delta) for every
    traveller in the population, at a fixed perturbation size delta."""
    taus = np.empty(N_TRAVELLERS)
    for i in range(N_TRAVELLERS):
        w = pop_w_time[i]
        w_perturbed = np.clip(w + delta, 0.0, 1.0)
        r1 = ranking(pop_origin[i], w)
        r2 = ranking(pop_origin[i], w_perturbed)
        # Kendall's tau needs numeric rank vectors: rank of each gate
        # under r1, looked up in the order given by r2.
        rank1 = {name: idx for idx, name in enumerate(r1)}
        rank2 = {name: idx for idx, name in enumerate(r2)}
        common = base.boundary_nodes
        x = [rank1[g] for g in common]
        y = [rank2[g] for g in common]
        tau, _ = kendalltau(x, y)
        taus[i] = tau if not np.isnan(tau) else 1.0  # constant ranking -> perfect agreement
    return taus


# ---------------------------------------------------------------------
# Result 1: distribution of tau at one representative perturbation size
# ---------------------------------------------------------------------
DELTA_SHOWCASE = 0.15
taus_showcase = tau_for_delta(DELTA_SHOWCASE)

# ---------------------------------------------------------------------
# Result 2: mean tau as a function of perturbation size
# ---------------------------------------------------------------------
deltas = np.linspace(0.02, 0.5, 15)
mean_taus = [tau_for_delta(d).mean() for d in deltas]
frac_unchanged = [
    np.mean(tau_for_delta(d) == 1.0) for d in deltas
]  # fraction of travellers whose ranking didn't move at all

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.hist(taus_showcase, bins=20, color="slategray")
ax1.axvline(taus_showcase.mean(), color="crimson", linestyle="--", linewidth=1.5)
ax1.set_title(
    f"Rank stability at \u03b4={DELTA_SHOWCASE}\n"
    f"mean \u03c4={taus_showcase.mean():.3f}  |  N={N_TRAVELLERS} attendees",
    fontsize=10,
)
ax1.set_xlabel("Kendall's \u03c4 (Rank(w) vs Rank(w+\u03b4))")
ax1.set_ylabel("number of attendees")

ax2.plot(deltas, mean_taus, marker="o", color="steelblue", label="mean Kendall's \u03c4")
ax2.plot(deltas, frac_unchanged, marker="s", color="darkorange", label="fraction with unchanged ranking")
ax2.set_xlabel("perturbation size \u03b4 (change in w_time)")
ax2.set_ylabel("value")
ax2.set_ylim(-0.05, 1.05)
ax2.set_title("Ranking stability vs. perturbation size", fontsize=10)
ax2.legend(fontsize=8)
ax2.axhline(0, color="gray", linewidth=0.8)

fig.suptitle("How much does a small preference change move the gate ranking?", fontsize=12)
fig.tight_layout()

if __name__ == "__main__":
    print(f"At delta={DELTA_SHOWCASE}: mean tau = {taus_showcase.mean():.3f}, "
          f"{np.mean(taus_showcase == 1.0)*100:.0f}% of attendees had an unchanged ranking")
    plt.show()
