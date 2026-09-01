from fleet.grid import WarehouseGrid
from fleet.planning.astar import astar


def test_finds_path_on_default_layout():
    grid = WarehouseGrid.default()
    path = astar(grid, (0, 0), (9, 8))
    assert path, "expected a non-empty path on the default layout"
    assert path[0] == (0, 0)
    assert path[-1] == (9, 8)


def test_path_never_crosses_obstacles():
    grid = WarehouseGrid.default()
    path = astar(grid, (0, 0), (9, 8))
    for cell in path:
        assert grid.is_free(cell), f"path crosses an obstacle at {cell}"


def test_path_is_stepwise_connected():
    grid = WarehouseGrid.default()
    path = astar(grid, (0, 0), (9, 4))
    for a, b in zip(path, path[1:]):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        assert (dx, dy) in {(1, 0), (0, 1)}, f"non-adjacent step {a} -> {b}"


def test_unreachable_goal_returns_empty():
    grid = WarehouseGrid.default()
    path = astar(grid, (0, 0), (999, 999))
    assert path == []


def test_same_cell_start_goal():
    grid = WarehouseGrid.default()
    path = astar(grid, (2, 2), (2, 2))
    assert path == [(2, 2)]
