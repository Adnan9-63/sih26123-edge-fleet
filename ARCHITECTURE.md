# Architecture

## Design principle

Every robot is an independent process. Nothing in this system — not the
dashboard, not any shared object, not a queue — sits between two robots'
decisions. If you can point to one thing whose failure would stop the
whole fleet, that's a bug in the architecture, not an acceptable
trade-off. This is the property SIH26123 is actually testing for, more
than any individual algorithm choice.

## Layers (per robot)

```
   Task Allocation (allocation/auction.py)
        - Contract Net-style bidding for pickup tasks
        - no dispatcher: every idle agent bids independently
                 |
   Path Planning (planning/pibt.py)
        - Priority Inheritance with Backtracking (Okumura et al., 2019)
        - resolves discrete-grid conflicts, deadlock-free by construction
                 |
   Local Avoidance (avoidance/orca.py)
        - Optimal Reciprocal Collision Avoidance (van den Berg et al., 2008)
        - continuous-space, real-time, no communication required for
          avoidance itself
                 |
   Comms substrate (comms/p2p.py)
        - ROS2 + DDS (preferred) or raw UDP multicast (fallback)
        - broker-free peer discovery -- deliberately NOT MQTT, which
          requires a central broker and would reintroduce the single
          point of failure the PS explicitly asks us to remove
```

## Why PIBT, not CBS

Conflict-Based Search is a strong algorithm family, but in its classic
form it searches the *joint* conflict space of all agents at once —
that's inherently centralized computation, even if you later distribute
where it runs. PIBT resolves conflicts through local, per-tick priority
comparisons between agents that are actually adjacent to each other. That
is what makes it a fit for "algorithms for edge hardware": the compute
per agent per tick stays small regardless of fleet size.

## Why ORCA, not a custom velocity solver

ORCA is a published, real-time-proven algorithm (van den Berg et al.,
2008), demonstrated on real robots and validated at scale (thousands of
simulated agents, collision-free velocities computed in milliseconds).
There is a mature, pip-installable implementation (Python-RVO2) — using
it removes a large chunk of implementation risk that would otherwise go
into re-deriving and debugging the underlying linear program ourselves.

## Why the dashboard is one-way

`dashboard/render_pygame.py` only ever calls
`SimulationEngine.dashboard_state()` — a read. It never calls into
planning, comms, or allocation. This is what proves, not just claims,
that visualizing the fleet isn't secretly controlling it. If a judge asks
"is there a hidden coordinator," the answer is: check the dashboard's
imports.

## The resilience demo this architecture buys us

Because there is no shared state and no broker, killing one agent's
comms mid-run (see `comms/p2p.py` TODO for a `kill()` method) should not
stop the other agents from continuing to plan and move. A centrally
orchestrated system — including commercial ones — cannot make this claim.
This is the single best live demo moment for judges: show it working,
then kill a robot's connection on stage.

## Benchmark methodology

`benchmark/stop_and_wait_baseline.py` runs the *same* `SimulationEngine`
twice on the *same* scenario: once with agents naively halting whenever a
conflict is predicted (the PS's named baseline, "traditional
stop-and-wait"), and once with the PIBT + ORCA stack resolving conflicts
instead. The two runs' tick counts and collision counts are compared
directly. This is deliberately the same engine both times — the only
variable that changes is the planner — so the comparison is honest and
reproducible, not two different systems being compared unfairly.
