"""
Material flow model: Warehouse -> Buffer -> Exchange -> Track -> Roll Stand

Implementa estructuras simples para representar bobinas y moverlas
entre zonas con capacidades y políticas sencillas (FIFO).
"""
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Reel:
    id: str
    weight: float
    type: str
    location: str  # warehouse, buffer, exchange, track, roll_stand, returned
    order_id: Optional[str] = None
    track_id: Optional[str] = None
    is_partial: bool = False


class MaterialsFlow:
    def __init__(self, config: Dict = None):
        config = config or {}
        self.warehouse_capacity = int(config.get("warehouse_capacity", 200))
        self.buffer_capacity = int(config.get("buffer_capacity", 20))
        self.num_tracks = int(config.get("num_tracks", 10))

        self.warehouse: List[Reel] = []
        self.buffer: List[Reel] = []
        self.exchange: List[Reel] = []
        # tracks: dict track_id -> Reel or None
        self.tracks: Dict[str, Optional[Reel]] = {f"T{i+1}": None for i in range(self.num_tracks)}
        self.roll_stands: Dict[str, Optional[Reel]] = {}
        self.returned: List[Reel] = []

    def add_reel_to_warehouse(self, reel: Reel) -> bool:
        if len(self.warehouse) < self.warehouse_capacity:
            reel.location = "warehouse"
            self.warehouse.append(reel)
            return True
        return False

    def request_reel(self, reel_type: str) -> Optional[Reel]:
        """Solicita una bobina del almacén (FIFO por tipo)."""
        for reel in list(self.warehouse):
            if reel.type == reel_type:
                self.warehouse.remove(reel)
                reel.location = "buffer"
                return reel
        return None

    def move_to_buffer(self, reel: Reel) -> bool:
        if len(self.buffer) < self.buffer_capacity:
            reel.location = "buffer"
            self.buffer.append(reel)
            return True
        return False

    def move_to_exchange(self, reel: Reel) -> bool:
        reel.location = "exchange"
        self.exchange.append(reel)
        return True

    def move_to_track(self, reel: Reel, track_id: str) -> bool:
        if track_id not in self.tracks:
            return False
        if self.tracks[track_id] is None:
            reel.location = "track"
            reel.track_id = track_id
            self.tracks[track_id] = reel
            return True
        return False

    def move_to_roll_stand(self, reel: Reel, stand_id: str) -> bool:
        reel.location = "roll_stand"
        self.roll_stands[stand_id] = reel
        return True

    def return_reel(self, reel: Reel) -> bool:
        reel.location = "returned"
        reel.is_partial = True
        self.returned.append(reel)
        return True

    def return_partial_reel(self, track_id: str) -> bool:
        """Move a partial reel from a track to the returned list.

        Criteria: if a track has a reel and its weight < 300 kg, treat as partial.
        """
        if track_id not in self.tracks:
            return False
        reel = self.tracks[track_id]
        if reel is None:
            return False
        if reel.weight < 300.0:
            reel.location = "returned"
            reel.is_partial = True
            self.returned.append(reel)
            self.tracks[track_id] = None
            return True
        return False

    def get_track_status(self) -> Dict:
        return {
            track_id: {
                "occupied": self.tracks[track_id] is not None,
                "reel_type": self.tracks[track_id].type if self.tracks[track_id] else None,
                "reel_weight": self.tracks[track_id].weight if self.tracks[track_id] else 0,
            }
            for track_id in self.tracks
        }
