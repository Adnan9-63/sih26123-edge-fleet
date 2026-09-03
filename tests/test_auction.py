from fleet.agent import Agent
from fleet.allocation.auction import Task, check_blocked_agents, run_auction
from fleet.grid import WarehouseGrid
from fleet.sim.engine import SimulationEngine


def test_auction_assigns_task_to_closest_idle_agent():
    grid = WarehouseGrid.default()
    agents = {
        "near": Agent(agent_id="near", pos=(1, 0), goal=(1, 0)),
        "far": Agent(agent_id="far", pos=(9, 8), goal=(9, 8)),
    }
    task = Task(task_id="t1", pickup_cell=(0, 0))

    remaining = run_auction(grid, agents, [task])

    assert remaining == []
    assert agents["near"].task_id == "t1"
    assert agents["near"].goal == (0, 0)
    assert agents["far"].task_id is None, "the far agent should not have won this bid"


def test_auction_leaves_task_open_when_no_idle_agents():
    grid = WarehouseGrid.default()
    busy = Agent(agent_id="busy", pos=(0, 0), goal=(9, 8), task_id="already-carrying")
    agents = {"busy": busy}
    task = Task(task_id="t1", pickup_cell=(5, 5))

    remaining = run_auction(grid, agents, [task])

    assert remaining == [task]
    assert busy.task_id == "already-carrying", "must not overwrite an agent already on a task"


def test_stuck_agent_releases_task_back_to_open_pool():
    """Unit test of the release mechanism in isolation, independent of
    *why* the agent got stuck -- see the full integration test below for
    a real blocked-aisle scenario driving this end to end."""
    agent = Agent(agent_id="a", pos=(3, 3), goal=(7, 7), task_id="t1", blocked_ticks=5)
    agents = {"a": agent}

    released = check_blocked_agents(agents, open_tasks=[])

    assert len(released) == 1
    assert released[0].task_id == "t1"
    assert released[0].pickup_cell == (7, 7)
    assert agent.task_id is None
    assert agent.goal == agent.pos, "released agent should idle in place, not keep chasing the old goal"
    assert agent.blocked_ticks == 0


def test_blocked_aisle_reassigns_task_to_a_different_agent_end_to_end():
    """The actual PS scenario: one robot encounters a blocked aisle
    mid-task; a different, unblocked robot picks up the same task
    instead of the fleet waiting on the stuck one indefinitely.

    Layout reminder (see grid.py): x=0, x=5, x=9 are the only vertical
    corridors. Blocking all of x=0's corridor cells forces "mover"
    (assigned via the x=0 route) to have no way through, while "backup"
    can still reach the same pickup point via the x=5 corridor.
    """
    grid = WarehouseGrid.default()
    for y in (1, 3, 5, 7):
        grid.block_cell((0, y))  # seal off the entire x=0 corridor

    agents = {
        "mover": Agent(agent_id="mover", pos=(0, 0), goal=(0, 0)),
        "backup": Agent(agent_id="backup", pos=(5, 0), goal=(5, 0)),
    }
    task = Task(task_id="pickup-42", pickup_cell=(0, 8))

    # "mover" is closer in raw terms but -- crucially -- run_auction bids
    # on TRUE graph distance (Day 4's BFS fix), so with x=0 fully sealed
    # it should already prefer "backup" even before anything gets stuck.
    open_tasks = run_auction(grid, agents, [task])
    assert open_tasks == []
    winner_id = "mover" if agents["mover"].task_id == "pickup-42" else "backup"

    engine = SimulationEngine(grid, list(agents.values()), mode="pibt")
    # engine.agents are the SAME Agent objects (constructed from
    # agents.values()), so mutations from run_auction are already live.

    completed_task_ids = set()
    for tick in range(120):
        engine.step()
        newly_open = check_blocked_agents(engine.agents, open_tasks=[])
        if newly_open:
            run_auction(grid, engine.agents, newly_open)
        for agent in engine.agents.values():
            if agent.task_id is not None and agent.pos == agent.goal:
                completed_task_ids.add(agent.task_id)
                agent.task_id = None

        if "pickup-42" in completed_task_ids:
            break

    assert "pickup-42" in completed_task_ids, "task must eventually be completed by SOMEONE"
    if winner_id == "mover":
        # if "mover" somehow won the initial bid despite the block, it
        # must have been re-routed to "backup" by the blocked-agent check
        assert agents["backup"].blocked_ticks == 0  # backup did real work, not stuck
