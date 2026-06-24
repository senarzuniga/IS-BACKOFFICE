"""Digital Twin 2D prototype for Reel Load Simulator.

This engine provides a simple, step-based digital twin with:
- 2D map coordinates (meters)
- Vehicles (forklifts / transfer) with kinematic updates
- Task queue and simple assignment logic
- Collision avoidance (proximity-based) and KPIs derived from real distances/time

Notes:
- The implementation is intentionally lightweight to avoid new dependencies
  while being realistic enough for engineering comparisons.
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SimulationResult:
    sim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    time_min: float = 0.0
    movements: int = 0
    reel_changes: int = 0
    starvation_events: int = 0
    downtime_min: float = 0
    utilization_pct: float = 0.0
    total_distance_m: float = 0.0


@dataclass
class Position:
    x: float
    y: float


class Task:
    def __init__(self, task_id: str, order_id: str, pick: Position, drop: Position):
        self.id = task_id
        self.order_id = order_id
        self.pick = pick
        self.drop = drop
        self.status = "pending"  # pending, assigned, in_progress, done
        self.assigned: Optional[str] = None
        self.created_at: float = 0.0


class Vehicle:
    def __init__(
        self,
        vid: str,
        vtype: str,
        pos: Position,
        speed_m_per_min: float = 80.0,
        capacity: int = 1,
        pick_time: float = 1.0,
        drop_time: float = 1.0,
    ) -> None:
        self.id = vid
        self.type = vtype
        self.pos = pos
        self.speed = float(speed_m_per_min)
        self.capacity = capacity
        self.pick_time = pick_time
        self.drop_time = drop_time
        self.state: str = "idle"  # idle, moving, picking, dropping, waiting, blocked
        self.task: Optional[Task] = None
        self.path: List[Position] = []
        self.time_remaining: float = 0.0
        self.cargo: List[str] = []
        self.distance_moved: float = 0.0

    def assign(self, task: Task, path: List[Position]) -> None:
        self.task = task
        task.assigned = self.id
        task.status = "assigned"
        self.path = path
        self.state = "moving"

    def clear_task(self, mark_done: bool = True) -> None:
        """Clear the current task from the vehicle.

        If `mark_done` is True the task.status will be set to 'done'.
        Otherwise the task.status is left unchanged (useful when engine will
        manage task lifecycle further, e.g. scheduling track processing).
        """
        if self.task:
            if mark_done:
                try:
                    self.task.status = "done"
                except Exception:
                    pass
        self.task = None
        self.path = []
        self.state = "idle"

    def update(self, step_min: float, vehicles: List["Vehicle"], safety_dist: float = 1.0) -> float:
        """Advance vehicle state by step_min (minutes). Returns distance moved (meters)."""
        moved = 0.0
        if self.state == "moving" and self.path:
            target = self.path[0]
            dx = target.x - self.pos.x
            dy = target.y - self.pos.y
            dist = math.hypot(dx, dy)
            max_move = self.speed * step_min
            if dist <= max_move or dist < 1e-6:
                # arrive exactly
                self.pos.x = target.x
                self.pos.y = target.y
                moved = dist
                self.distance_moved += moved
                self.path.pop(0)
                # arrival handling left to engine
            else:
                # tentative move
                ratio = max_move / dist
                new_x = self.pos.x + dx * ratio
                new_y = self.pos.y + dy * ratio

                # simple collision avoidance: check against other vehicles projected positions
                blocked = False
                for v in vehicles:
                    if v.id == self.id:
                        continue
                    # predict other vehicle position (assume they keep current)
                    d_future = math.hypot(new_x - v.pos.x, new_y - v.pos.y)
                    if d_future < safety_dist:
                        blocked = True
                        break

                if blocked:
                    # wait (no movement)
                    self.state = "waiting"
                    moved = 0.0
                else:
                    self.pos.x = new_x
                    self.pos.y = new_y
                    moved = max_move
                    self.distance_moved += moved

        elif self.state in ("picking", "dropping"):
            self.time_remaining = max(0.0, self.time_remaining - step_min)
            if self.time_remaining <= 0.0:
                # finish action
                if self.state == "picking":
                    # carry item
                    if self.task:
                        self.cargo.append(self.task.order_id)
                    # next: move to drop
                    self.state = "moving"
                    # path should already contain drop as remaining
                elif self.state == "dropping":
                    # unload
                    if self.cargo and self.task:
                        try:
                            self.cargo.remove(self.task.order_id)
                        except ValueError:
                            pass
                    # signal to engine that drop has completed; engine will schedule track processing
                    self.just_dropped = True
                    self.state = "idle"
                    self.time_remaining = 0.0

        elif self.state == "waiting":
            # simple retry: return to moving if path still available
            if self.path:
                self.state = "moving"

        return moved


class SimpleMap:
    def __init__(self, width_m: float = 100.0, height_m: float = 40.0):
        self.width = float(width_m)
        self.height = float(height_m)
        # define racks centers (three rows)
        self.racks: List[Position] = [Position(10.0, 8.0), Position(10.0, 20.0), Position(10.0, 32.0)]
        self.exchange = Position(30.0, 20.0)
        # tracks positions (10 lanes)
        self.tracks: List[Position] = []
        x0 = 50.0
        x1 = 85.0
        for i in range(10):
            tx = x0 + (x1 - x0) * (i / 9.0)
            ty = 5.0 + (self.height - 10.0) * ((i % 5) / 4.0)
            self.tracks.append(Position(tx, ty))
        self.corrugadora = Position(95.0, 20.0)
        # conveyor / track parameters (defaults)
        self.conveyor_speed_m_per_s = 1.2  # m/s
        self.conveyor_speed_m_per_min = self.conveyor_speed_m_per_s * 60.0
        self.track_load_time_min = 20.0 / 60.0
        self.track_unload_time_min = 40.0 / 60.0


class SimulationEngine:
    """Digital twin engine.

    Public API maintained: constructor(cfg, orders, scenario), step(step_minutes=1.0), reset(), to_canvas_state(), result
    """

    def __init__(self, cfg: Dict[str, Any], orders: List[Dict[str, Any]], scenario: str = "A", seed: Optional[int] = None) -> None:
        self.cfg = cfg or {}
        self.orders = list(orders) if orders else []
        self.scenario = scenario
        self.time_min = 0.0
        self.result = SimulationResult()

        if seed is not None:
            random.seed(seed)

        # Map and entities
        self.map = SimpleMap(float(self.cfg.get("plant_width_m", 100.0)), float(self.cfg.get("plant_height_m", 40.0)))
        self.vehicles: List[Vehicle] = []
        self.tasks: List[Task] = []

        # statistics
        self.total_work_time = 0.0
        self.total_possible_time = 0.0

        # initialize vehicles
        if self.scenario == "A":
            n = int(self.cfg.get("conventional_num_forklifts", 2))
            for i in range(n):
                # start near warehouse
                start = Position(12.0, 8.0 + i * 10.0)
                # forklift speed: range default 120-210 m/min
                fmin = float(self.cfg.get("forklift_speed_min_m_per_min", 120.0))
                fmax = float(self.cfg.get("forklift_speed_max_m_per_min", 210.0))
                speed = float(self.cfg.get("forklift_speed_m_per_min", random.uniform(fmin, fmax)))
                pick_time_min = float(self.cfg.get("forklift_pick_sec", 30.0)) / 60.0
                drop_time_min = float(self.cfg.get("forklift_drop_sec", 15.0)) / 60.0
                v = Vehicle(f"F{i+1}", "forklift", start, speed_m_per_min=speed, capacity=1, pick_time=pick_time_min, drop_time=drop_time_min)
                self.vehicles.append(v)
        else:
            # single transfer
            start = Position(self.map.exchange.x, self.map.exchange.y)
            t_speed = float(self.cfg.get("ingetrans_transfer_speed", 59.0))
            pick_t = float(self.cfg.get("ingetrans_pick_sec", 6.0)) / 60.0
            drop_t = float(self.cfg.get("ingetrans_drop_sec", 6.0)) / 60.0
            v = Vehicle("T1", "transfer", start, speed_m_per_min=t_speed, capacity=int(self.cfg.get("transfer_capacity", 1)), pick_time=pick_t, drop_time=drop_t)
            self.vehicles.append(v)

        # schedule MTBF/repair times per vehicle
        mtbf_hours = float(self.cfg.get("forklift_mtbf_hours", 100.0))
        mtbf_min = mtbf_hours * 60.0
        mean_repair_min = float(self.cfg.get("mean_repair_min", 30.0))
        for v in self.vehicles:
            v.next_failure_at = float(self.time_min + random.expovariate(1.0 / max(1.0, mtbf_min)))
            v.blocked_until = None
            v.mtbf_min = mtbf_min
            v.mean_repair_min = mean_repair_min
            v.just_dropped = False

        # Build tasks from orders (simple mapping: 1 task per order)
        for idx, wo in enumerate(self.orders):
            order_id = wo.get("id", f"WO-{idx}")
            # choose a rack (round-robin)
            rack = self.map.racks[idx % len(self.map.racks)]
            # choose a track (round-robin)
            track = self.map.tracks[idx % len(self.map.tracks)]
            task = Task(f"TASK-{idx+1}", order_id, pick=Position(rack.x, rack.y), drop=Position(track.x, track.y))
            # defect probability based on config
            defect_rate = float(self.cfg.get("defect_rate", 0.01))
            task.defective = (random.random() < defect_rate)
            self.tasks.append(task)

        # internal counters
        self._completed_tasks = 0

    def reset(self) -> None:
        self.time_min = 0.0
        self.result = SimulationResult()
        self._completed_tasks = 0

    def _assign_tasks(self) -> None:
        """Assign pending tasks to available vehicles.

        - Scenario A: assign nearest idle forklift
        - Scenario B: transfer picks next pending task (FIFO)
        """
        pending = [t for t in self.tasks if t.status == "pending"]
        if not pending:
            return

        if self.scenario == "A":
            # use PathPlanner for more realistic routing
            try:
                from agents.Reel_load_simulator.movement_agent import PathPlanner
                planner = PathPlanner(self.map)
            except Exception:
                planner = None

            for task in pending:
                best: Optional[Tuple[Vehicle, float, List[Position]]] = None
                for v in self.vehicles:
                    if v.state != "idle":
                        continue
                    # estimate time to pick (use planner if available)
                    if planner:
                        p_to_pick = planner.shortest_path(v.pos, task.pick)
                        # compute path length
                        plen = 0.0
                        for a, b in zip(p_to_pick[:-1], p_to_pick[1:]):
                            plen += math.hypot(a.x - b.x, a.y - b.y)
                        eta = plen / max(0.1, v.speed)
                    else:
                        d = math.hypot(v.pos.x - task.pick.x, v.pos.y - task.pick.y)
                        eta = d / max(0.1, v.speed)

                    if best is None or eta < best[1]:
                        best = (v, eta, p_to_pick if planner else [])

                if best:
                    vsel, _, p_to_pick = best
                    if planner and p_to_pick:
                        p_pick_to_drop = planner.shortest_path(task.pick, task.drop)
                        # combine paths avoiding duplication of pick point
                        combined = p_to_pick + p_pick_to_drop[1:]
                    else:
                        combined = [Position(task.pick.x, task.pick.y), Position(self.map.exchange.x, self.map.exchange.y), Position(task.drop.x, task.drop.y)]
                    vsel.assign(task, combined)
                    task.status = "assigned"

        else:
            # transfer: single vehicle
            transfer = self.vehicles[0]
            if transfer.state == "idle" and pending:
                task = pending[0]
                # path: go to pick (exchange in this design), then along rail to drop
                path = [Position(task.pick.x, task.pick.y), Position(task.drop.x, task.drop.y)]
                transfer.assign(task, path)
                task.status = "assigned"

    def step(self, step_minutes: float = 1.0) -> None:
        """Advance simulation by `step_minutes` minutes.

        This method updates vehicles, assigns tasks and computes KPIs.
        """
        # update time
        self.time_min += step_minutes
        self.result.time_min = self.time_min

        # try to assign tasks first
        # check scheduled failures / repairs
        for v in self.vehicles:
            # if blocked and repair time passed
            if getattr(v, "blocked_until", None) is not None and self.time_min >= v.blocked_until:
                v.state = "idle"
                v.blocked_until = None
                # schedule next failure
                v.next_failure_at = float(self.time_min + random.expovariate(1.0 / max(1.0, getattr(v, "mtbf_min", 6000.0))))

            # if not currently blocked and it's time for a failure
            if getattr(v, "blocked_until", None) is None and getattr(v, "next_failure_at", None) is not None and self.time_min >= v.next_failure_at:
                # vehicle fails
                repair = float(max(1.0, random.expovariate(1.0 / max(1.0, getattr(v, "mean_repair_min", 30.0)))))
                v.state = "blocked"
                v.blocked_until = float(self.time_min + repair)
                # account downtime immediately
                self.result.downtime_min += repair

        self._assign_tasks()

        # update each vehicle and aggregate moved distance
        total_moved = 0.0
        for v in self.vehicles:
            # do not move blocked vehicles
            if v.state == "blocked":
                # accumulate downtime
                self.result.downtime_min += step_minutes
                moved = 0.0
            else:
                moved = v.update(step_minutes, self.vehicles, safety_dist=1.0)
            total_moved += moved

            # arrival handling: if vehicle reached waypoint and has task
            if v.state == "moving" and not v.path and v.task:
                # determine whether at pick or drop
                # if not carrying the task order -> we are at pick
                if v.task.order_id not in v.cargo:
                    v.state = "picking"
                    v.time_remaining = v.pick_time
                    v.task.status = "in_progress"
                else:
                    v.state = "dropping"
                    v.time_remaining = v.drop_time

            # if vehicle just finished dropping, schedule track processing
            if getattr(v, "just_dropped", False) and v.task:
                task = v.task
                # find nearest track index to drop point
                try:
                    distances = [math.hypot(tr.x - task.drop.x, tr.y - task.drop.y) for tr in self.map.tracks]
                    track_idx = int(min(range(len(distances)), key=lambda i: distances[i]))
                except Exception:
                    track_idx = 0

                # compute processing time: load + conveyor travel + unload
                d_to_corr = math.hypot(self.map.corrugadora.x - task.drop.x, self.map.corrugadora.y - task.drop.y)
                conveyor_speed = float(getattr(self.map, "conveyor_speed_m_per_min", self.map.conveyor_speed_m_per_min))
                travel_time = d_to_corr / conveyor_speed if conveyor_speed > 0 else 0.0
                load_time = float(getattr(self.map, "track_load_time_min", self.map.track_load_time_min))
                unload_time = float(getattr(self.map, "track_unload_time_min", self.map.track_unload_time_min))
                processing_time = load_time + travel_time + unload_time

                task.status = "processing"
                task.processing_complete_time = float(self.time_min + processing_time)
                task.processing_track_index = track_idx
                # mark track busy
                if not hasattr(self, "tracks_busy_until"):
                    self.tracks_busy_until = [None] * len(self.map.tracks)
                self.tracks_busy_until[track_idx] = task.processing_complete_time

                # clear vehicle assignment (do not mark task done here)
                v.clear_task(mark_done=False)
                v.just_dropped = False

            # if vehicle finished drop and task cleared, count movement
            if v.state == "idle" and v.task is None and v.distance_moved > 0:
                # a completed task increments movements
                self._completed_tasks += 1
                v.distance_moved = 0.0

        # Update KPIs
        # finalize processing tasks whose time has elapsed
        for t in self.tasks:
            if t.status == "processing" and getattr(t, "processing_complete_time", float("inf")) <= self.time_min:
                t.status = "done"
                self._completed_tasks += 1
                ti = getattr(t, "processing_track_index", None)
                if ti is not None and hasattr(self, "tracks_busy_until") and ti < len(self.tracks_busy_until):
                    # free track
                    if self.tracks_busy_until[ti] is not None and self.tracks_busy_until[ti] <= self.time_min:
                        self.tracks_busy_until[ti] = None

        self.result.total_distance_m += total_moved
        self.result.movements = self._completed_tasks

        # simple reel change logic: every N completed tasks at corrugadora -> reel change
        if self._completed_tasks > 0 and self._completed_tasks % max(1, int(self.cfg.get("reels_per_change", 5))) == 0:
            self.result.reel_changes += 1

        # starvation: if tasks queue empty but corrugadora requires feed -> event
        if not any(t.status in ("pending", "assigned", "in_progress") for t in self.tasks) and random.random() < 0.01:
            self.result.starvation_events += 1

        # downtime random events based on MTBF
        if random.random() < 0.001:
            self.result.downtime_min += int(max(1, random.gauss(5, 2)))

        # utilization: fraction of vehicles active
        active = sum(1 for v in self.vehicles if v.state not in ("idle", "waiting"))
        self.result.utilization_pct = round(100.0 * (active / max(1, len(self.vehicles))), 1)

    def to_canvas_state(self) -> Dict[str, Any]:
        """Return simplified state for visualization (normalized coords 0..100)."""
        state: Dict[str, Any] = {
            "scenario": self.scenario,
            "time_min": self.time_min,
            "metrics": self.result.__dict__,
            "orders": [dict(o) for o in self.orders],
        }

        # normalize positions to 0..100
        def norm(p: Position) -> Dict[str, float]:
            return {"x": (p.x / self.map.width) * 100.0, "y": (p.y / self.map.height) * 100.0}

        state["racks"] = [0 for _ in self.map.racks]
        state["tracks"] = [{"id": f"T{i+1}", "occupied": False} for i in range(len(self.map.tracks))]

        # vehicles
        vehs = []
        for v in self.vehicles:
            vehs.append({"id": v.id, "type": v.type, "pos": norm(v.pos), "state": v.state, "carrying": list(v.cargo)})
        state["vehicles"] = vehs

        # Compatibility: provide `forklifts` (list of dicts) and `transfer` for existing canvas code
        if self.scenario == "A":
            forklifts = []
            for v in self.vehicles:
                if v.type == "forklift":
                    p = norm(v.pos)
                    forklifts.append({"id": v.id, "x": p["x"], "y": p["y"], "carrying": bool(v.cargo), "state": v.state})
            state["forklifts"] = forklifts
        else:
            # transfer: use x coordinate as pos 0..100 and show carrying
            tr = None
            for v in self.vehicles:
                if v.type == "transfer":
                    p = norm(v.pos)
                    tr = {"pos": p["x"], "carrying": list(v.cargo), "state": v.state}
                    break
            state["transfer"] = tr or {"pos": 30.0, "carrying": [], "state": "idle"}

        # tracks occupancy: mark track occupied if any task drop equals its coords and status in progress/assigned
        for t in self.tasks:
            if t.status in ("assigned", "in_progress"):
                for i, tr in enumerate(self.map.tracks):
                    if abs(tr.x - t.drop.x) < 0.1 and abs(tr.y - t.drop.y) < 0.1:
                        state["tracks"][i]["occupied"] = True

        return state

    
