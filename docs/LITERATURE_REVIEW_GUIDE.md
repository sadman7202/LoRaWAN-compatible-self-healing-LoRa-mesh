# Literature Review Guide

## How to Find, Read, and Cite Research Papers

---

## 1. Search Strategy

### 1.1 Keywords to Search

Use combinations of these terms on Google Scholar, IEEE Xplore, and Semantic Scholar:

**Primary keywords:**
- "LoRa mesh network"
- "self-healing wireless sensor network"
- "disaster communication IoT"
- "LoRaWAN multi-hop"
- "delay tolerant network disaster"

**Secondary keywords:**
- "energy-aware routing IoT"
- "TinyML edge intelligence"
- "store and forward mobile relay"
- "flood early warning system"
- "emergency mesh network"
- "LPWAN disaster resilience"

**Combined searches (most relevant):**
- "LoRa mesh self-healing routing"
- "LoRaWAN disaster communication flood"
- "AI routing wireless sensor network"
- "mobile data mule delay tolerant"
- "multi-hop LoRa energy aware"

### 1.2 Where to Search

| Source | URL | Best For |
|--------|-----|----------|
| Google Scholar | scholar.google.com | Broad search, citation counts |
| IEEE Xplore | ieeexplore.ieee.org | IEEE papers (high quality) |
| Semantic Scholar | semanticscholar.org | AI-powered recommendations |
| ACM Digital Library | dl.acm.org | ACM conference papers |
| ScienceDirect | sciencedirect.com | Elsevier journals |
| arXiv | arxiv.org | Preprints (cutting edge) |
| Connected Papers | connectedpapers.com | Visual citation graphs |

### 1.3 Search Tips
- Start with recent papers (2020-2026) and work backward
- Look at the "Cited by" and "Related articles" links
- Read survey/review papers first for broad overview
- Check reference lists of good papers for more relevant work
- Use quotation marks for exact phrases: "self-healing mesh"

---

## 2. How to Read a Paper Efficiently

### The 3-Pass Method

**Pass 1 (5-10 minutes):** Get the big picture
- Read title, abstract, introduction (last paragraph with contributions)
- Look at figures and tables
- Read conclusion
- Decision: Is this relevant to my work?

**Pass 2 (30-60 minutes):** Understand the approach
- Read the full paper, skipping proofs/detailed math
- Note key algorithms, architectures, results
- Mark sentences you might cite
- Identify strengths and weaknesses

**Pass 3 (2-4 hours):** Deep understanding (only for key papers)
- Understand every detail
- Try to mentally reproduce the approach
- Identify assumptions and limitations
- Think about how it connects to YOUR work

### What to Note for Each Paper
```
Paper: [Title]
Authors: [Names]
Year: [Year]
Venue: [Journal/Conference]
---
What they did: [1-2 sentences]
How it relates to my work: [1 sentence]
Their limitation (gap I fill): [1 sentence]
Key result: [specific number/finding]
Citation: [BibTeX entry]
```

---

## 3. Organizing Your Related Work

### 3.1 Category Structure (for this research)

Organize papers into these categories:

```
1. LoRa/LoRaWAN Performance & Characteristics
   - Range, power, SF trade-offs
   - Duty cycle limitations
   - Scalability studies

2. LoRa Mesh / Multi-Hop Protocols
   - Meshtastic, LoRaMesh protocols
   - Flooding vs. routing approaches
   - Collision avoidance in mesh

3. Self-Healing Network Protocols
   - AODV, DSR, OLSR for constrained devices
   - Heartbeat/keepalive mechanisms
   - Failure detection algorithms
   - Route convergence analysis

4. AI/ML for IoT Routing
   - Reinforcement learning routing
   - Multi-criteria optimization
   - TinyML on microcontrollers
   - Edge intelligence architectures

5. Delay-Tolerant Networking (DTN)
   - Store-and-forward paradigm
   - Mobile data mules
   - Epidemic/spray-and-wait routing
   - Opportunistic networking

6. Disaster Communication Systems
   - Emergency mesh deployments
   - Post-disaster ICT solutions
   - Community early warning systems
   - Bangladesh flood context
```

### 3.2 The Comparison Table (Critical!)

Your paper MUST have a table like this:

