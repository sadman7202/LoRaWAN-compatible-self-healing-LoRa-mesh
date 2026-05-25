# LoRaWAN-Compatible Self-Healing LoRa Mesh Network for Disaster Communication

## An Agentic AI-Driven Emergency Communication System for Flood-Prone Regions

---

## 📋 Project Overview

This repository contains the complete research framework for designing, simulating, and prototyping a **self-healing LoRa mesh network** integrated with **Agentic AI** for emergency communication during natural disasters (specifically floods) in regions where traditional mobile networks and electricity infrastructure fail.

### The Problem
In flood-prone haor regions of Bangladesh (and similar areas worldwide), when disasters strike:
- Mobile networks go down (tower power loss, infrastructure damage)
- Electricity is unavailable
- Roads are submerged, making physical rescue coordination nearly impossible
- Villages become isolated islands with no way to call for help

### The Solution
A pre-deployed, solar-powered, self-healing LoRa mesh network with intelligent (Agentic AI) routing that:
- Allows victims to send SOS signals via simple button-press devices
- Routes messages through multi-hop mesh relays to rescue command centers
- Automatically heals broken routes when relay nodes fail
- Uses mobile relays (boats/backpacks) to reach completely isolated areas
- Employs AI agents for priority classification, energy management, and rescue coordination

---

## 🏗️ Repository Structure

```
LoRaWAN-compatible-self-healing-LoRa-mesh/
│
├── README.md                          ← You are here
│
├── docs/                              ← Documentation & Guides
│   ├── GETTING_STARTED.md             ← Beginner's guide to the research project
│   ├── LITERATURE_REVIEW_GUIDE.md     ← How to conduct literature review
│   └── EVALUATION_GUIDE.md            ← How to evaluate and benchmark the system
│
├── paper/                             ← Research Paper Writing
│   ├── PAPER_TEMPLATE.md              ← Full paper template with writing instructions
│   └── WRITING_TIPS.md                ← Academic writing best practices
│
├── protocols/                         ← Protocol Specifications
│   ├── MESH_ROUTING_PROTOCOL.md       ← Self-healing routing protocol design
│   └── PACKET_FORMAT.md               ← Complete packet format specification
│
├── src/                               ← Source Code
│   ├── simulation/                    ← Python simulation code
│   │   ├── network_simulator.py       ← Main mesh network simulator
│   │   ├── routing_agent.py           ← AI routing agent implementation
│   │   ├── energy_model.py            ← Energy consumption model
│   │   └── mobile_relay.py            ← Mobile relay store-and-forward
│   │
│   └── firmware/                      ← Hardware firmware (ESP32)
│       ├── sos_node/                  ← SOS device firmware
│       │   └── sos_node.ino           ← Arduino sketch for SOS device
│       └── relay_node/                ← Relay node firmware
│           └── relay_node.ino         ← Arduino sketch for relay node
│
├── references/                        ← Reference Materials
│   └── KEY_PAPERS.md                  ← Annotated bibliography
│
├── figures/                           ← Diagrams and Figures
│
└── System Architecture *.md           ← Original system design document
```

---

## 🎯 Research Contributions

This research makes the following novel contributions:

1. **Hybrid Architecture**: First LoRa mesh + LoRaWAN gateway architecture specifically designed for disaster SOS with self-healing capability
2. **7-Agent Agentic AI Framework**: Distributed intelligence across edge nodes, relay nodes, and gateway
3. **Mobile Relay Store-and-Forward**: DTN-inspired boat/backpack relay for completely disconnected scenarios
4. **Predictive Pre-Positioning**: AI-driven pre-disaster resource deployment
5. **Incident Clustering**: Intelligent deduplication and priority assignment at gateway level

---

## 🧠 The 7 Agentic AI Components

| # | Agent | Location | Function |
|---|-------|----------|----------|
| 1 | Predictive Pre-Positioning | Gateway | Pre-disaster risk assessment & relay deployment |
| 2 | Priority Agent | SOS Node | Classifies emergency severity |
| 3 | Routing Agent | Relay Nodes | Selects optimal path (RSSI + battery + hops) |
| 4 | Self-Healing Agent | All Nodes | Detects failures, recalculates routes |
| 5 | Energy Agent | All Nodes | Adaptive duty cycling & power management |
| 6 | Mobile Relay Agent | Boat/Backpack | Prioritizes SOS collection order |
| 7 | Incident Coordination Agent | Gateway | Clusters, deduplicates, assigns rescue teams |

