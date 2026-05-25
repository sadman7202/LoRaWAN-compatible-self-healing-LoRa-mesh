# Getting Started — A Beginner's Guide

## Welcome to the SHLM Research Project!

This guide will walk you through everything you need to understand, develop, and write a research paper on the **Self-Healing LoRa Mesh (SHLM)** network for disaster communication.

---

## Step 1: Understand the Problem (Week 1)

### What You Should Know First
Before diving into the technical work, understand the real-world problem:

1. **Bangladesh floods**: Bangladesh experiences severe flooding annually, particularly in haor (wetland) regions. During floods, mobile towers lose power, roads are submerged, and villages become isolated.

2. **Communication gap**: When people are trapped, they have NO way to call for help. No mobile network, no internet, no landline.

3. **Our solution**: Pre-deploy a mesh of small, solar-powered LoRa radio devices that can relay SOS messages even when everything else fails.

### Key Concepts to Learn
- **LoRa** (Long Range): A radio modulation technique for IoT. Range: 2-15 km. Low power. No license needed.
- **LoRaWAN**: A network protocol built on LoRa. Gateway-centric (star topology).
- **Mesh Network**: Every node can relay messages for others (multi-hop).
- **Self-Healing**: If a node dies, the network automatically finds another path.
- **Agentic AI**: AI agents that make autonomous decisions (route selection, priority, energy management).

### Recommended First Reads
1. Read the `System Architecture *.md` file in this repo (the original design document)
2. Read `protocols/MESH_ROUTING_PROTOCOL.md` for the full protocol
3. Watch YouTube videos on "LoRa explained" and "mesh networking basics"

---

## Step 2: Set Up Your Environment (Week 1-2)

### For Simulation (Python)
```bash
# Install Python 3.8+
python --version  # Should be 3.8 or higher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install numpy matplotlib

# Run the simulator
cd src/simulation
python network_simulator.py --nodes 50 --failure-rate 0.2 --duration 7200
```

### For Hardware Prototyping (Optional)
```
1. Install Arduino IDE (https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - File → Preferences → Additional Boards Manager URLs
   - Add: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
3. Install libraries:
   - RadioLib (by Jan Gromes)
   - ArduinoJson (by Benoit Blanchon)
4. Select board: "TTGO LoRa32-OLED" or "ESP32 Dev Module"
```

### For Paper Writing
```
1. Create account on Overleaf (https://www.overleaf.com) — FREE
2. Start new project → IEEE Journal template
3. Or use Word with IEEE template from: 
   https://template-selector.ieee.org/
```

---

## Step 3: Understand the Architecture (Week 2)

### The Big Picture
```
Victims → SOS Device → Local Relay → Backbone Relay → Gateway → Rescue Team
                                          ↑
                            Mobile Relay (boat) fills gaps
```

### Study These Files in Order
1. `protocols/MESH_ROUTING_PROTOCOL.md` — How routing works
2. `protocols/PACKET_FORMAT.md` — What the bytes look like
3. `src/simulation/routing_agent.py` — The AI brain
4. `src/simulation/energy_model.py` — Power management
5. `src/simulation/mobile_relay.py` — Last-resort connectivity
6. `src/firmware/sos_node/sos_node.ino` — What the hardware does
7. `src/firmware/relay_node/relay_node.ino` — How relays work

---

## Step 4: Run Simulations (Week 3-6)

### Basic Simulation
```bash
cd src/simulation
python network_simulator.py
```

### Experiment with Parameters
```bash
# Test different failure rates
python network_simulator.py --failure-rate 0.0 --output results_0pct.json
python network_simulator.py --failure-rate 0.1 --output results_10pct.json
python network_simulator.py --failure-rate 0.2 --output results_20pct.json
python network_simulator.py --failure-rate 0.3 --output results_30pct.json
python network_simulator.py --failure-rate 0.5 --output results_50pct.json

# Test different network sizes
python network_simulator.py --nodes 20 --output results_20nodes.json
python network_simulator.py --nodes 50 --output results_50nodes.json
python network_simulator.py --nodes 80 --output results_80nodes.json
```

