import heapq
import random
from typing import Any, Dict, List

from .roll_stand import RollStand
from .track_state import TrackState
from .predictive_logic import should_pre_reserve, predict_arrival_time
from .reactive_logic import reactive_arrival_time


class CorrugatorEngineV3:
    def __init__(self, config: Dict[str, Any] = None, scenario: str = "A", seed: int = 42):
        self.config = config or {}
        self.scenario = scenario  # 'A' = Forklift (reactive), 'B' = INGETRANS (predictive)
        self.rng = random.Random(seed)

        self.num_roll_stands = int(self.config.get("num_roll_stands", 5))
        self.tracks_per_roll_stand = int(self.config.get("tracks_per_roll_stand", 2))
        self.num_tracks = int(self.config.get("num_tracks", 10))
        self.corrugator_speed = float(self.config.get("corrugator_avg_speed", 220.0))
        self.avg_reel_length = float(self.config.get("avg_reel_length", 5000.0))

        # initialise roll stands
        self.roll_stands: List[RollStand] = [RollStand(i, self.avg_reel_length, self.corrugator_speed) for i in range(self.num_roll_stands)]

        # initialise tracks
        self.tracks: List[Dict[str, Any]] = []
        for i in range(self.num_tracks):
            self.tracks.append({"id": i, "state": TrackState.EMPTY, "reel": None, "reserved_for": None})

        # event queue (min-heap by event time)
        self.event_queue: List[tuple] = []  # (time_min, event_counter, event_dict)
        self._ev_counter = 0

        # simulation time
        self.time = 0.0

        # metrics
        self.metrics = {
            "production_meters": 0.0,
            "starvation_count": 0,
            "deliveries_scheduled": 0,
            "deliveries_successful": 0,
        }

    def _push_event(self, time_min: float, ev: Dict[str, Any]):
        heapq.heappush(self.event_queue, (time_min, self._ev_counter, ev))
        self._ev_counter += 1

    def pending_deliveries_count(self) -> int:
        return sum(1 for (t, c, ev) in self.event_queue if ev.get("type") == "arrival_exchange")

    def theoretical_max_production(self) -> float:
        # use current simulated time as period
        return self.corrugator_speed * max(self.time, 1.0) * max(len(self.roll_stands), 1)

    def find_empty_track(self):
        for t in self.tracks:
            if t["state"] == TrackState.EMPTY:
                return t
        return None

    def schedule_delivery_for_stand(self, stand_idx: int, arrival_time_min: float):
        track = self.find_empty_track()
        if track is None:
            # no empty track; try to find RESERVED or RETURN_PENDING - then queue and mark blocked
            return False
        track["state"] = TrackState.RESERVED
        track["reserved_for"] = stand_idx
        self.metrics["deliveries_scheduled"] += 1
        # schedule arrival to exchange
        ev = {"type": "arrival_exchange", "stand": stand_idx, "track": track["id"]}
        self._push_event(arrival_time_min, ev)
        return True

    def _process_event(self, ev: Dict[str, Any]):
        ev_type = ev.get("type")
        if ev_type == "arrival_exchange":
            track_id = ev.get("track")
            stand_idx = ev.get("stand")
            track = self.tracks[track_id]
            track["state"] = TrackState.DELIVERING
            # schedule transfer to stand shortly after arrival
            transfer_delay = float(self.config.get("transfer_dropoff_reel", 6.0)) / 60.0
            self._push_event(self.time + transfer_delay, {"type": "transfer_to_stand", "stand": stand_idx, "track": track_id})
        elif ev_type == "transfer_to_stand":
            track_id = ev.get("track")
            stand_idx = ev.get("stand")
            track = self.tracks[track_id]
            track["state"] = TrackState.FULL
            # transfer reel to stand
            self.roll_stands[stand_idx].install_new_reel(self.avg_reel_length)
            self.metrics["deliveries_successful"] += 1
            track["state"] = TrackState.CONSUMING
            # schedule return pending -> empty
            return_delay = float(self.config.get("exchange_to_track_return", 7.0)) / 60.0
            self._push_event(self.time + return_delay, {"type": "return_pending", "track": track_id})
        elif ev_type == "return_pending":
            track_id = ev.get("track")
            track = self.tracks[track_id]
            track["state"] = TrackState.RETURN_PENDING
            # set empty shortly after
            self._push_event(self.time + 0.1, {"type": "empty_track", "track": track_id})
        elif ev_type == "empty_track":
            track_id = ev.get("track")
            track = self.tracks[track_id]
            track["state"] = TrackState.EMPTY
            track["reserved_for"] = None

    def step(self, dt_min: float = 1.0):
        # check predictive reservations first
        for i, stand in enumerate(self.roll_stands):
            if self.scenario == "B":
                # predictive: if we should pre-reserve and no pending delivery for that stand
                pending_for_stand = any(ev for (t, c, ev) in self.event_queue if ev.get("stand") == i)
                if should_pre_reserve(stand, self.config) and not pending_for_stand:
                    arrival = predict_arrival_time(self.time, self.config, self.rng)
                    self.schedule_delivery_for_stand(i, arrival)
            else:
                # reactive: only request when below 10%
                if stand.needs_reel(threshold_fraction=0.1):
                    pending_for_stand = any(ev for (t, c, ev) in self.event_queue if ev.get("stand") == i)
                    if not pending_for_stand:
                        arrival = reactive_arrival_time(self.time, self.config, self.rng)
                        self.schedule_delivery_for_stand(i, arrival)

        # advance time and production
        self.time += dt_min

        # process events up to current time
        while self.event_queue and self.event_queue[0][0] <= self.time:
            _, _, ev = heapq.heappop(self.event_queue)
            self._process_event(ev)


        # consumption (detect depletion within the time-step)
        produced = 0.0
        for stand in self.roll_stands:
            # record previous minimum remaining to detect if depletion happened during this step
            prev_min = min((layer.remaining_m for layer in stand.layers), default=0.0)
            consumed = stand.consume(dt_min)
            produced += consumed
            post_min = min((layer.remaining_m for layer in stand.layers), default=0.0)
            # if we crossed from >0 to <=0 within this step, that's a starvation occurrence
            if prev_min > 0.0 and post_min <= 0.0:
                self.metrics["starvation_count"] += 1

        self.metrics["production_meters"] += produced

    def run(self, duration_min: float, step_min: float = 1.0):
        steps = int(max(1, duration_min / step_min))
        for _ in range(steps):
            self.step(step_min)
