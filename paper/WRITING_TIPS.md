# Research Paper Writing Tips for Beginners

## A Complete Guide to Academic Writing Style, Structure, and Best Practices

---

## 1. Before You Start Writing

### 1.1 Read Papers in Your Target Venue
Before writing a single word, read 5-10 papers from the journal/conference you're targeting. Notice:
- How long is the average paper? (page count)
- What sections do they typically have?
- How many figures/tables are common?
- What citation style do they use? (IEEE, ACM, etc.)
- How formal is the language?

### 1.2 Know Your Audience
- **IEEE IoT Journal**: Expects strong technical depth, mathematical formulations
- **IEEE Access**: Broader audience, more accessible language
- **Conference papers (ICC, GLOBECOM)**: Shorter (6-8 pages), more focused
- **Workshop papers**: Even shorter (4 pages), can be more exploratory

### 1.3 Organize Your Evidence First
Before writing, gather:
- [ ] All simulation results (tables, raw data)
- [ ] All figures ready (or sketched)
- [ ] Key related work papers read and noted
- [ ] Protocol specifications finalized
- [ ] Clear list of contributions

---

## 2. Academic Writing Style Rules

### 2.1 Use Third Person or "We"
```
❌ WRONG: "I designed a self-healing protocol..."
✓ RIGHT: "We design a self-healing protocol..."
✓ RIGHT: "A self-healing protocol is proposed..."
```

### 2.2 Present Tense for Facts, Past Tense for Actions
```
✓ "LoRa uses Chirp Spread Spectrum modulation." (fact — present)
✓ "We evaluated the system under 50% failure rate." (what you did — past)
✓ "The results demonstrate improved delivery." (findings — present)
✓ "Figure 3 shows the latency distribution." (describing figures — present)
```

### 2.3 Be Specific, Not Vague
```
❌ WRONG: "The system performs much better than existing solutions."
✓ RIGHT: "The proposed system achieves 93% PDR under 20% relay failure, 
          compared to 79% for AODV-based routing."

❌ WRONG: "The latency is very low."
✓ RIGHT: "The average end-to-end latency is 4.2 seconds."

❌ WRONG: "Many researchers have worked on this problem."
✓ RIGHT: "Prior works [3]-[7] address LoRa mesh routing but lack 
          self-healing capability."
```

### 2.4 Avoid Informal Language
```
❌ WRONG: "This is a really cool approach..."
✓ RIGHT: "This approach offers significant advantages..."

❌ WRONG: "The system works great..."
✓ RIGHT: "The system demonstrates effective performance..."

❌ WRONG: "Obviously, LoRa is better than WiFi for this..."
✓ RIGHT: "LoRa provides superior range characteristics compared to 
          WiFi for this application scenario."
```

### 2.5 Define All Acronyms on First Use
```
✓ RIGHT: "Long Range (LoRa) modulation enables communication up to 15 km. 
          LoRa Wide Area Network (LoRaWAN) defines the MAC layer protocol 
          built on top of LoRa."
```
After first definition, use the acronym freely.

### 2.6 One Idea Per Paragraph
Each paragraph should:
1. Start with a topic sentence (what the paragraph is about)
2. Develop that single idea with evidence/explanation
3. End with a transition to the next paragraph

```
EXAMPLE:
"The self-healing mechanism relies on periodic heartbeat messages 
exchanged between neighboring nodes. [TOPIC SENTENCE] Each node 
broadcasts a heartbeat packet every T_h seconds containing its 
node ID, battery level, and neighbor table. [DEVELOPMENT] When a 
node fails to receive three consecutive heartbeats from a neighbor, 
it marks that neighbor as DOWN and triggers a route recalculation. 
[MORE DETAIL] This approach enables detection of failures within 
3×T_h seconds, providing a tunable trade-off between detection 
speed and energy consumption. [CONCLUSION/TRANSITION]"
```

---

## 3. Common Mistakes to Avoid

### 3.1 Plagiarism
- NEVER copy text from other papers, even with citation
- Paraphrase in your own words and cite the source
- Use plagiarism detection tools (Turnitin, iThenticate) before submission
- Direct quotes are extremely rare in engineering papers

