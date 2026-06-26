"""
CorrugatorEngine: motor principal de simulación con consumo continuo.

Modelo de flujo continuo y recursos diferenciados entre FORKLIFT (humano)
y INGETRANS (automático).
"""
from dataclasses import dataclass
import heapq
import random
from typing import List, Dict, Optional

from .consumption_model import ConsumptionModel
from .materials_flow import MaterialsFlow, Reel
from .starvation_detector import StarvationDetector
from .human_factors import HumanFactors


@dataclass
class ResourceBase:
    id: str
    state: str = "idle"
    speed: float = 1.0
    loaded: bool = False
    current_order: Optional[str] = None
    block_until: float = 0.0
    moving_time: float = 0.0
    handling_time: float = 0.0
    distance: float = 0.0


class CorrugatorEngine:
    def __init__(self, scenario: str, config: Dict = None, seed: int = None):
        config = config or {}
        self.scenario = scenario  # 'A' (forklift) or 'B' (ingetrans)
        self.config = config
        self.rng = random.Random(seed)
        self.time = 0.0
        self.dt = float(config.get("dt_min", 0.1))
        self.running = False

        # models
        self.consumption = ConsumptionModel(config)
        self.flow = MaterialsFlow(config)
        self.starvation = StarvationDetector()

        self.human = HumanFactors(config, self.rng) if scenario == "A" else None

        # corrugator state
        self.current_stand = "stand_1"
        self.current_reel_weight = float(config.get("initial_reel_weight_kg", self.consumption.reel_weight_kg))
        self.current_reel_type = config.get("initial_reel_type", "Kraft 150")
        self.meters_produced = 0.0
        self.meters_theoretical = 0.0

        # resources
        self.resources: List[ResourceBase] = self._init_resources()
        self.tracks = self._init_tracks()

        # queues and orders
        self.queue: List[Dict] = []
        self.active_orders: Dict[str, Dict] = {}
        self.completed_orders: List[Dict] = []

        # metrics
        self.metrics = {
            "meters_produced": 0.0,
            "reels_changed": 0,
            "starvation_events": 0,
            "starvation_time": 0.0,
            "reels_delivered": 0,
            "reels_returned": 0,
            "changeovers": 0,
            "operator_wait_time": 0.0,
            "total_distance_m": 0.0,
            "downtime_min": 0.0,
        }

        self.event_log: List[Dict] = []
        self.history: List[Dict] = []

        # event queue
        self.event_queue: List = []

        # schedule initial events
        self._schedule_initial_events()

    def _init_resources(self) -> List[ResourceBase]:
        if self.scenario == "A":
            num = int(self.config.get("num_forklifts", 1))
            resources = []
            for i in range(num):
                resources.append(ResourceBase(id=f"FL-{i+1}", speed=float(self.config.get("forklift_speed_loaded", 60.0))))
            return resources
        else:
            # INGETRANS automatic transfer
            return [ResourceBase(id="INGETRANS-1", speed=float(self.config.get("transfer_speed", 80.0)))]

    def _init_tracks(self) -> List[Dict]:
        tracks = []
        num_tracks = int(self.config.get("num_tracks", 10))
        for i in range(num_tracks):
            stand = (i // 2) + 1
            tracks.append({
                "id": f"T{i+1}",
                "stand": f"stand_{stand}",
                "occupied": False,
                "reel_weight": 0.0,
                "reel_type": None,
                "order_id": None,
            })
        return tracks

    def _schedule_initial_events(self):
        if self.scenario == "A" and self.human:
            self.schedule_event("shift_change", self.human.shift_interval)
            self.schedule_event("operator_break", self.human.operator_break_interval)

        # initial reel depletion event
        life = self.consumption.calculate_reel_life(self.current_reel_weight)
        self.schedule_event("reel_depleted", life)

    def schedule_event(self, event_type: str, delay_min: float, **kwargs):
        event_time = self.time + float(delay_min)
        heapq.heappush(self.event_queue, (event_time, event_type, kwargs))

    def step(self):
        if not self.running:
            return

        # process scheduled events up to time + dt
        while self.event_queue and self.event_queue[0][0] <= self.time + self.dt:
            event_time, event_type, kwargs = heapq.heappop(self.event_queue)
            # advance to event time
            self.time = event_time
            self._process_event(event_type, kwargs)

        # advance time by dt
        self.time += self.dt

        # 1. Consume paper
        meters = self.consumption.calculate_consumption(self.dt)
        self.meters_produced += meters
        self.meters_theoretical += self.consumption.corrugator_speed_m_min * self.dt

        # 2. Reduce current reel weight
        kg_per_m = self.consumption.kg_per_meter()
        consumed_kg = meters * kg_per_m
        self.current_reel_weight -= consumed_kg

        # 3. Starvation check
        starving = self.starvation.check_starvation(self.current_reel_weight, self.dt)
        if starving:
            self.metrics["starvation_time"] += self.dt

        # 4. If reel depleted, request change
        if self.consumption.is_reel_depleted(self.current_reel_weight):
            self._request_reel_change()

        # 5. update resources
        self._update_resources()

        # 6. metrics
        self.metrics["meters_produced"] = self.meters_produced

        # 7. snapshot
        self.history.append(self.get_snapshot())

    def _process_event(self, event_type: str, kwargs: Dict):
        if event_type == "reel_depleted":
            self._request_reel_change()
        elif event_type == "shift_change" and self.human:
            self.metrics["downtime_min"] += self.human.shift_duration
            self.event_log.append({"time": self.time, "type": "shift_change"})
            self.schedule_event("shift_change", self.human.shift_interval)
        elif event_type == "operator_break" and self.human:
            self.metrics["downtime_min"] += self.human.operator_break_duration
            self.event_log.append({"time": self.time, "type": "operator_break"})
            self.schedule_event("operator_break", self.human.operator_break_interval)
        elif event_type == "reel_delivered":
            track_id = kwargs.get("track_id")
            reel = kwargs.get("reel")
            self._deliver_reel_to_track(track_id, reel)
        elif event_type == "reel_returned":
            track_id = kwargs.get("track_id")
            self._return_reel(track_id)

    def _request_reel_change(self):
        track = self._find_available_track()
        if track:
            self.metrics["reels_changed"] += 1
            self.metrics["changeovers"] += 1
            # load reel from track
            self.current_reel_weight = track["reel_weight"]
            self.current_reel_type = track["reel_type"]
            track["occupied"] = False
            # request new reel to fill the track
            self._request_new_reel(track["id"])
        else:
            # If no pre-loaded track has a usable reel, try to request a
            # replacement to an empty track (real plants pre-fill tracks).
            empty_track = None
            for t in self.tracks:
                if not t.get("occupied"):
                    empty_track = t
                    break
            if empty_track is not None:
                # create a request to deliver a reel to this empty track
                self._request_new_reel(empty_track["id"])
                return

            # starvation: no reel available immediately
            if not self.starvation.is_starving:
                self.event_log.append({"time": self.time, "type": "starvation_start"})
            self.starvation.is_starving = True

    def _find_available_track(self) -> Optional[Dict]:
        for track in self.tracks:
            if track["occupied"] and track["reel_weight"] > self.consumption.min_reel_weight_kg:
                return track
        return None

    def _request_new_reel(self, track_id: str):
        order = {
            "id": f"REQ-{len(self.completed_orders)+1}",
            "track_id": track_id,
            "reel_type": self.current_reel_type,
            "created_at": self.time,
            "status": "pending",
        }
        self.queue.append(order)
        self._assign_task()

    def _assign_task(self):
        if not self.queue:
            return

        free_resource = None
        for r in self.resources:
            if r.state == "idle" and r.block_until <= self.time:
                free_resource = r
                break

        if not free_resource:
            return

        order = self.queue.pop(0)
        order["status"] = "in_progress"

        # movement time depends on scenario
        if self.scenario == "A" and self.human:
            # human variability: normal noise around delivery time
            search_time = self.human.get_search_time()
            traffic_delay = self.human.get_traffic_delay()
            base_delivery = 2.0 + search_time + traffic_delay
            noise = self.rng.normalvariate(0, 0.3)
            delivery_time = max(0.1, base_delivery + noise)
            free_resource.handling_time += delivery_time
            free_resource.distance += 50.0
        else:
            base_delivery = 1.0
            noise = self.rng.normalvariate(0, 0.05)
            delivery_time = max(0.05, base_delivery + noise)
            free_resource.handling_time += delivery_time
            free_resource.distance += 30.0

        free_resource.state = "handling"
        free_resource.current_order = order["id"]

        # schedule delivery event
        self.schedule_event("reel_delivered", delivery_time, track_id=order["track_id"], reel=Reel(id=order["id"], weight=self.consumption.reel_weight_kg, type=order["reel_type"], location="in_transit", order_id=order["id"]))

    def _deliver_reel_to_track(self, track_id: str, reel: Reel):
        for track in self.tracks:
            if track["id"] == track_id:
                track["occupied"] = True
                track["reel_weight"] = reel.weight
                track["reel_type"] = reel.type
                track["order_id"] = reel.order_id
                self.metrics["reels_delivered"] += 1
                break

        # free resource that had this order
        for r in self.resources:
            if r.current_order == reel.order_id:
                r.state = "idle"
                r.current_order = None
                r.loaded = False
                break

    def _return_reel(self, track_id: str):
        for track in self.tracks:
            if track["id"] == track_id:
                if track["reel_weight"] < self.consumption.min_reel_weight_kg:
                    self.flow.return_reel(Reel(id=f"RET-{len(self.flow.returned)+1}", weight=track["reel_weight"], type=track["reel_type"], location="returned", is_partial=True))
                    self.metrics["reels_returned"] += 1
                    track["occupied"] = False
                # also attempt to move partial reels via materials_flow API
                try:
                    self.flow.return_partial_reel(track["id"])
                except Exception:
                    pass
                break

    def _update_resources(self):
        for r in self.resources:
            if r.state == "handling" and r.block_until > 0:
                r.block_until -= self.dt
                if r.block_until <= 0:
                    r.state = "idle"
                    r.block_until = 0

    def get_kpis(self) -> Dict:
        t_h = self.time / 60.0 if self.time > 0 else 1.0
        availability = 1.0 - (self.metrics["starvation_time"] / max(1.0, self.time))
        performance = self.meters_produced / max(1.0, self.meters_theoretical)
        quality = 0.98
        oee = availability * performance * quality

        return {
            "oee": oee * 100,
            "availability": availability * 100,
            "performance": performance * 100,
            "quality": quality * 100,
            "meters_produced": self.meters_produced,
            "meters_theoretical": self.meters_theoretical,
            "reels_changed": self.metrics["reels_changed"],
            "starvation_events": self.starvation.starvation_events,
            "starvation_time": self.metrics["starvation_time"],
            "reels_delivered": self.metrics["reels_delivered"],
            "reels_returned": self.metrics["reels_returned"],
            "downtime_min": self.metrics["downtime_min"],
            "changeovers": self.metrics["changeovers"],
            "utilization": self._calculate_utilization(),
        }

    def _calculate_utilization(self) -> float:
        total_time = self.time if self.time > 0 else 1.0
        busy_time = sum(r.moving_time + r.handling_time for r in self.resources)
        return (busy_time / (len(self.resources) * total_time)) * 100

    def get_snapshot(self) -> Dict:
        return {
            "time": self.time,
            "scenario": self.scenario,
            "resources": [
                {"id": r.id, "state": r.state, "loaded": r.loaded, "current_order": r.current_order} for r in self.resources
            ],
            "tracks": self.tracks,
            "queue_length": len(self.queue),
            "current_reel_weight": self.current_reel_weight,
            "meters_produced": self.meters_produced,
            "starvation": self.starvation.is_starving,
        }

    def run(self, duration_min: float):
        self.running = True
        target = self.time + duration_min
        while self.time < target and self.running:
            self.step()

    def stop(self):
        self.running = False
