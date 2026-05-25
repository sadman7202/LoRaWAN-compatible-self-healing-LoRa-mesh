# Evaluation Guide

## How to Evaluate and Benchmark the SHLM System

---

## 1. Evaluation Philosophy

### What Makes a Good Evaluation?
A strong evaluation section must be:
- **Reproducible**: Another researcher can repeat your experiment
- **Fair**: All approaches compared under identical conditions
- **Comprehensive**: Multiple metrics, multiple scenarios
- **Honest**: Report failures and limitations too

### What Reviewers Look For
- Clear definition of metrics (mathematical formulas)
- Multiple baselines (at least 2-3 comparison approaches)
- Statistical significance (multiple runs, confidence intervals)
- Sensitivity analysis (how do results change with parameters?)
- Realistic scenarios (based on real-world conditions)

---

## 2. Metrics Definitions

### 2.1 Packet Delivery Ratio (PDR)
The most important metric — what percentage of SOS messages reach the gateway.

```
PDR = (Number of SOS delivered to gateway) / (Total SOS generated) × 100%

Target: > 95% under normal conditions
        > 80% under 50% relay failure
```

### 2.2 End-to-End Latency
Time from SOS button press to gateway receipt.

```
Latency(msg_i) = time_gateway_receipt(msg_i) - time_sos_press(msg_i)

Report: Average, Median (P50), P95, P99, Maximum
Target: Average < 5 minutes for disaster scenarios
```

### 2.3 Route Recovery Time
Time for the network to heal after a relay failure.

```
Recovery_Time = time_new_route_active - time_failure_detected

Report: Average, Standard Deviation, Maximum
Target: < 30 seconds average
```

### 2.4 Energy Efficiency
How long nodes survive compared to baselines.

```
Energy_Efficiency = Lifetime_proposed / Lifetime_baseline

Or simply report: Operational hours until battery < 10%
Target: > 72 hours for relay nodes in disaster mode
```

### 2.5 Mobile Relay Recovery Rate
Percentage of isolated messages recovered by mobile relays.

```
Mobile_Recovery = (Isolated messages delivered via mobile relay) / 
                  (Total messages stored by isolated nodes) × 100%

Target: > 80%
```

### 2.6 Scalability
How PDR and latency change as network size increases.

```
Measure PDR and Latency at: 20, 30, 40, 50, 60, 70, 80 nodes
Plot: PDR vs. Node Count, Latency vs. Node Count
```

---

## 3. Simulation Setup

### 3.1 Run Parameters
```python
# Standard experiment parameters
SIMULATION_DURATION = 7200  # seconds (2 hours of disaster)
NUM_RUNS = 10  # Minimum runs per configuration for statistical validity
RANDOM_SEEDS = [42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021]
```

### 3.2 Scenarios to Test

| Scenario | Failure Rate | Mobile Relays | Mode | Purpose |
|----------|-------------|---------------|------|---------|
| S1: Normal | 0% | 0 | Normal | Baseline performance |
| S2: Mild | 10% | 0 | Disaster | Small disruption |
| S3: Moderate | 20% | 0 | Disaster | Typical disaster |
| S4: Severe | 30% | 0 | Disaster | Major disruption |
| S5: Critical | 50% | 0 | Disaster | Worst case |
| S6: With Mobile | 30% | 2 | Disaster | Mobile relay benefit |
| S7: Full System | 30% | 2 | Disaster | Complete proposed system |

### 3.3 Baselines to Compare

| Approach | Description | Implementation |
|----------|-------------|----------------|
| B1: Static LoRaWAN | Single-hop to gateway only, no mesh | Remove all relay forwarding |
| B2: Flooding | Broadcast every message to all neighbors | Use FloodingRouter class |
| B3: AODV Basic | Standard hop-count routing, no energy awareness | Use AODVRouter class |
| B4: Proposed (No AI) | Multi-hop but random next-hop selection | Random from active neighbors |
| B5: Proposed (Full) | Complete SHLM with all 7 agents | Full RoutingAgent with weights |

---

## 4. How to Run Experiments

### 4.1 Batch Experiment Script
```python
"""Run all experiments and collect results."""
import json
import os

# Import the simulator
from network_simulator import NetworkSimulator, SimConfig

SEEDS = [42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021]
FAILURE_RATES = [0.0, 0.1, 0.2, 0.3, 0.5]
OUTPUT_DIR = "results/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

all_results = []

for failure_rate in FAILURE_RATES:
    for seed in SEEDS:
        config = SimConfig(
            num_sos_nodes=50,
            failure_rate=failure_rate,
            simulation_duration=7200,
            seed=seed,
        )
        sim = NetworkSimulator(config)
        sim.run()
        result = sim.get_results_dict()
        result['seed'] = seed
        all_results.append(result)
        
        filename = f"results_fr{int(failure_rate*100)}_seed{seed}.json"
        with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
            json.dump(result, f, indent=2)

# Save combined results
with open(os.path.join(OUTPUT_DIR, "all_results.json"), 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"Completed {len(all_results)} experiments.")
```

