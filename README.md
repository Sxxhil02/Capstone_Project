# Preference-Sensitive Boundary Routing for Event Travel

## Overview
This project investigates whether outer-network routing advice for mass
events (concerts, sports matches at Suncorp Stadium, Brisbane) should account
for both individual preferences (time vs. fare) AND shared-network congestion.

**Answer:** Yes. Both matter, and they interact measurably.

## Methodology
- **Network:** Real Brisbane coordinates (Suncorp, Milton, CBD)
- **Modes:** Walk, Transit via Milton, Transit via CBD, Rideshare
- **Routing:** Multi-objective Pareto routing (time/fare trade-offs)
- **Congestion:** Mode-specific penalties, validated with live TransLink data
- **Population:** 300 synthetic attendees with realistic origins/preferences

## Quick Start

1. **Build the network:**
   ```bash
   python3 realistic_network_builder.py
   ```
   Output: real Brisbane network with actual coordinates and fares

2. **Interactive preference demo:**
   ```bash
   python3 realistic_routing_demo.py
   ```
   Drag slider to change time-vs-fare weight. Watch recommended mode flip.

3. **Interactive congestion demo:**
   ```bash
   python3 realistic_congestion_demo.py
   ```
   Drag slider to increase congestion severity. Watch load redistribute.

4. **Live TransLink integration:**
   ```bash
   python3 realistic_live_integration.py
   ```
   Fetches today's real service alerts. Shows how they change routing.

5. **Preference robustness (optional):**
   ```bash
   python3 rank_sensitivity_experiment.py
   ```
   Kendall's tau analysis: how stable are mode rankings under preference shifts?

6. **Persona-based analysis (optional):**
   ```bash
   python3 persona_analysis.py
   ```
   Named personas (Budget, Balanced, Time-pressed) show realistic diversity.

## Key Results

### Beat 1: Preferences Matter
- **Claim:** An attendee's time-vs-fare weight changes which mode is recommended
- **Evidence:** Interactive slider in realistic_routing_demo.py
- **Finding:** YES. Dragging from w_time=0 (fare-focused) to w_time=1
  (time-focused) changes the recommendation every time.

### Beat 2: Ignoring Congestion Costs Real Money
- **Claim:** Advice that ignores mode congestion is systematically wrong
- **Evidence:** Interactive slider in realistic_congestion_demo.py
- **Finding:** YES. At k=0.5 congestion severity, mean regret=0.614,
  and 100% of time-pressed attendees are redirected to less-congested modes.

### Beat 3: Stability Matters (Extended)
- **Claim:** Iterative congestion feedback must be properly damped
- **Evidence:** Comparison of undamped vs. MSA-damped iteration
- **Finding:** Undamped iteration oscillates forever. MSA damping converges.

## Data Sources

- **Network coordinates:** Real (Suncorp Stadium, Milton Station, CBD Brisbane)
- **Walking times:** Geodesic distance ÷ 5 km/h
- **Transit fares:** Real TransLink rates ($3.50 per trip)
- **Rideshare costs:** Real Brisbane Uber rates
- **Live alerts:** Real TransLink GTFS-Realtime public feed (no API key required)

## Files

| File | Purpose |
|------|---------|
| realistic_network_builder.py | Build the real Brisbane network |
| realistic_routing_demo.py | Interactive preference demo |
| realistic_congestion_demo.py | Interactive congestion demo |
| realistic_live_integration.py | Live TransLink data integration |
| rank_sensitivity_experiment.py | Preference robustness (Kendall's tau) |
| persona_analysis.py | Named personas (Budget/Balanced/Time-pressed) |

## References

[1] Hart, Nilsson, Raphael, "A formal basis for the heuristic determination
    of minimum cost paths," IEEE Trans. Syst. Sci. Cybern., vol. 4, 1968.

[2] Mandow & Pérez-de-la-Cruz, "A new approach to multiobjective A* search,"
    Proc. IJCAI, 2005.

[3] Peeta & Ziliaskopoulos, "Foundations of dynamic traffic assignment,"
    Netw. Spat. Econ., vol. 1, 2001.

## Author
Saahil Dharmaji, University of Queensland, DATA7901 Capstone Project

---

In particular, the congestion penalty is derived from the initial naive boundary-node load. It is therefore a **proxy for congestion near the venue**, rather than a complete inner-network traffic assignment.

This allows the effect of congestion on boundary-node selection and routing distortion to be investigated while keeping the model relatively simple.