```
| Feature           | LoRaWAN | Meshtastic | [Paper X] | [Paper Y] | OURS |
|-------------------|---------|------------|-----------|-----------|------|
| Long range (>5km) | ✓       | ✓          | ✓         | ✗         | ✓    |
| Multi-hop mesh    | ✗       | ✓          | ✓         | ✓         | ✓    |
| Self-healing      | ✗       | Partial    | ✗         | ✓         | ✓    |
| AI-driven routing | ✗       | ✗          | ✗         | ✗         | ✓    |
| Energy-aware      | ✗       | Partial    | ✓         | ✗         | ✓    |
| Mobile relay/DTN  | ✗       | ✗          | ✗         | ✗         | ✓    |
| Pre-positioning   | ✗       | ✗          | ✗         | ✗         | ✓    |
| Incident cluster  | ✗       | ✗          | ✗         | ✗         | ✓    |
```

This table clearly shows YOUR gap/contribution.

---

## 4. How to Write Related Work

### Formula for Each Paragraph
```
[What prior work did] + [How it relates to ours] + [Its limitation we address]
```

### Example Paragraphs

**Good example:**
```
Bor et al. [5] conducted one of the earliest experimental evaluations of 
LoRa range and reliability in urban environments, demonstrating ranges of 
up to 5 km with packet delivery rates exceeding 90% at spreading factor 12. 
While their work validates LoRa's physical layer suitability for long-range 
IoT, it considers only single-hop star topology and does not address the 
multi-hop mesh routing required when gateway infrastructure may be destroyed 
during disasters.
```

**Another good example:**
```
The Meshtastic project [12] provides an open-source LoRa mesh protocol 
enabling multi-hop communication without infrastructure. Nodes use a 
flooding-based approach where each received packet is rebroadcast to all 
neighbors. However, this simple flooding mechanism lacks energy awareness — 
a critical limitation in disaster scenarios where battery resupply is 
impossible and nodes may need to operate for 72+ hours without solar 
recharge. Our proposed routing agent addresses this by incorporating 
battery state as a primary routing criterion.
```

### What NOT to Do
```
❌ "Smith et al. [3] proposed a mesh routing protocol." 
   (Too vague — what kind? what's the contribution?)

❌ "There are many papers about LoRa mesh." 
   (Which papers? Be specific.)

❌ "Our system is better than all previous work." 
   (Overclaiming without evidence.)
```

---

## 5. Citation Management

### 5.1 Using Zotero (Recommended for Beginners)
1. Download Zotero from zotero.org (free)
2. Install browser extension
3. When you find a paper, click the extension to save it
4. Zotero stores PDF + metadata automatically
5. Export citations as BibTeX for LaTeX

### 5.2 BibTeX Format (for LaTeX)
```bibtex
@article{bor2016lora,
  title={LoRa for the Internet of Things},
  author={Bor, Martin C and Roedig, Utz and Voigt, Thiemo and Alonso, Juan M},
  journal={IEEE Internet of Things Journal},
  year={2016},
  publisher={IEEE}
}

@inproceedings{meshtastic2023,
  title={Meshtastic: An Open Source LoRa Mesh Networking Platform},
  author={Meshtastic Contributors},
  year={2023},
  note={Available: https://meshtastic.org}
}
```

### 5.3 How Many References?
- Minimum: 25-30 for a conference paper
- Ideal: 40-50 for a journal paper
- Distribution: ~60% from last 5 years, ~30% from 5-10 years, ~10% seminal older works

---

## 6. Avoiding Plagiarism

### Golden Rules
1. **NEVER** copy-paste text from another paper
2. Always paraphrase in your OWN words
3. Cite the SOURCE of every idea that isn't yours
4. Even when paraphrasing, include a citation
5. Use plagiarism checker before submission (Turnitin/iThenticate)

### Example: Proper Paraphrasing
```
ORIGINAL (from a paper):
"LoRa achieves remarkable range through chirp spread spectrum 
modulation, trading data rate for sensitivity."

YOUR VERSION:
The long range capability of LoRa is achieved through its use of 
chirp spread spectrum (CSS) modulation, which sacrifices throughput 
in exchange for improved receiver sensitivity [5].
```