### Compare Routing Strategies
Edit `routing_agent.py` to switch between:
- `RoutingStrategy.AI_MULTICRITERIA` (our proposed)
- `RoutingStrategy.SHORTEST_PATH` (baseline)
- `RoutingStrategy.FLOODING` (baseline)
- `RoutingStrategy.AODV_BASIC` (baseline)

Run each and collect results for comparison tables.

### What Results You Need
For your paper, you need these graphs/tables:
- [ ] PDR vs. Failure Rate (comparing 4 strategies)
- [ ] Average Latency vs. Failure Rate
- [ ] Route Recovery Time distribution
- [ ] Battery Lifetime comparison
- [ ] Mobile Relay collection effectiveness

---

## Step 5: Write the Paper (Week 7-14)

### Writing Order (DO NOT write linearly!)
```
1. System Architecture section (you know this best)
2. Evaluation Methodology (describe what you simulated)
3. Results (present your graphs and tables)
4. Related Work (you've read the papers by now)
5. Introduction (now you know what to introduce)
6. Conclusion (summarize findings)
7. Abstract (write this LAST — it's a summary of everything)
```

### Resources
- `paper/PAPER_TEMPLATE.md` — Section-by-section guide
- `paper/WRITING_TIPS.md` — Academic writing rules
- `docs/LITERATURE_REVIEW_GUIDE.md` — How to find and cite papers
- `docs/EVALUATION_GUIDE.md` — How to present results
- `references/KEY_PAPERS.md` — Papers you should read and cite

---

## Step 6: Revise and Submit (Week 15-16)

1. Have your advisor/colleague read the paper
2. Check against the template checklist
3. Ensure all figures are high quality (300 DPI)
4. Verify reference format matches venue requirements
5. Submit via the journal/conference portal

---

## Common Questions

### Q: Do I need actual hardware to write this paper?
**A:** No. You can write a solid simulation-based paper. Many top venues accept simulation-only research, especially for novel protocol designs. If you DO have hardware, that strengthens the paper significantly.

### Q: How long should the paper be?
**A:** 
- IEEE Journal: 10-14 pages (double column)
- IEEE Conference: 6-8 pages
- Workshop paper: 4-6 pages

### Q: What programming skills do I need?
**A:** 
- Python (intermediate) — for simulation
- C/C++ (basic) — for firmware understanding
- LaTeX (basic) — for paper writing (or use Word)

### Q: Can I modify the protocol?
**A:** Absolutely! This is YOUR research. The protocol in this repo is a starting point. You might improve it by:
- Adding security features
- Optimizing the route score weights
- Implementing a different failure detection algorithm
- Adding machine learning for the routing agent

### Q: What if my simulation results don't look good?
**A:** Research is about honest findings. If a certain approach doesn't work well, that's a valid finding too. Discuss WHY it fails and suggest improvements. Honesty in results builds credibility.

---

## Troubleshooting

### Simulation won't run
```
Error: ModuleNotFoundError: No module named 'routing_agent'
Fix: Make sure you're running from the src/simulation/ directory
```

### Firmware won't compile
```
Error: RadioLib.h: No such file or directory
Fix: Install RadioLib library in Arduino IDE (Sketch → Include Library → Manage Libraries → search "RadioLib")
```

### Results seem unrealistic
- Check that node positions make sense (within range of each other)
- Verify that path loss model parameters match your scenario
- Ensure simulation runs long enough to be statistically meaningful
- Use multiple random seeds and average the results

---

## Need Help?

1. Re-read the relevant documentation file
2. Check if the issue is addressed in this guide
3. Look at the demo/test sections in each Python module (run with `python module_name.py`)
4. Search Google Scholar for related concepts
5. Ask your research supervisor

Good luck with your research! 🎓