### 3.2 Overclaiming
```
❌ WRONG: "Our system is the first to solve disaster communication."
✓ RIGHT: "To the best of our knowledge, this is the first system to 
          combine self-healing LoRa mesh routing with distributed 
          Agentic AI agents for disaster SOS delivery."
```
Always qualify claims with "to the best of our knowledge" or "among existing approaches."

### 3.3 Missing Baselines
- NEVER present results without comparison to at least 2-3 baselines
- Baselines should include: (1) a simple/naive approach, (2) existing state-of-art
- Fair comparison means same simulation conditions for all approaches

### 3.4 Figures Without Explanation
Every figure/table MUST be:
1. Referenced in the text: "As shown in Fig. 3..."
2. Explained: what does it show and why is it important?
3. Labeled clearly (axis labels, legends, units)

### 3.5 Unsupported Statements
```
❌ WRONG: "LoRa is the best technology for disaster communication."
          (Where's the evidence?)
✓ RIGHT: "LoRa's combination of long range (up to 15 km in rural areas [3]), 
          low power consumption (25 mA Tx current [4]), and operation in 
          unlicensed spectrum makes it well-suited for disaster scenarios 
          where infrastructure is unavailable."
```

---

## 4. How to Write Each Section (Practical Tips)

### 4.1 Writing Order (Don't Write Linearly!)
The best order to write a research paper:

```
1. System Architecture (Section 4) — Write this FIRST, you know it best
2. Evaluation Methodology (Section 6) — Describe what you did
3. Results (Section 7) — Present what you found
4. Related Work (Section 3) — You've read the papers by now
5. Introduction (Section 2) — Now you know what to introduce
6. Conclusion (Section 8) — Summarize what you've written
7. Abstract (Section 1) — Write this LAST
```

### 4.2 Introduction Writing Formula
```
Paragraph 1: Context (broad problem — disaster communication)
Paragraph 2: Specific challenge (why existing solutions fail)
Paragraph 3: Your approach (high-level description)
Paragraph 4: Research questions (specific RQs)
Paragraph 5: Contributions (numbered list)
Paragraph 6: Paper organization (roadmap)
```

### 4.3 Related Work Writing Formula
For each related paper/system:
```
1. What did they do? (1-2 sentences)
2. How does it relate to your work? (1 sentence)
3. What limitation does it have that your work addresses? (1 sentence)
```

Example:
```
"Meshtastic [5] provides an open-source LoRa mesh protocol enabling 
multi-hop communication without infrastructure. However, it employs 
simple flooding-based routing without energy awareness or intelligent 
path selection, leading to rapid battery depletion under high message 
loads — a critical limitation in disaster scenarios where power 
resupply is unavailable."
```

### 4.4 System Architecture Writing Formula
For each component:
```
1. Purpose: What problem does this component solve?
2. Design: How does it work? (with diagram/pseudocode)
3. Justification: Why this design choice over alternatives?
```

### 4.5 Results Interpretation Formula
For each result:
```
1. State the observation: "Table II shows that..."
2. Explain why: "This improvement is attributed to..."
3. Compare with baselines: "Compared to AODV, our approach achieves..."
4. Discuss significance: "This is particularly important because..."
```

---

## 5. Figures and Tables Best Practices

### 5.1 Figure Requirements
- **Resolution**: Minimum 300 DPI for print
- **Font size in figures**: At least 8pt (readable when printed)
- **Colors**: Use colorblind-friendly palettes; ensure readability in B&W
- **Vector format**: Use SVG/PDF for line drawings (not JPEG)
- **Caption**: Below the figure, descriptive enough to understand without reading text

### 5.2 Essential Figures for This Paper
```
Figure 1: System architecture overview (multi-tier topology diagram)
Figure 2: Node deployment map on Tanguar Haor geography
Figure 3: Self-healing process flowchart
Figure 4: Routing agent decision algorithm
Figure 5: PDR vs. failure rate comparison graph
Figure 6: End-to-end latency CDF
Figure 7: Energy consumption over time
Figure 8: Mobile relay message collection rate
```

### 5.3 Table Best Practices
- Column headers should be clear and include units
- Align numbers by decimal point
- Bold the best result in each row/column
- Include confidence intervals or standard deviation if applicable

