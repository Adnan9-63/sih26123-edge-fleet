"use strict";
/*
 * JS port of src/fleet/{grid,agent,planning/pibt,allocation/auction}.py
 *
 * This mirrors the tested Python implementation's LOGIC as closely as
 * possible -- same PIBT algorithm structure (priority inheritance +
 * backtracking, two-mode candidate ordering, BFS distance not Manhattan,
 * blocked_ticks freezing at goal, tick-varying tie-break jitter), same
 * auction bidding formula. It exists ONLY to drive the live in-browser
 * demo -- the Python version remains the tested, authoritative
 * implementation behind every benchmark number and PPT claim. Every
 * behavior here was re-verified independently in Node (see
 * verify_js_port.js) against the same scenarios the Python test suite
 * covers, precisely because a second implementation that silently
 * diverges from the tested one would be worse than no live demo at all.
 */

// ---------- grid ----------

function generateLargeLayout(numShelfCols = 8, shelfRows = 9, crossAisleEvery = 4, stagingRows = 2) {
  const width = numShelfCols * 2 + 1;
  const rows = [];
  for (let r = 0; r < shelfRows; r++) {
    if (r % crossAisleEvery === crossAisleEvery - 1) {
      rows.push("0".repeat(width));
    } else {
      let row = "";
      for (let c = 0; c < width; c++) row += (c % 2 === 1) ? "1" : "0";
      rows.push(row);
    }
  }
  for (let i = 0; i < stagingRows; i++) rows.push("0".repeat(width));
  return rows;
}

class Grid {
  constructor(layout) {
    this.layout = layout;
    this.width = layout[0].length;
    this.height = layout.length;
    this.blockedCells = new Set();
    this.version = 0;
  }
  key(x, y) { return x + "," + y; }
  isFree(x, y) {
    if (x < 0 || x >= this.width || y < 0 || y >= this.height) return false;
    if (this.blockedCells.has(this.key(x, y))) return false;
    return this.layout[y][x] !== "1";
  }
  neighbors(x, y) {
    const out = [];
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = x + dx, ny = y + dy;
      if (this.isFree(nx, ny)) out.push([nx, ny]);
    }
    return out;
  }
  blockCell(x, y) { this.blockedCells.add(this.key(x, y)); this.version++; }
  unblockCell(x, y) { this.blockedCells.delete(this.key(x, y)); this.version++; }
  bfsDistances(goalX, goalY) {
    const dist = new Map();
    const startKey = this.key(goalX, goalY);
    dist.set(startKey, 0);
    const q = [[goalX, goalY]];
    let qi = 0;
    while (qi < q.length) {
      const [cx, cy] = q[qi++];
      const d = dist.get(this.key(cx, cy));
      for (const [nx, ny] of this.neighbors(cx, cy)) {
        const k = this.key(nx, ny);
        if (!dist.has(k)) { dist.set(k, d + 1); q.push([nx, ny]); }
      }
    }
    return dist;
  }
}

// ---------- agent ----------

function makeAgent(id, x, y, goalX, goalY) {
  return { id, x, y, goalX, goalY, battery: 100.0, taskId: null, blockedTicks: 0 };
}

// ---------- PIBT ----------

// Deterministic tie-break -- mirrors pibt.py's _stable_jitter (crc32,
// specifically NOT relying on any per-process-random hash). Simple
// FNV-1a: deterministic across runs/browsers, which is what matters here
// -- reproducibility of "the same seed gives the same run", not
// cryptographic quality.
function stableJitter(agentId, tick) {
  const s = agentId + "-" + tick;
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0) % 997;
}

class DistCache {
  constructor() { this.cache = new Map(); }
  get(grid, goalX, goalY) {
    const key = goalX + "," + goalY + "@" + grid.version;
    if (!this.cache.has(key)) this.cache.set(key, grid.bfsDistances(goalX, goalY));
    return this.cache.get(key);
  }
  distTo(grid, x, y, goalX, goalY) {
    const d = this.get(grid, goalX, goalY);
    const v = d.get(x + "," + y);
    return v === undefined ? 1e6 : v;
  }
}

