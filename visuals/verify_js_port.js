const {
  generateLargeLayout, Grid, makeAgent, DistCache, runAuction,
  checkBlockedAgents, stepPibt,
} = require("./fleet_sim.js");

let failures = 0;
function check(name, cond) {
  if (cond) console.log("PASS " + name);
  else { console.log("FAIL " + name); failures++; }
}

function runScenario(name, grid, agentsArr, maxTicks = 300) {
  const agents = new Map(agentsArr.map(a => [a.id, a]));
  const distCache = new DistCache();
  let totalCollisions = 0;
  let tick = 0;
  for (; tick < maxTicks; tick++) {
    const collisions = stepPibt(grid, agents, tick, distCache);
    totalCollisions += collisions.length;
    const allAtGoal = [...agents.values()].every(a => a.x === a.goalX && a.y === a.goalY);
    if (allAtGoal) { tick++; break; }
  }
  const allAtGoal = [...agents.values()].every(a => a.x === a.goalX && a.y === a.goalY);
  console.log(`  [${name}] ticks=${allAtGoal ? tick : "DNF"} collisions=${totalCollisions}`);
  return { ticks: allAtGoal ? tick : null, collisions: totalCollisions, agents };
}

// ---- test 1: forced head-on corridor (mirrors test_pibt.py) ----
{
  const layout = ["0000000000","0111101110","0000000000","0111101110","0000000000",
                  "0111101110","0000000000","0111101110","0000000000"];
  const grid = new Grid(layout);
  const agentsArr = [makeAgent("north", 5, 0, 5, 8), makeAgent("south", 5, 8, 5, 0)];
  const r = runScenario("head_on_choke", grid, agentsArr, 100);
  check("head-on corridor: zero collisions", r.collisions === 0);
  check("head-on corridor: both reach goal", r.ticks !== null);
}

// ---- test 2: three agents multi-choke (mirrors test_pibt.py) ----
{
  const layout = ["0000000000","0111101110","0000000000","0111101110","0000000000",
                  "0111101110","0000000000","0111101110","0000000000"];
  const grid = new Grid(layout);
  const agentsArr = [
    makeAgent("agent-1", 0, 0, 9, 8), makeAgent("agent-2", 9, 0, 0, 8),
    makeAgent("agent-3", 4, 0, 4, 8),
  ];
  const r = runScenario("three_agent_multi_choke", grid, agentsArr, 100);
  check("3-agent: zero collisions", r.collisions === 0);
  check("3-agent: all reach goal", r.ticks !== null);
}

// ---- test 3: swap-adjacent-with-DISTINCT-far-goals (mirrors test_pibt.py, must resolve) ----
{
  const layout = ["0000000000","0111101110","0000000000","0111101110","0000000000",
                  "0111101110","0000000000","0111101110","0000000000"];
  const grid = new Grid(layout);
  const agentsArr = [makeAgent("a", 5, 3, 5, 7), makeAgent("b", 5, 4, 5, 1)];
  const r = runScenario("adjacent_distinct_goals", grid, agentsArr, 100);
  check("adjacent distinct goals: zero collisions", r.collisions === 0);
  check("adjacent distinct goals: both reach goal", r.ticks !== null);
}

// ---- test 4: direct positional swap -- known-safe-but-not-guaranteed (mirrors test_pibt.py) ----
{
  const layout = ["0000000000","0111101110","0000000000","0111101110","0000000000",
                  "0111101110","0000000000","0111101110","0000000000"];
  const grid = new Grid(layout);
  const agentsArr = [makeAgent("a", 5, 3, 5, 4), makeAgent("b", 5, 4, 5, 3)];
  const r = runScenario("direct_swap_safety_only", grid, agentsArr, 100);
  check("direct swap: zero collisions (liveness not required)", r.collisions === 0);
}

// ---- test 5: 9-robot large-layout scenario like the live demo will run ----
{
  const layout = generateLargeLayout();
  const grid = new Grid(layout);
  const stagingRow = layout.length - 1;
  const startCols = [1,3,5,7,9,11,13,15,2];
  const agentsArr = startCols.map((c,i) => makeAgent("R"+(i+1), c, stagingRow, c, stagingRow));
  const agentsMap = new Map(agentsArr.map(a => [a.id, a]));
  const distCache = new DistCache();

  const pickupCells = [[2,0],[12,0],[14,2],[8,2],[0,0],[16,2],[6,0],[4,2],[10,0]];
  let openTasks = pickupCells.map((c,i) => ({taskId: "T"+(i+1), pickupX: c[0], pickupY: c[1]}));
  openTasks = runAuction(grid, agentsMap, openTasks, distCache);
  check("9-robot: auction assigns all tasks", openTasks.length === 0);

  let totalCollisions = 0, tick = 0, completed = new Set();
  grid.blockCell(8, 7);
  for (; tick < 300; tick++) {
    totalCollisions += stepPibt(grid, agentsMap, tick, distCache).length;
    const released = checkBlockedAgents(agentsMap);
    if (released.length) runAuction(grid, agentsMap, released, distCache);
    for (const a of agentsMap.values()) {
      if (a.taskId !== null && a.x === a.goalX && a.y === a.goalY) { completed.add(a.taskId); a.taskId = null; }
    }
    if (completed.size === pickupCells.length) { tick++; break; }
  }
  console.log(`  [9-robot live-style] ticks=${tick} collisions=${totalCollisions} completed=${completed.size}/9`);
  check("9-robot: zero collisions", totalCollisions === 0);
  check("9-robot: all tasks completed", completed.size === pickupCells.length);
}

// ---- test 6: determinism -- same seed (tick sequence) gives identical result ----
{
  const layout = generateLargeLayout();
  function fullRun() {
    const grid = new Grid(layout);
    const startCols = [1,3,5,7,9,11,13,15,2];
    const stagingRow = layout.length - 1;
    const agentsArr = startCols.map((c,i) => makeAgent("R"+(i+1), c, stagingRow, c, stagingRow));
    const agentsMap = new Map(agentsArr.map(a => [a.id, a]));
    const distCache = new DistCache();
    const pickupCells = [[2,0],[12,0],[14,2],[8,2],[0,0],[16,2],[6,0],[4,2],[10,0]];
    let openTasks = pickupCells.map((c,i) => ({taskId: "T"+(i+1), pickupX: c[0], pickupY: c[1]}));
    runAuction(grid, agentsMap, openTasks, distCache);
    let tick = 0, completed = new Set();
    for (; tick < 300; tick++) {
      stepPibt(grid, agentsMap, tick, distCache);
      for (const a of agentsMap.values()) if (a.taskId !== null && a.x === a.goalX && a.y === a.goalY) { completed.add(a.taskId); a.taskId = null; }
      if (completed.size === pickupCells.length) { tick++; break; }
    }
    return tick;
  }
  const t1 = fullRun(), t2 = fullRun();
  check("determinism: repeated runs give identical tick count", t1 === t2);
}

console.log(failures === 0 ? "\nALL CHECKS PASSED" : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