### 5.4 Tools for Creating Figures
| Type | Recommended Tools |
|------|-------------------|
| Architecture diagrams | draw.io, Lucidchart, Visio |
| Flowcharts | draw.io, PlantUML |
| Graphs/plots | Python matplotlib, MATLAB |
| Network topology | NS-3 visualizer, custom Python |
| Maps | QGIS, Google Earth + annotations |

---

## 6. Citation Best Practices

### 6.1 IEEE Citation Style
```
In-text: "As demonstrated in [1], LoRa can achieve ranges up to 15 km."
         "Several works [3]-[7] have addressed mesh routing for IoT."
         "Author et al. [2] proposed a self-healing protocol for WSNs."
```

### 6.2 How Many References?
- **Journal paper (12+ pages)**: 40-60 references
- **Conference paper (6-8 pages)**: 20-35 references
- **Workshop paper (4 pages)**: 15-25 references

### 6.3 What to Cite
- Every claim that isn't your own original finding
- Background facts about technologies (LoRa specs, etc.)
- Related work comparisons
- Algorithms you build upon
- Tools/simulators you use

### 6.4 Reference Management Tools
- **Zotero** (free, open-source) — RECOMMENDED for beginners
- **Mendeley** (free) — good PDF annotation
- **EndNote** (paid) — if your university provides it
- **BibTeX** — if using LaTeX directly

### 6.5 Finding Good References
1. **Google Scholar**: Start here for keyword searches
2. **IEEE Xplore**: For IEEE papers specifically
3. **Semantic Scholar**: AI-powered paper discovery
4. **Connected Papers**: Visualize citation networks
5. **Reference lists**: Check references of papers you've found

---

## 7. LaTeX / Overleaf Tips

