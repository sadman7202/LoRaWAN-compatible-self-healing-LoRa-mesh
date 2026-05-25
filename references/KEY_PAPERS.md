# Key Papers — Annotated Bibliography

## Essential References for This Research

Below are 35+ key papers organized by category. For each paper, we provide:
- Citation info
- Brief summary (what they did)
- Relevance to our work
- Why to cite it

---

## Category 1: LoRa/LoRaWAN Fundamentals

### [1] Semtech, "LoRa Modulation Basics," AN1200.22, 2015
- **Summary**: Official Semtech application note explaining CSS modulation
- **Relevance**: Foundational reference for LoRa physical layer
- **Cite when**: Describing LoRa modulation in background section

### [2] LoRa Alliance, "LoRaWAN Specification v1.0.4," 2022
- **Summary**: Official protocol specification for LoRaWAN
- **Relevance**: Our system is "LoRaWAN-compatible" at the gateway layer
- **Cite when**: Explaining why standard LoRaWAN is insufficient (star topology)

### [3] Augustin et al., "A Study of LoRa: Long Range & Low Power Networks for IoT," Sensors, 2016
- **Summary**: Comprehensive LoRa performance characterization
- **Relevance**: Reference for LoRa range, SF trade-offs, and power
- **Cite when**: Justifying LoRa choice for disaster communication

### [4] Cattani et al., "Experimental Evaluation of LoRa Reliability," JSAN, 2017
- **Summary**: Real-world LoRa reliability measurements
- **Relevance**: Empirical data for packet delivery rates at various distances
- **Cite when**: Validating simulation path loss model assumptions