// planStep: mirrors planning/pibt.py's plan_step exactly, including both
// bug-fix behaviors (fair own-turn ranking incl. "stay"; being-displaced
// ranking forces "stay" last) and the swap guard.
function planStep(grid, agents, tick, distCache) {
  const occupancy = new Map();
  for (const a of agents.values()) occupancy.set(a.x + "," + a.y, a.id);

  const decided = new Map();
  const reservedBy = new Map();
  const inProgress = new Set();

  const order = [...agents.keys()].sort((a, b) => {
    const pa = agents.get(a), pb = agents.get(b);
    if (pb.blockedTicks !== pa.blockedTicks) return pb.blockedTicks - pa.blockedTicks;
    const ja = stableJitter(a, tick), jb = stableJitter(b, tick);
    if (ja !== jb) return ja - jb;
    return a < b ? -1 : 1;
  });

  function candidates(agent, beingDisplaced) {
    const nbrs = grid.neighbors(agent.x, agent.y)
      .sort((p, q) => {
        const dp = distCache.distTo(grid, p[0], p[1], agent.goalX, agent.goalY);
        const dq = distCache.distTo(grid, q[0], q[1], agent.goalX, agent.goalY);
        if (dp !== dq) return dp - dq;
        if (p[0] !== q[0]) return p[0] - q[0];
        return p[1] - q[1];
      });
    if (beingDisplaced) return [...nbrs, [agent.x, agent.y]];
    const all = [...nbrs, [agent.x, agent.y]];
    all.sort((p, q) => {
      const dp = distCache.distTo(grid, p[0], p[1], agent.goalX, agent.goalY);
      const dq = distCache.distTo(grid, q[0], q[1], agent.goalX, agent.goalY);
      if (dp !== dq) return dp - dq;
      if (p[0] !== q[0]) return p[0] - q[0];
      return p[1] - q[1];
    });
    return all;
  }

  function pibt(agentId, beingDisplaced) {
    if (decided.has(agentId)) return true;
    if (inProgress.has(agentId)) return false;
    inProgress.add(agentId);
    const agent = agents.get(agentId);

    for (const [cx, cy] of candidates(agent, beingDisplaced)) {
      const cellKey = cx + "," + cy;
      if (reservedBy.has(cellKey) && reservedBy.get(cellKey) !== agentId) continue;

      const occupantId = occupancy.get(cellKey);
      if (occupantId !== undefined && occupantId !== agentId) {
        if (!decided.has(occupantId)) {
          if (!pibt(occupantId, true)) continue;
        }
        const occDecided = decided.get(occupantId);
        if (occDecided && occDecided[0] === cx && occDecided[1] === cy) continue;
        if (occDecided && occDecided[0] === agent.x && occDecided[1] === agent.y) continue;
      }

      decided.set(agentId, [cx, cy]);
      reservedBy.set(cellKey, agentId);
      inProgress.delete(agentId);
      return true;
    }
    inProgress.delete(agentId);
    return false;
  }

  for (const agentId of order) if (!decided.has(agentId)) pibt(agentId, false);

  for (const agentId of agents.keys()) {
    if (!decided.has(agentId)) {
      const a = agents.get(agentId);
      decided.set(agentId, [a.x, a.y]);
    }
  }
  return decided;
}

// ---------- auction ----------

function bid(grid, distCache, agent, task) {
  const dist = distCache.distTo(grid, agent.x, agent.y, task.pickupX, task.pickupY);
  const batteryPenalty = (100.0 - agent.battery) * 0.05;
  return dist + batteryPenalty;
}

function runAuction(grid, agents, openTasks, distCache) {
  const idle = [...agents.values()].filter(a => a.taskId === null);
  const stillOpen = [];
  for (const task of openTasks) {
    if (idle.length === 0) { stillOpen.push(task); continue; }
    let best = idle[0], bestBid = bid(grid, distCache, idle[0], task);
    for (let i = 1; i < idle.length; i++) {
      const b = bid(grid, distCache, idle[i], task);
      if (b < bestBid) { best = idle[i]; bestBid = b; }
    }
    best.taskId = task.taskId;
    best.goalX = task.pickupX; best.goalY = task.pickupY;
    best.blockedTicks = 0;
    idle.splice(idle.indexOf(best), 1);
  }
  return stillOpen;
}

function checkBlockedAgents(agents, threshold = 5) {
  const released = [];
  for (const a of agents.values()) {
    if (a.taskId !== null && a.blockedTicks >= threshold) {
      released.push({ taskId: a.taskId, pickupX: a.goalX, pickupY: a.goalY });
      a.taskId = null; a.goalX = a.x; a.goalY = a.y; a.blockedTicks = 0;
    }
  }
  return released;
}

// ---------- engine tick ----------

function stepPibt(grid, agents, tick, distCache) {
  const decided = planStep(grid, agents, tick, distCache);
  const collisions = [];
  const seen = new Map();
  for (const [id, [x, y]] of decided) {
    const k = x + "," + y;
    if (seen.has(k)) collisions.push([seen.get(k), id]);
    else seen.set(k, id);
  }
  for (const [id, [x, y]] of decided) {
    const a = agents.get(id);
    const moved = (x !== a.x || y !== a.y);
    a.x = x; a.y = y;
    a.battery = Math.max(0, a.battery - (moved ? 0.08 : 0.02));
    const atGoal = (a.x === a.goalX && a.y === a.goalY);
    if (atGoal) a.blockedTicks = 0;
    else if (moved) a.blockedTicks = 0;
    else a.blockedTicks += 1;
  }
  return collisions;
}

if (typeof module !== "undefined") {
  module.exports = {
    generateLargeLayout, Grid, makeAgent, DistCache, planStep, stableJitter,
    bid, runAuction, checkBlockedAgents, stepPibt,
  };
}