---

## 🛠️ Hardware Components

| Device Type | Quantity (Full) | Controller | Radio | Power |
|-------------|----------------|------------|-------|-------|
| SOS Device | 45–60 | ESP32/STM32 | SX1276/SX1262 | Battery + Solar |
| Local Mesh Relay | 12–18 | ESP32 | SX1276 | Solar (10-20W) + LiFePO4 |
| Backbone Relay | 6–8 | ESP32 | SX1276 | Solar + Battery |
| Boat Mobile Relay | 4–6 | ESP32 | SX1276 + GPS | Battery + Boat Power |
| Command Gateway | 2 | Raspberry Pi | LoRa Concentrator | Solar/IPS + Battery |

---

## 📊 Case Study Area

**Tanguar Haor, Tahirpur Upazila, Sunamganj District, Bangladesh**
- Area: ~100 sq km
- Coordinates: 25°01′–25°12′N, 91°02′–91°19′E
- Disaster type: Flash flood / Haor flood
- Primary failure mode: Mobile network + road access

---

## 🚀 Quick Start

### For Paper Writing
1. Start with [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for overall guidance
2. Read [`paper/PAPER_TEMPLATE.md`](paper/PAPER_TEMPLATE.md) for the paper structure
3. Follow [`paper/WRITING_TIPS.md`](paper/WRITING_TIPS.md) for academic writing advice
4. Use [`references/KEY_PAPERS.md`](references/KEY_PAPERS.md) for literature review

### For Protocol Design
1. Study [`protocols/MESH_ROUTING_PROTOCOL.md`](protocols/MESH_ROUTING_PROTOCOL.md)
2. Understand [`protocols/PACKET_FORMAT.md`](protocols/PACKET_FORMAT.md)

### For Simulation
1. Install Python 3.8+ and required packages
2. Run `python src/simulation/network_simulator.py`
3. Analyze results from the simulation output

### For Hardware Prototyping
1. Set up Arduino IDE with ESP32 board support
2. Install LoRa library (RadioLib or LoRa by Sandeep Mistry)
3. Flash `src/firmware/sos_node/sos_node.ino` to SOS device
4. Flash `src/firmware/relay_node/relay_node.ino` to relay node

---

## 📈 Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Packet Delivery Ratio (PDR) | % of SOS reaching gateway | > 95% |
| End-to-End Latency | SOS press → Gateway receipt | < 5 minutes |
| Route Recovery Time | Self-healing after relay failure | < 30 seconds |
| Energy Efficiency | Node lifetime under disaster mode | > 72 hours |
| Mobile Relay Effectiveness | % messages recovered from isolated nodes | > 80% |

---

## 📝 Target Publication Venues

- IEEE Internet of Things Journal
- IEEE Access
- Computer Networks (Elsevier)
- Ad Hoc Networks (Elsevier)
- IEEE ICC / GLOBECOM
- ACM MobiCom workshops
- ISCRAM (Information Systems for Crisis Response and Management)

---

## 🔧 Tools & Technologies

| Category | Tools |
|----------|-------|
| Simulation | Python, NS-3, OMNeT++ (FLoRa) |
| TinyML | TensorFlow Lite Micro, Edge Impulse |
| Firmware | Arduino IDE, ESP-IDF, PlatformIO |
| Hardware | ESP32, SX1276/SX1262, Raspberry Pi |
| GIS/Mapping | QGIS, OpenStreetMap |
| Paper Writing | LaTeX (Overleaf), IEEE template |
| Version Control | Git, GitHub |
| Diagrams | draw.io, Lucidchart, PlantUML |

---

## 📅 Suggested Research Timeline

| Week | Activity |
|------|----------|
| 1-2 | Literature review & related work study |
| 3-4 | Protocol design & specification writing |
| 5-8 | Simulation development & testing |
| 9-10 | Hardware prototype (if applicable) |
| 11-12 | Results analysis & comparison |
| 13-14 | Paper writing & revision |
| 15-16 | Submission & peer review response |

---

## 📄 License

This research project is open-source for academic purposes. Please cite this work if you use any part of it in your research.

---

## 👥 Contributing

This is a research project. Contributions in the form of:
- Protocol improvements
- Simulation enhancements
- Hardware test results
- Literature references

are welcome via Pull Requests.
