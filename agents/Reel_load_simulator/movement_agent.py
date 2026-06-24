"""Movement / Path planning agent for Reel Load Simulator.

Provides a simple graph-based planner (Dijkstra) over logical nodes: racks,
exchange, tracks and corrugadora. The planner returns a list of `Position`
waypoints that the `SimulationEngine` can follow.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple, Any




class PathPlanner:
    def __init__(self, plant_map: Any):
        # plant_map is expected to have attributes: racks, exchange, tracks, corrugadora
        self.map = plant_map
        # Build node list: racks, exchange, tracks, corrugadora
        self.nodes: List[Position] = []
        self.node_names: List[str] = []
        for i, r in enumerate(self.map.racks):
            self.nodes.append(r)
            self.node_names.append(f"R{i}")
        self.nodes.append(self.map.exchange)
        self.node_names.append("EXCHANGE")
        for i, t in enumerate(self.map.tracks):
            self.nodes.append(t)
            self.node_names.append(f"T{i}")
        self.nodes.append(self.map.corrugadora)
        self.node_names.append("CORRUGADORA")

        # Precompute adjacency (fully connect sensible neighbors)
        self.adj: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(len(self.nodes))}
        self._build_adjacency()

    def _dist(self, a: Any, b: Any) -> float:
        ax = a.x if hasattr(a, "x") else (a[0] if isinstance(a, (list, tuple)) else 0.0)
        ay = a.y if hasattr(a, "y") else (a[1] if isinstance(a, (list, tuple)) else 0.0)
        bx = b.x if hasattr(b, "x") else (b[0] if isinstance(b, (list, tuple)) else 0.0)
        by = b.y if hasattr(b, "y") else (b[1] if isinstance(b, (list, tuple)) else 0.0)
        return math.hypot(ax - bx, ay - by)

    def _build_adjacency(self) -> None:
        n = len(self.nodes)
        # connect racks -> exchange
        exchange_idx = len(self.map.racks)
        for i in range(len(self.map.racks)):
            d = self._dist(self.nodes[i], self.nodes[exchange_idx])
            self.adj[i].append((exchange_idx, d))
            self.adj[exchange_idx].append((i, d))

        # exchange -> tracks
        track_start = exchange_idx + 1
        for i in range(track_start, track_start + len(self.map.tracks)):
            d = self._dist(self.nodes[exchange_idx], self.nodes[i])
            self.adj[exchange_idx].append((i, d))
            self.adj[i].append((exchange_idx, d))

        # tracks -> corrugadora
        corr_idx = len(self.nodes) - 1
        for i in range(track_start, track_start + len(self.map.tracks)):
            d = self._dist(self.nodes[i], self.nodes[corr_idx])
            self.adj[i].append((corr_idx, d))
            self.adj[corr_idx].append((i, d))

    def _nearest_node_index(self, pos: Any) -> int:
        best_i = 0
        best_d = float("inf")
        for i, n in enumerate(self.nodes):
            d = self._dist(pos, n)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    def shortest_path(self, start: Any, goal: Any) -> List[Any]:
        """Return a list of Positions from start to goal using logical nodes.

        Strategy:
        - Find nearest node to start and goal
        - Run Dijkstra on node graph
        - Return concatenated path: start -> node path -> goal
        """
        import heapq

        si = self._nearest_node_index(start)
        gi = self._nearest_node_index(goal)

        # Dijkstra
        dist = {i: float("inf") for i in range(len(self.nodes))}
        prev: Dict[int, int] = {}
        dist[si] = 0.0
        pq: List[Tuple[float, int]] = [(0.0, si)]
        while pq:
            dcur, u = heapq.heappop(pq)
            if dcur > dist[u]:
                continue
            if u == gi:
                break
            for v, w in self.adj.get(u, []):
                nd = dcur + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        # Reconstruct path
        path_nodes: List[Position] = []
        if gi in prev or gi == si:
            cur = gi
            node_path = []
            while cur != si:
                node_path.append(self.nodes[cur])
                cur = prev[cur]
            node_path.append(self.nodes[si])
            node_path.reverse()
            path_nodes = node_path
        else:
            # fallback direct
            path_nodes = [self.nodes[si], self.nodes[gi]]

        # build full path: start -> nodes -> goal
        # build full path: start -> nodes -> goal (use simple objects with x,y)
        out: List[Any] = [type(start)(start.x, start.y) if hasattr(start, "x") else start]
        out.extend([type(n)(n.x, n.y) for n in path_nodes])
        out.append(type(goal)(goal.x, goal.y) if hasattr(goal, "x") else goal)
        return out