### 7.1 Getting Started with LaTeX
1. Create a free account on [Overleaf](https://www.overleaf.com)
2. Start a new project using the IEEE template
3. Templates available:
   - IEEE Transactions (journal): `IEEEtran.cls`
   - IEEE Conference: `conference` option in `IEEEtran.cls`

### 7.2 Basic LaTeX Structure
```latex
\documentclass[journal]{IEEEtran}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{cite}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{booktabs}

\begin{document}

\title{Your Paper Title Here}
\author{Your Name \\ Your Affiliation \\ email@university.edu}
\maketitle

\begin{abstract}
Your abstract text here...
\end{abstract}

\begin{IEEEkeywords}
LoRa, self-healing, mesh network, disaster communication, Agentic AI
\end{IEEEkeywords}

\section{Introduction}
Your introduction text...

\section{Related Work}
\subsection{LoRa and LoRaWAN}
Text...

% ... more sections ...

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
```

### 7.3 Useful LaTeX Commands
```latex
% Figure
\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/architecture.pdf}
\caption{Multi-tier system architecture overview.}
\label{fig:architecture}
\end{figure}

% Table
\begin{table}[t]
\centering
\caption{Performance Comparison Under 20\% Relay Failure}
\label{tab:results}
\begin{tabular}{lccc}
\toprule
Metric & AODV & Flooding & Proposed \\
\midrule
PDR (\%) & 79 & 71 & \textbf{93} \\
Latency (s) & 5.4 & 8.7 & \textbf{4.2} \\
\bottomrule
\end{tabular}
\end{table}

% Algorithm
\begin{algorithm}[t]
\caption{Self-Healing Route Recovery}
\label{alg:selfheal}
\begin{algorithmic}[1]
\STATE \textbf{Input:} Failed node ID $n_f$
\STATE Mark $n_f$ as DOWN in neighbor table
\STATE Invalidate all routes through $n_f$
\FOR{each pending message $m$ in queue}
    \STATE $path \leftarrow$ RouteAgent.findAlternate($m.dest$)
    \IF{$path \neq \emptyset$}
        \STATE Forward $m$ via $path$
    \ELSE
        \STATE Store $m$ for mobile relay collection
    \ENDIF
\ENDFOR
\end{algorithmic}
\end{algorithm}

% Equation
\begin{equation}
\text{RouteScore}(p) = w_1 \cdot \text{RSSI}(p) + w_2 \cdot \text{Battery}(p) - w_3 \cdot \text{Hops}(p)
\label{eq:routescore}
\end{equation}

% Cross-references
As shown in Fig.~\ref{fig:architecture}...
Table~\ref{tab:results} presents...
The route score is computed using (\ref{eq:routescore})...
Algorithm~\ref{alg:selfheal} describes...
```

---

## 8. Revision and Proofreading Checklist

### First Pass: Structure
- [ ] Does each section flow logically to the next?
- [ ] Are all research questions answered in the results?
- [ ] Is every figure/table referenced and explained?
- [ ] Are contributions in the introduction supported by results?

### Second Pass: Clarity
- [ ] Can each sentence be understood on first reading?
- [ ] Are there any ambiguous pronouns ("it", "this", "they")?
- [ ] Are paragraphs the right length (4-8 sentences typically)?
- [ ] Is technical jargon defined before use?

### Third Pass: Correctness
- [ ] Are all numbers consistent between text and tables?
- [ ] Are units specified everywhere?
- [ ] Are all acronyms defined on first use?
- [ ] Are figure numbers sequential?
- [ ] Do all references appear in the bibliography?

### Fourth Pass: Polish
- [ ] Run spell-check (but don't rely on it alone)
- [ ] Check for consistent formatting (e.g., "Fig." vs "Figure")
- [ ] Ensure consistent notation throughout
- [ ] Check that the paper meets page limits
- [ ] Verify author information and acknowledgments

---

## 9. Responding to Peer Reviews

### 9.1 When You Get Reviews Back
- Read ALL reviews before responding to any
- Take 24 hours before starting your response (don't react emotionally)
- Address EVERY point raised, even if you disagree

### 9.2 Response Letter Format
```
--------------------------------------------
Response to Reviewer 1, Comment 3:

REVIEWER COMMENT:
"The authors should compare with more recent LoRa mesh protocols 
such as [reference]."

OUR RESPONSE:
We thank the reviewer for this suggestion. We have now included 
a comparison with [protocol name] in Section III-B (Related Work) 
and added it as a baseline in our simulations (Section VI). The 
results in Table III (new) show that our approach outperforms 
[protocol] by X% in PDR under 30% failure conditions.

CHANGES MADE:
- Added paragraph in Section III-B, page 4, lines 12-18
- Added new baseline in Table III
- Updated Figure 7 with additional comparison curve
--------------------------------------------
```

### 9.3 Common Review Outcomes
- **Accept**: Rare for first submission. Celebrate!
- **Minor Revision**: Good news! Small changes needed, usually accepted after.
- **Major Revision**: Significant work needed, but still has a chance.
- **Reject**: Don't give up. Revise and submit to another venue.

---

## 10. Time Management Tips

### 10.1 Writing Schedule
- Set a daily writing goal (e.g., 500 words/day or 1 section/week)
- Write at your most productive time of day
- Don't edit while writing — get ideas down first, polish later
- Use the Pomodoro technique (25 min writing, 5 min break)

### 10.2 Dealing with Writer's Block
- Start with the section you're most comfortable with
- Write bullet points first, then expand into paragraphs
- Talk through your ideas out loud (or to a colleague)
- Read a related paper to get your mind in "academic mode"
- Move to a different section and come back later

### 10.3 Backup Strategy
- Use Overleaf (auto-saves and has version history)
- Or use Git for LaTeX files
- Email yourself a backup weekly
- Never have only one copy of your paper!

---

## 11. Keywords for This Research

When submitting, use relevant keywords:
```
Primary: LoRa, mesh network, self-healing, disaster communication, 
         Agentic AI, IoT

Secondary: delay-tolerant network, store-and-forward, multi-hop routing, 
           energy-aware, TinyML, flood, emergency, LoRaWAN

Specific: heartbeat protocol, route recovery, mobile relay, 
          incident clustering, priority routing
```

---

## Quick Reference: Common Academic Phrases

| Purpose | Phrases |
|---------|---------|
| Introducing topic | "In recent years...", "With the increasing demand for..." |
| Stating problem | "However, existing approaches lack...", "A key challenge is..." |
| Proposing solution | "We propose...", "This paper presents...", "We introduce..." |
| Comparing | "In contrast to [X], our approach...", "Unlike previous work..." |
| Showing results | "Results demonstrate that...", "As shown in Table X..." |
| Acknowledging limits | "One limitation of...", "Future work could address..." |
| Concluding | "In summary...", "These findings suggest...", "We have demonstrated..." |