### [5] Bor et al., "Do LoRa Low-Power Wide-Area Networks Scale?" MSWiM, 2016
- **Summary**: Scalability analysis showing LoRaWAN limitations with many devices
- **Relevance**: Justifies need for mesh (standard LoRaWAN doesn't scale)
- **Cite when**: Motivating mesh architecture over pure LoRaWAN

---

## Category 2: LoRa Mesh / Multi-Hop

### [6] Liao et al., "Multi-Hop LoRa Networks Enabled by Concurrent Transmission," IEEE Access, 2017
- **Summary**: One of the first proposals for multi-hop LoRa
- **Relevance**: Direct precursor to our mesh approach
- **Cite when**: Describing multi-hop LoRa feasibility

### [7] Meshtastic Contributors, "Meshtastic: Off-Grid Communication," 2023
- **Summary**: Open-source LoRa mesh platform using flooding
- **Relevance**: Key baseline comparison — lacks AI routing and energy awareness
- **Cite when**: Comparing with existing LoRa mesh solutions

### [8] Lundell et al., "A Routing Protocol for LoRa Mesh Networks," IEEE WF-IoT, 2018
- **Summary**: Proposes routing tables for LoRa mesh with distance-vector
- **Relevance**: Alternative routing approach (we use multi-criteria AI instead)
- **Cite when**: Discussing routing algorithm design choices

### [9] Dias & Grilo, "LoRaMesh: A Custom Multi-Hop Protocol," Sensors, 2020
- **Summary**: Custom LoRa mesh protocol with time-slotted access
- **Relevance**: Comparison baseline for mesh protocol design
- **Cite when**: Comparing our MAC approach with TDMA-based solutions

### [10] Bezerra et al., "Multi-Hop LoRa Linear Sensor Network," IEEE Sensors Journal, 2021
- **Summary**: Linear multi-hop LoRa for pipeline monitoring
- **Relevance**: Validates multi-hop LoRa over long distances (similar to our backbone)
- **Cite when**: Justifying backbone relay corridor design

---

## Category 3: Self-Healing Protocols

### [11] Perkins et al., "Ad hoc On-Demand Distance Vector (AODV) Routing," RFC 3561, 2003
- **Summary**: Foundational reactive routing protocol for ad-hoc networks
- **Relevance**: AODV is our primary baseline for comparison
- **Cite when**: Describing AODV baseline implementation

### [12] Johnson et al., "DSR: Dynamic Source Routing," RFC 4728, 2007
- **Summary**: Source-routing protocol for mobile ad-hoc networks
- **Relevance**: Alternative self-healing approach (source-routed vs. hop-by-hop)
- **Cite when**: Discussing routing protocol design alternatives

### [13] Clausen & Jacquet, "OLSR: Optimized Link State Routing," RFC 3626, 2003
- **Summary**: Proactive link-state routing for mobile networks
- **Relevance**: Proactive component of our hybrid approach (heartbeat-based)
- **Cite when**: Explaining hybrid proactive+reactive design choice

### [14] Stankovic et al., "Self-Healing Wireless Sensor Networks," IEEE Computer, 2016
- **Summary**: Survey of self-healing mechanisms in WSNs
- **Relevance**: Establishes state-of-art in self-healing (we extend with AI)
- **Cite when**: Defining self-healing requirements and background

---

## Category 4: AI/ML in IoT Routing

### [15] Fadlullah et al., "State-of-the-Art Deep Learning for Communication Networks," IEEE COMST, 2017
- **Summary**: Survey of deep learning applications in networking
- **Relevance**: Establishes AI-for-routing as a research direction
- **Cite when**: Justifying AI-driven routing approach

### [16] Banerjee et al., "TinyML: Machine Learning for Microcontrollers," 2021
- **Summary**: Overview of ML inference on resource-constrained devices
- **Relevance**: Validates feasibility of AI agents on ESP32-class hardware
- **Cite when**: Discussing TinyML implementation on SOS/relay nodes

### [17] Liu et al., "Energy-Efficient Routing with Q-Learning for WSN," IEEE TNSE, 2020
- **Summary**: Reinforcement learning for energy-aware routing decisions
- **Relevance**: Similar goal (energy-aware routing) different method (RL vs. weighted scoring)
- **Cite when**: Comparing our weighted scoring with RL approaches

### [18] Mao et al., "Routing Optimization with Deep RL in IoT Networks," IEEE IoT-J, 2020
- **Summary**: Deep reinforcement learning for IoT routing
- **Relevance**: Advanced AI routing (may be too heavy for ESP32 but future work)
- **Cite when**: Discussing future work / more advanced AI approaches

---

## Category 5: Delay-Tolerant Networking

### [19] Fall, "A Delay-Tolerant Network Architecture," ACM SIGCOMM, 2003
- **Summary**: Seminal DTN paper establishing store-and-forward paradigm
- **Relevance**: Theoretical foundation for our mobile relay mechanism
- **Cite when**: Introducing store-and-forward concept

### [20] Vahdat & Becker, "Epidemic Routing for Partially-Connected Ad Hoc Networks," Duke Tech Report, 2000
- **Summary**: Epidemic (flooding-based) routing for disconnected networks
- **Relevance**: Our mobile relay uses selective collection, not epidemic flooding
- **Cite when**: Comparing DTN routing strategies

### [21] Shah et al., "Data Mules: Modeling a Three-Tier Architecture for Sparse Sensor Networks," IEEE SNPA, 2003
- **Summary**: Mobile entities (mules) collecting data from sparse sensors
- **Relevance**: DIRECTLY relevant — our boat/backpack relays ARE data mules
- **Cite when**: Describing mobile relay concept and its theoretical basis

### [22] Spyropoulos et al., "Spray and Wait: Efficient Routing in Intermittently Connected Networks," ACM WDTN, 2005
- **Summary**: Limited-copy forwarding strategy for DTN
- **Relevance**: Our mobile relay uses limited collection (priority-based), not spray
- **Cite when**: Comparing our collection strategy with spray-and-wait

---

## Category 6: Disaster Communication

### [23] Sakhardande et al., "Design of Disaster Management System Using IoT," IOTA, 2016
- **Summary**: IoT-based disaster management framework
- **Relevance**: General disaster IoT context (we focus on communication layer)
- **Cite when**: Broader disaster management context

### [24] Manzoni et al., "Emergency Communication Through LoRa," IEEE Access, 2019
- **Summary**: LoRa-based emergency communication system design
- **Relevance**: Similar application domain, but no mesh/self-healing
- **Cite when**: Showing existing LoRa disaster work lacks mesh capability

### [25] Ullah et al., "IoT-Based Emergency and Disaster Management Systems," IEEE Access, 2021
- **Summary**: Survey of IoT disaster management systems
- **Relevance**: Establishes research landscape and gaps
- **Cite when**: Introduction — surveying current disaster ICT solutions

### [26] Ray et al., "IoT for Disaster Management: State-of-the-Art and Prospects," IEEE Access, 2017
- **Summary**: Comprehensive IoT disaster management survey
- **Relevance**: Identifies communication as key challenge in disasters
- **Cite when**: Motivating the research problem

### [27] Hossain et al., "Flood Disaster Management in Bangladesh," 2020
- **Summary**: Bangladesh-specific flood management challenges
- **Relevance**: Case study context — Tanguar Haor flooding patterns
- **Cite when**: Justifying case study area selection

---

## Category 7: Energy-Efficient IoT

### [28] Rault et al., "Energy Efficiency in WSN: Survey," IEEE COMST, 2014
- **Summary**: Comprehensive survey of energy-efficient WSN techniques
- **Relevance**: Background for our Energy Agent design
- **Cite when**: Discussing energy management strategies

### [29] Bouguera et al., "Energy Consumption Model for LoRa," Sensors, 2018
- **Summary**: Detailed energy consumption model for LoRa devices
- **Relevance**: Our energy model is based on similar approach
- **Cite when**: Validating energy model parameters in simulation

### [30] Casals et al., "Modeling the Energy Performance of LoRaWAN," Sensors, 2017
- **Summary**: LoRaWAN energy performance modeling
- **Relevance**: Reference for energy parameters (current, sleep, Tx time)
- **Cite when**: Justifying energy model values in simulation setup

---

## Category 8: Network Simulation

### [31] Magrin et al., "Performance Evaluation of LoRa Networks in NS-3," WNS3, 2017
- **Summary**: NS-3 LoRa module development and validation
- **Relevance**: If using NS-3 for simulation, this validates the model
- **Cite when**: Describing simulation environment choice

### [32] Slabicki et al., "Adaptive Configuration of LoRa Networks," NOMS, 2018
- **Summary**: Adaptive SF/power allocation in LoRa networks
- **Relevance**: Similar optimization goal (adaptive parameters)
- **Cite when**: Discussing adaptive parameter tuning in our system

---

## Category 9: Agentic AI / Multi-Agent Systems

### [33] Wooldridge, "An Introduction to MultiAgent Systems," Wiley, 2009
- **Summary**: Foundational textbook on multi-agent systems
- **Relevance**: Theoretical basis for our 7-agent architecture
- **Cite when**: Defining "Agentic AI" and multi-agent coordination

### [34] Dorri et al., "Multi-Agent Systems: A Survey," IEEE Access, 2018
- **Summary**: Survey of multi-agent systems in various domains
- **Relevance**: Establishes multi-agent paradigm for distributed systems
- **Cite when**: Justifying agent-based architecture for distributed IoT

### [35] Park et al., "Generative Agents: Interactive Simulacra," arXiv, 2023
- **Summary**: Influential paper on autonomous AI agents
- **Relevance**: Establishes "Agentic AI" terminology and paradigm
- **Cite when**: Connecting to modern Agentic AI concepts in introduction

---

## How to Find More Papers

1. Start with these papers on Google Scholar
2. Click "Cited by" to find NEWER papers that built on them
3. Check their reference lists for OLDER foundational papers
4. Use Connected Papers (connectedpapers.com) for visual exploration
5. Search for recent surveys (2023-2026) in your specific sub-topic
6. Check IEEE Xplore for the latest conference proceedings

---

## Citation Count Targets

| Section | Number of Citations |
|---------|--------------------|
| Introduction | 5-8 |
| Related Work (total) | 20-30 |
| System Architecture | 3-5 (justifying design choices) |
| Evaluation | 3-5 (methodology references) |
| **Total** | **35-50** |