### 4.2 Results Analysis Script
```python
"""Analyze and plot results."""
import json
import numpy as np

# Load results
with open("results/all_results.json") as f:
    results = json.load(f)

# Group by failure rate
from collections import defaultdict
grouped = defaultdict(list)
for r in results:
    grouped[r['failure_rate']].append(r)

# Print summary table
print(f"{'Failure%':<10} {'PDR Mean':<10} {'PDR Std':<10} "
      f"{'Latency':<10} {'Recovery':<10}")
print("-" * 50)
for fr in sorted(grouped.keys()):
    pdrs = [r['pdr_percent'] for r in grouped[fr]]
    lats = [r['avg_latency_s'] for r in grouped[fr]]
    recs = [r['avg_recovery_time_s'] for r in grouped[fr]]
    print(f"{fr*100:<10.0f} {np.mean(pdrs):<10.1f} {np.std(pdrs):<10.1f} "
          f"{np.mean(lats):<10.2f} {np.mean(recs):<10.2f}")
```

---

## 5. Presenting Results

### 5.1 Essential Figures

**Figure: PDR vs. Failure Rate**
- X-axis: Failure Rate (0%, 10%, 20%, 30%, 50%)
- Y-axis: Packet Delivery Ratio (%)
- Lines: One per approach (4-5 lines)
- Include error bars (standard deviation)

**Figure: Latency CDF**
- X-axis: Latency (seconds)
- Y-axis: Cumulative Probability
- Lines: One per approach
- Shows P50, P95, P99 visually

**Figure: Energy Over Time**
- X-axis: Time (hours, 0-72)
- Y-axis: Average Battery (%)
- Lines: Different routing strategies
- Shows when each approach "dies"

**Figure: Recovery Time Boxplot**
- X-axis: Failure Rate
- Y-axis: Recovery Time (seconds)
- Box-and-whisker for each scenario

### 5.2 Python Plotting Code (matplotlib)
```python
import matplotlib.pyplot as plt
import numpy as np

# Example: PDR vs Failure Rate
failure_rates = [0, 10, 20, 30, 50]
pdr_proposed = [97.2, 95.1, 93.4, 88.7, 82.1]  # Your results
pdr_aodv = [94.0, 87.3, 79.2, 68.5, 54.2]
pdr_flooding = [92.1, 82.5, 71.0, 58.3, 42.1]
pdr_lorawan = [78.0, 52.0, 31.0, 18.0, 8.0]

plt.figure(figsize=(8, 5))
plt.plot(failure_rates, pdr_proposed, 'bo-', label='Proposed (SHLM)', linewidth=2)
plt.plot(failure_rates, pdr_aodv, 'gs--', label='AODV Mesh')
plt.plot(failure_rates, pdr_flooding, 'r^-.', label='Flooding')
plt.plot(failure_rates, pdr_lorawan, 'kd:', label='Static LoRaWAN')

plt.xlabel('Relay Failure Rate (%)', fontsize=12)
plt.ylabel('Packet Delivery Ratio (%)', fontsize=12)
plt.title('PDR Performance Under Various Failure Conditions')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig('figures/pdr_vs_failure.pdf', dpi=300)
plt.show()
```

### 5.3 Results Table Format
```
Table I: Performance Comparison Under Various Failure Rates

| Metric          | Failure | LoRaWAN | Flooding | AODV  | Proposed |
|-----------------|---------|---------|----------|-------|----------|
| PDR (%)         | 0%      | 78.0    | 92.1     | 94.0  | **97.2** |
| PDR (%)         | 20%     | 31.0    | 71.0     | 79.2  | **93.4** |
| PDR (%)         | 50%     | 8.0     | 42.1     | 54.2  | **82.1** |
| Latency (s)     | 20%     | 2.1     | 8.7      | 5.4   | **4.2**  |
| Recovery (s)    | 20%     | N/A     | N/A      | 45.3  | **28.1** |
| Battery Life(h) | -       | 168     | 48       | 96    | **129**  |

Bold = best result in each row
```

---

## 6. Statistical Rigor

### 6.1 Multiple Runs
- Run EACH configuration at least 10 times with different random seeds
- Report mean ± standard deviation
- Consider confidence intervals (95% CI)

### 6.2 Statistical Tests (Optional but Strong)
- **t-test**: Compare means of two approaches
- **ANOVA**: Compare means of 3+ approaches
- **Mann-Whitney U**: If data is not normally distributed

### 6.3 Reporting Format
```
"The proposed SHLM approach achieves a mean PDR of 93.4% ± 2.1% 
under 20% relay failure, compared to 79.2% ± 3.5% for AODV-based 
routing (p < 0.01, paired t-test), representing a 17.9% relative 
improvement."
```

---

## 7. Checklist Before Finalizing Results

- [ ] Each experiment ran at least 10 times (different seeds)
- [ ] All approaches used identical simulation conditions
- [ ] Standard deviation or confidence intervals reported
- [ ] Figures have clear axis labels, legends, and captions
- [ ] Tables highlight the best result in each category
- [ ] Results section explains WHY differences occur (not just WHAT)
- [ ] Limitations are acknowledged honestly
- [ ] All claimed improvements are backed by specific numbers
