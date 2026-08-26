# Preference-Sensitive Boundary Routing for Event Travel

## Project Overview

This project investigates routing decisions for travellers attending large events, with a focus on **boundary-node selection, traveller preferences, congestion, and routing distortion**.

The project compares two approaches to routing:

* **Congestion-naive routing** – travellers select a boundary node based primarily on their individual travel preferences, such as travel time and fare.
* **Congestion-aware routing** – routing decisions additionally account for congestion caused by multiple travellers converging on the same boundary node.

The aim is to investigate how ignoring congestion can affect routing recommendations and traveller outcomes.

---

## Project Structure

The repository contains four Python scripts:

### `outer_routing_demo.py`

This script provides the base outer-routing model used by the congestion analysis. It contains the network, boundary nodes, Pareto-optimal routing labels, and the time/fare scales used by the other routing scripts.

### `congestion_distortion_demo.py`

This script extends the outer-routing model to compare congestion-naive and congestion-aware routing.

It:

1. Generates a synthetic population of travellers.
2. Calculates each traveller's preferred boundary node using individual time/fare preferences.
3. Calculates the resulting traveller load at each boundary node.
4. Converts the boundary-node load into a congestion penalty.
5. Re-routes travellers using congestion-aware costs.
6. Measures the distortion/regret associated with following the congestion-naive recommendation.
7. Visualises the difference between naive and congestion-aware routing.

### `suncorp_outer_routing_demo.py`

This script contains the Suncorp-specific version of the outer-routing analysis.

### `suncorp_congestion_distortion.py`

This script contains the Suncorp-specific congestion and routing-distortion analysis.

---

## Methodology

### Traveller Population

The congestion analysis uses a synthetic population of **300 travellers**.

Each traveller is assigned:

* An origin selected from the available origins.
* A randomly generated time preference between 0 and 1.

The time preference is combined with a corresponding fare preference:

```text
fare weight = 1 - time weight
```

This allows different travellers to place different importance on travel time versus fare.

---

## Individual Routing Cost

For each traveller and boundary node, the model calculates a scalarised routing cost using the traveller's time and fare preferences.

The cost is based on:

```text
Cost = time preference × normalised travel time
     + fare preference × normalised fare
```

The cheapest available Pareto-optimal route is selected for each traveller and boundary node.

---

## Congestion-Naive Routing

In the initial routing stage, congestion is ignored.

Each traveller independently selects the boundary node with the lowest individualised routing cost.

The number of travellers selecting each boundary node is then calculated to obtain the **naive load**.

---

## Congestion-Aware Routing

The naive load is used to construct a simple congestion penalty for each boundary node.

The congestion penalty is represented as:

```text
g_j = k × naive_load_j
```

where:

* `g_j` is the congestion penalty for boundary node `j`
* `k` is the congestion severity
* `naive_load_j` is the number of travellers initially selecting boundary node `j`

The congestion-aware routing cost then incorporates this additional penalty.

This provides a simplified representation of congestion near the event venue rather than a full inner-network traffic assignment.

---

## Routing Distortion / Regret

The model compares the cost of following the congestion-naive recommendation with the cost of following the congestion-aware recommendation.

For each traveller, the distortion is calculated as:

```text
D_i = | C_aware(j_naive) - C_aware(j_aware) |
```

This measures the regret associated with selecting the naive recommendation when the actual routing environment includes congestion.

The model also calculates the proportion of travellers whose recommended boundary node changes after congestion is considered.

---

## Visualisations

`congestion_distortion_demo.py` produces three visualisations:

### 1. Congestion Penalty

Shows the congestion penalty associated with each boundary node.

### 2. Traveller Load

Compares the number of travellers assigned to each boundary node under:

* Naive routing
* Congestion-aware routing

### 3. Routing Regret Distribution

Shows the distribution of traveller-level regret/distortion.

The plot also reports:

* Mean regret
* Percentage of travellers redirected by the congestion-aware model

---

## Interactive Congestion Analysis

The congestion analysis includes an interactive slider controlling the congestion severity parameter `k`.

The parameter ranges from:

```text
k = 0.0 to 1.0
```

When:

```text
k = 0
```

there is no congestion penalty, so congestion-aware routing becomes equivalent to naive routing.

Increasing `k` increases the congestion penalty associated with heavily used boundary nodes and can cause travellers to redistribute across alternative boundary nodes.

---

## Requirements

The Python scripts use the following main libraries:

* Python 3
* NumPy
* Matplotlib

The congestion distortion model also uses:

* `matplotlib.widgets.Slider`
* Python's built-in `collections.Counter`

---

## How to Run

Clone or download this repository and open a terminal in the project directory.

The congestion distortion demonstration can be run using:

```bash
python congestion_distortion_demo.py
```

The script imports `outer_routing_demo.py`, so both files should remain in the same project directory.

The Suncorp-specific scripts can similarly be run from the repository directory:

```bash
python suncorp_outer_routing_demo.py
python suncorp_congestion_distortion.py
```

If your system uses `python3` instead of `python`, use:

```bash
python3 congestion_distortion_demo.py
```

---

## Repository Structure

```text
Capstone_Project/
│
├── README.md
├── congestion_distortion_demo.py
├── outer_routing_demo.py
├── suncorp_congestion_distortion.py
└── suncorp_outer_routing_demo.py
```

---

## Current Scope and Limitations

The congestion model provides a simplified representation of congestion.

In particular, the congestion penalty is derived from the initial naive boundary-node load. It is therefore a **proxy for congestion near the venue**, rather than a complete inner-network traffic assignment.

This allows the effect of congestion on boundary-node selection and routing distortion to be investigated while keeping the model relatively simple.
