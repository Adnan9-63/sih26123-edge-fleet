# SIH 2026 Idea Submission Video Script
**Problem Statement:** 26123 - Edge-AI Based Distributed Fleet Coordination for Autonomous Mobile Robots (AMRs) in Smart Warehouses
**Target Duration:** 3 minutes

---

### [0:00 - 0:15] Hook / Problem Statement
**VISUAL:** Fast-paced animation of a modern smart warehouse. Hundreds of robots moving. Suddenly, a red Wi-Fi icon flashes. The central cloud server icon goes dark. Robots crash, halt, and form a massive gridlock.
**NARRATION:** "Modern smart warehouses rely on fleets of autonomous mobile robots. But as fleets grow, centralized cloud control creates fatal bottlenecks — network latency, Wi-Fi dead zones, and single points of failure. What happens when the brain goes down? Everything stops."

### [0:15 - 0:40] Our Solution
**VISUAL:** The gridlock dissolves. A new architecture diagram builds up: a robot with three distinct layers inside (P2P Comms, PIBT Conflict Resolution, Task Bidding). Text overlays appear: "NO Central Server." "XGBoost + Isolation Forest."
**NARRATION:** "Our solution eliminates the brain entirely. We present a three-layer, fully decentralized edge stack. Peer-to-peer communication, local PIBT conflict resolution, and auction-based task allocation. Powered by Edge-AI using XGBoost and Isolation Forests. Our core guarantee: NO central server anywhere. Period."

### [0:40 - 1:10] Core Algorithm (PIBT)
**VISUAL:** Screen recording of `visuals/warehouse_demo.html`. Show 3-4 robots navigating a very narrow, high-traffic intersection. They weave around each other fluidly without stopping. A highlight shows their localized communication radii.
**NARRATION:** "At the core is our PIBT algorithm. Each robot only talks to its immediate neighbors. If two robots want the same cell, the one that's been waiting longer gets priority. If this creates a chain reaction, the chain resolves locally across neighbors — no central coordinator needed. Based on IJCAI 2019 research, it is mathematically proven to be deadlock-free."

### [1:10 - 1:35] Edge-AI Layer
**VISUAL:** Cut to technical diagrams. Left: XGBoost tree predicting congestion. Right: Isolation Forest plotting a robot's strange behavior as an outlier. Show the tiny model file sizes (`<50KB`).
**NARRATION:** "Our Edge-AI doesn't just react to problems — it predicts them. A tiny XGBoost model, running in under 2 milliseconds on a Raspberry Pi, predicts aisle congestion before robots enter. An Isolation Forest monitors internal metrics to flag malfunctioning units before they cascade failures across the fleet. Both models are under 50 kilobytes — small enough to fit in the CPU cache."

### [1:35 - 2:00] Live Demo / Resilience
**VISUAL:** Back to the browser demo. A cursor clicks a busy aisle, dropping a red "BLOCK" obstacle. The robots instantly calculate new paths.
**VISUAL:** Terminal split-screen. One terminal process is abruptly killed (simulating a dead robot). The other robots ping the dead unit, recognize it's gone in seconds, and route around it.
**NARRATION:** "Watch what happens when we block an aisle mid-operation — the fleet re-routes instantly, zero collisions. Now watch what happens when we kill a robot's connection entirely — the other robots don't even flinch. They detect the missing peer within two seconds and continue their missions. This is what true decentralization looks like."

### [2:00 - 2:25] Benchmark Results
**VISUAL:** A clean, high-contrast benchmark table.
*   Collisions: Stop-and-Wait (Many) vs. Ours (ZERO)
*   Throughput: Stop-and-Wait (Deadlocks) vs. Ours (93%+ Faster)
**NARRATION:** "The problem statement asks for zero collisions and at least 20% faster than stop-and-wait methods. Our results? Zero collisions in every scenario, every run. And over 93% faster — not because we cherry-picked scenarios, but because stop-and-wait permanently deadlocks in narrow corridors. Our PIBT stack resolves those bottlenecks in real-time."

### [2:25 - 2:50] Feasibility & Edge Hardware
**VISUAL:** B-roll/photos of a Raspberry Pi 4 and a Jetson Nano. Quick specs overlay: "Inference: <2ms. Memory: <100KB. Cloud required: NONE."
**NARRATION:** "Everything you've seen runs entirely on a Raspberry Pi 4. The PIBT logic takes under 1.5 milliseconds per tick. Our AI models are under 100 kilobytes total. No GPU, no cloud, no internet required. This is designed for air-gapped military depots and remote facilities where connectivity cannot be assumed, and collision safety is non-negotiable."

### [2:50 - 3:00] Closing
**VISUAL:** Final architecture diagram morphing into the Team Name and SIH Problem Statement ID (26123).
**NARRATION:** "Edge-AI fleet coordination. Decentralized by design. Proven by math. Verified by code. Thank you."
