"""Data models for the Corrugated Plant Simulator module."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PlantType(str, Enum):
    CORRUGATOR_CONVERTER = "corrugator_converter"
    CORRUGATOR_ONLY = "corrugator_only"
    CONVERTER_ONLY = "converter_only"


class TransportType(str, Enum):
    FORKLIFTS = "carretillas"
    CONVEYORS = "conveyors"
    TRACKS = "tracks"
    MIXED = "mixed"


class MachineType(str, Enum):
    CORRUGATOR = "corrugadora"
    DIE_CUTTER = "troqueladora"
    FLEXO = "flexografica"
    ROTARY = "rotativa"
    FOLDER_GLUER = "pegadora"
    SLITTER = "rebobinadora"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Sub-configurations
# ---------------------------------------------------------------------------

@dataclass
class CorrugatorConfig:
    speed_m_min: float = 250.0          # Production speed (m/min)
    width_mm: int = 2500                 # Useful width (mm)
    roll_store_capacity: int = 100       # Max rolls in storage
    has_intermediate_store: bool = True
    flutes: List[str] = field(default_factory=lambda: ["B", "C", "E"])
    rolls_per_hour: float = 2.5          # Roll consumption per hour

    @property
    def m2_per_hour(self) -> float:
        return self.speed_m_min * 60 * (self.width_mm / 1000)


@dataclass
class ConverterLine:
    id: str = "C1"
    machine_type: MachineType = MachineType.FLEXO
    format_width_mm: int = 500
    format_height_mm: int = 700
    speed_units_per_hour: int = 1000
    setup_time_min: int = 30
    availability: float = 0.92           # Planned availability 0-1

    @property
    def m2_per_hour(self) -> float:
        """Estimated m² consumed per hour."""
        return self.speed_units_per_hour * (self.format_width_mm / 1000) * (self.format_height_mm / 1000)


@dataclass
class TransportConfig:
    type: TransportType = TransportType.FORKLIFTS
    num_forklifts: int = 3
    forklift_speed_ms: float = 1.5       # m/s
    num_tracks: int = 0
    conveyor_speed_ms: float = 0.5       # m/s
    automatic: bool = False


@dataclass
class StorageConfig:
    input_capacity_pallets: int = 200
    buffer_capacity_pallets: int = 150
    output_capacity_pallets: int = 100
    fifo: bool = True


@dataclass
class ShiftConfig:
    shifts_per_day: int = 2
    working_days_per_month: int = 22
    hours_per_shift: float = 8.0

    @property
    def hours_per_month(self) -> float:
        return self.shifts_per_day * self.working_days_per_month * self.hours_per_shift


# ---------------------------------------------------------------------------
# Main plant configuration
# ---------------------------------------------------------------------------

@dataclass
class PlantConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Nueva Planta"
    plant_type: PlantType = PlantType.CORRUGATOR_CONVERTER
    corrugator: Optional[CorrugatorConfig] = None
    converters: List[ConverterLine] = field(default_factory=list)
    transport: TransportConfig = field(default_factory=TransportConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    shift: ShiftConfig = field(default_factory=ShiftConfig)
    simulation_duration_hours: float = 8.0
    simulation_speed: float = 10.0       # simulation-seconds per real-second
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_canvas_config(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict for the HTML5 canvas engine."""
        cfg: Dict[str, Any] = {
            "plantType": self.plant_type.value,
            "simSpeed": self.simulation_speed,
            "simDurationHours": self.simulation_duration_hours,
            "plantName": self.name,
            "bufferCapacity": self.storage.buffer_capacity_pallets,
            "transport": {
                "type": self.transport.type.value,
                "numForklifts": self.transport.num_forklifts,
                "forkliftsSpeed": self.transport.forklift_speed_ms,
                "numTracks": self.transport.num_tracks,
            },
        }
        if self.corrugator:
            cfg["corrugator"] = {
                "speedMMin": self.corrugator.speed_m_min,
                "widthMm": self.corrugator.width_mm,
                "rollStoreCapacity": self.corrugator.roll_store_capacity,
                "m2PerHour": round(self.corrugator.m2_per_hour),
                "rollsPerHour": self.corrugator.rolls_per_hour,
            }
        cfg["converters"] = [
            {
                "id": c.id,
                "type": c.machine_type.value,
                "speedUdsPerHour": c.speed_units_per_hour,
                "setupTimeMin": c.setup_time_min,
                "availability": c.availability,
                "m2PerHour": round(c.m2_per_hour, 1),
            }
            for c in self.converters
        ]
        return cfg


# ---------------------------------------------------------------------------
# Simulation result models
# ---------------------------------------------------------------------------

@dataclass
class MachineMetric:
    machine_id: str
    availability: float = 0.0       # % time available
    performance: float = 0.0        # % of max speed achieved
    quality: float = 0.0            # % good units
    oee: float = 0.0                # OEE = avail × perf × qual
    units_produced: float = 0.0
    blocked_time_s: float = 0.0
    setup_time_s: float = 0.0


@dataclass
class BottleneckRecord:
    location: str
    type: str                        # "machine", "transport", "storage"
    avg_wait_s: float = 0.0
    max_wait_s: float = 0.0
    frequency: int = 0               # how many times detected


@dataclass
class SimulationResults:
    sim_id: str
    plant_name: str
    plant_type: str
    duration_hours: float
    m2_produced: float = 0.0
    total_units_converted: float = 0.0
    corrugator_efficiency: float = 0.0
    average_oee: float = 0.0
    transport_utilization: float = 0.0
    buffer_max_occupancy: float = 0.0
    buffer_avg_occupancy: float = 0.0
    machine_metrics: List[MachineMetric] = field(default_factory=list)
    bottlenecks: List[BottleneckRecord] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)  # 1-min snapshots
    recommendations: List[str] = field(default_factory=list)
    scenario_label: str = "Base"
    completed_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
