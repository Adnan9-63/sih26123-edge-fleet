# Benchmark results: stop-and-wait baseline vs PIBT

Tick cap per run: 300

## no_contention
- stop-and-wait: 10 ticks, 0 collisions
- PIBT:          10 ticks, 0 collisions
- improvement:   0.0%

## head_on_choke
- stop-and-wait: DNF (>300 ticks), 0 collisions
- PIBT:          10 ticks, 0 collisions
- improvement:   96.7% (CONSERVATIVE LOWER BOUND -- naive never finished within the 300-tick cap, true gap may be larger or infinite)

## three_agent_multi_choke
- stop-and-wait: DNF (>300 ticks), 0 collisions
- PIBT:          20 ticks, 0 collisions
- improvement:   93.3% (CONSERVATIVE LOWER BOUND -- naive never finished within the 300-tick cap, true gap may be larger or infinite)
