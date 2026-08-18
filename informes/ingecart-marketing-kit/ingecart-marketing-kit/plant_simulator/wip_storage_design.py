"""Evidence-aware WIP, storage, and transport fleet dimensioning."""
from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from .models import PlantConfig


class EvidenceClass(str, Enum):
    FACT = "FACT"
    VALIDATED = "VALIDATED"
    BENCHMARK = "BENCHMARK"
    ENGINEERING_ESTIMATE = "ENGINEERING_ESTIMATE"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ParameterEvidence:
    classification: EvidenceClass
    source: str
    location: str = ""
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class WIPDemand:
    production_rate_pallets_h: float
    residence_time_h: float
    demand_rate_cv: float
    lead_time_std_h: float
    service_factor_z: float


@dataclass(frozen=True)
class StorageGeometry:
    load_length_m: float
    load_width_m: float
    longitudinal_clearance_m: float
    lateral_clearance_m: float
    stacking_levels: int
    target_occupancy: float
    storage_area_utilization: float
    positions_per_cell: int


@dataclass(frozen=True)
class TransportDemand:
    missions_per_pallet: float
    round_trip_distance_m: float
    speed_m_s: float
    handling_time_s: float
    availability: float
    charging_fraction: float
    congestion_factor: float
    target_utilization: float
    peak_factor: float
    redundancy_vehicles: int = 0


@dataclass(frozen=True)
class WIPArea:
    name: str
    available_area_m2: float


@dataclass(frozen=True)
class DeliveryFlow:
    name: str
    pallet_rate_h: float


@dataclass(frozen=True)
class RouteDistance:
    wip_area: str
    delivery_zone: str
    round_trip_distance_m: float


@dataclass(frozen=True)
class FacilityLayout:
    wip_areas: Tuple[WIPArea, ...]
    delivery_flows: Tuple[DeliveryFlow, ...]
    route_distances: Tuple[RouteDistance, ...]


@dataclass(frozen=True)
class WIPStorageDesignInput:
    demand: WIPDemand
    storage: StorageGeometry
    transport: TransportDemand
    evidence: Dict[str, ParameterEvidence] = field(default_factory=dict)
    layout: Optional[FacilityLayout] = None


@dataclass(frozen=True)
class WIPStorageDesignResult:
    average_wip_pallets: float
    safety_wip_pallets: float
    peak_wip_pallets: float
    storage_positions: int
    wip_cells: int
    net_storage_area_m2: float
    gross_storage_area_m2: float
    mission_rate_h: float
    mission_cycle_time_s: float
    weighted_round_trip_distance_m: float
    fleet_without_redundancy: int
    fleet_size: int
    layout_feasible: bool
    available_storage_area_m2: float
    area_deficit_m2: float
    zone_capacities: Dict[str, int]
    zone_allocations: Dict[str, int]
    route_profile: Tuple[Dict[str, Any], ...]
    evidence: Dict[str, ParameterEvidence]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_wip_storage_design(
    design: WIPStorageDesignInput,
) -> WIPStorageDesignResult:
    """Dimension WIP, floor storage, and fleet capacity from explicit inputs."""
    _validate(design)
    demand = design.demand
    storage = design.storage
    transport = design.transport

    average_wip = demand.production_rate_pallets_h * demand.residence_time_h
    demand_variability = demand.residence_time_h * demand.demand_rate_cv
    combined_time_variability = math.sqrt(
        demand.lead_time_std_h**2 + demand_variability**2
    )
    safety_wip = (
        demand.service_factor_z
        * demand.production_rate_pallets_h
        * combined_time_variability
    )
    peak_wip = average_wip + safety_wip

    effective_stack_capacity = storage.stacking_levels * storage.target_occupancy
    positions = math.ceil(peak_wip / effective_stack_capacity)
    position_area = (
        storage.load_length_m + storage.longitudinal_clearance_m
    ) * (storage.load_width_m + storage.lateral_clearance_m)
    net_area = positions * position_area
    gross_area = net_area / storage.storage_area_utilization
    cells = math.ceil(positions / storage.positions_per_cell)

    mission_rate = demand.production_rate_pallets_h * transport.missions_per_pallet
    weighted_distance = transport.round_trip_distance_m
    layout_feasible = True
    available_area = gross_area
    area_deficit = 0.0
    zone_capacities: Dict[str, int] = {}
    zone_allocations: Dict[str, int] = {}
    route_profile: Tuple[Dict[str, Any], ...] = ()
    if design.layout is not None:
        (
            layout_feasible,
            available_area,
            area_deficit,
            zone_capacities,
            zone_allocations,
            weighted_distance,
            route_profile,
        ) = _optimize_layout(design.layout, storage, positions, position_area)

    cycle_time = (
        weighted_distance / transport.speed_m_s
        + transport.handling_time_s
    ) * transport.congestion_factor
    capacity_per_vehicle_h = (
        3600.0
        / cycle_time
        * transport.availability
        * (1.0 - transport.charging_fraction)
        * transport.target_utilization
    )
    fleet_without_redundancy = math.ceil(
        mission_rate * transport.peak_factor / capacity_per_vehicle_h
    )

    return WIPStorageDesignResult(
        average_wip_pallets=round(average_wip, 3),
        safety_wip_pallets=round(safety_wip, 3),
        peak_wip_pallets=round(peak_wip, 3),
        storage_positions=positions,
        wip_cells=cells,
        net_storage_area_m2=round(net_area, 3),
        gross_storage_area_m2=round(gross_area, 3),
        mission_rate_h=round(mission_rate, 3),
        mission_cycle_time_s=round(cycle_time, 3),
        weighted_round_trip_distance_m=round(weighted_distance, 3),
        fleet_without_redundancy=fleet_without_redundancy,
        fleet_size=fleet_without_redundancy + transport.redundancy_vehicles,
        layout_feasible=layout_feasible,
        available_storage_area_m2=round(available_area, 3),
        area_deficit_m2=round(area_deficit, 3),
        zone_capacities=zone_capacities,
        zone_allocations=zone_allocations,
        route_profile=route_profile,
        evidence=dict(design.evidence),
    )


def _optimize_layout(
    layout: FacilityLayout,
    storage: StorageGeometry,
    required_positions: int,
    position_area_m2: float,
) -> Tuple[
    bool,
    float,
    float,
    Dict[str, int],
    Dict[str, int],
    float,
    Tuple[Dict[str, Any], ...],
]:
    """Allocate WIP positions to delivery demand at minimum travel distance."""
    available_area = sum(area.available_area_m2 for area in layout.wip_areas)
    capacities = {
        area.name: math.floor(
            area.available_area_m2
            * storage.storage_area_utilization
            / position_area_m2
            + 1e-9
        )
        for area in layout.wip_areas
    }
    total_capacity = sum(capacities.values())
    feasible = total_capacity >= required_positions
    missing_positions = max(0, required_positions - total_capacity)
    area_deficit = missing_positions * position_area_m2 / storage.storage_area_utilization

    total_flow = sum(flow.pallet_rate_h for flow in layout.delivery_flows)
    exact_demands = {
        flow.name: required_positions * flow.pallet_rate_h / total_flow
        for flow in layout.delivery_flows
    }
    demands = {name: math.floor(value) for name, value in exact_demands.items()}
    remainder = required_positions - sum(demands.values())
    for name in sorted(
        demands,
        key=lambda item: exact_demands[item] - demands[item],
        reverse=True,
    )[:remainder]:
        demands[name] += 1

    distances = {
        (route.wip_area, route.delivery_zone): route.round_trip_distance_m
        for route in layout.route_distances
    }
    assignments = _minimum_cost_assignments(
        capacities,
        demands,
        distances,
        min(required_positions, total_capacity),
    )

    allocated = sum(assignments.values())
    if feasible and allocated != required_positions:
        raise ValueError("route_distances do not connect all WIP areas and delivery zones")
    allocations = {
        area.name: sum(
            quantity
            for (area_name, _), quantity in assignments.items()
            if area_name == area.name
        )
        for area in layout.wip_areas
    }
    weighted_distance = (
        sum(distances[route] * quantity for route, quantity in assignments.items())
        / allocated
        if allocated
        else 0.0
    )
    route_profile = tuple(
        {
            "wip_area": area_name,
            "delivery_zone": delivery_name,
            "positions": quantity,
            "mission_share": quantity / allocated,
            "round_trip_distance_m": distances[(area_name, delivery_name)],
        }
        for (area_name, delivery_name), quantity in sorted(assignments.items())
    )
    return (
        feasible,
        available_area,
        area_deficit,
        capacities,
        allocations,
        weighted_distance,
        route_profile,
    )


def _minimum_cost_assignments(
    capacities: Dict[str, int],
    demands: Dict[str, int],
    distances: Dict[Tuple[str, str], float],
    target_flow: int,
) -> Dict[Tuple[str, str], int]:
    """Solve the integer transportation problem with successive shortest paths."""
    source = ("source", "")
    sink = ("sink", "")
    area_nodes = {name: ("area", name) for name in capacities}
    delivery_nodes = {name: ("delivery", name) for name in demands}
    graph: Dict[Tuple[str, str], list] = {
        node: []
        for node in (source, sink, *area_nodes.values(), *delivery_nodes.values())
    }

    def add_edge(start: Tuple[str, str], end: Tuple[str, str], capacity: int, cost: float) -> int:
        forward_index = len(graph[start])
        graph[start].append([end, len(graph[end]), capacity, cost])
        graph[end].append([start, forward_index, 0, -cost])
        return forward_index

    for name, capacity in capacities.items():
        add_edge(source, area_nodes[name], capacity, 0.0)
    route_edges: Dict[Tuple[str, str], Tuple[Tuple[str, str], int, int]] = {}
    for route, cost in distances.items():
        area_name, delivery_name = route
        edge_capacity = min(capacities[area_name], demands[delivery_name])
        edge_index = add_edge(
            area_nodes[area_name],
            delivery_nodes[delivery_name],
            edge_capacity,
            cost,
        )
        route_edges[route] = (area_nodes[area_name], edge_index, edge_capacity)
    for name, demand in demands.items():
        add_edge(delivery_nodes[name], sink, demand, 0.0)

    sent = 0
    nodes = list(graph)
    while sent < target_flow:
        distance = {node: math.inf for node in nodes}
        previous: Dict[Tuple[str, str], Tuple[Tuple[str, str], int]] = {}
        distance[source] = 0.0
        for _ in range(len(nodes) - 1):
            changed = False
            for start in nodes:
                if distance[start] == math.inf:
                    continue
                for edge_index, edge in enumerate(graph[start]):
                    end, _, capacity, cost = edge
                    if capacity > 0 and distance[start] + cost < distance[end]:
                        distance[end] = distance[start] + cost
                        previous[end] = (start, edge_index)
                        changed = True
            if not changed:
                break
        if sink not in previous:
            break
        quantity = target_flow - sent
        node = sink
        while node != source:
            start, edge_index = previous[node]
            quantity = min(quantity, graph[start][edge_index][2])
            node = start
        node = sink
        while node != source:
            start, edge_index = previous[node]
            edge = graph[start][edge_index]
            edge[2] -= quantity
            graph[node][edge[1]][2] += quantity
            node = start
        sent += quantity

    return {
        route: initial_capacity - graph[start][edge_index][2]
        for route, (start, edge_index, initial_capacity) in route_edges.items()
        if initial_capacity - graph[start][edge_index][2] > 0
    }


def configure_plant_for_wip_design(
    config: "PlantConfig",
    design: WIPStorageDesignInput,
    result: Optional[WIPStorageDesignResult] = None,
) -> "PlantConfig":
    """Return an isolated plant configuration dimensioned by the WIP model."""
    calculated = result or calculate_wip_storage_design(design)
    configured = deepcopy(config)
    configured.storage.buffer_capacity_pallets = math.ceil(
        calculated.peak_wip_pallets
    )
    configured.transport.num_forklifts = calculated.fleet_size
    configured.transport.forklift_speed_ms = design.transport.speed_m_s
    configured.transport.round_trip_distance_m = calculated.weighted_round_trip_distance_m
    configured.transport.route_profile = [dict(route) for route in calculated.route_profile]
    configured.transport.handling_time_s = design.transport.handling_time_s
    configured.transport.missions_per_pallet = design.transport.missions_per_pallet
    return configured


def _validate(design: WIPStorageDesignInput) -> None:
    demand = design.demand
    storage = design.storage
    transport = design.transport
    positive = {
        "production_rate_pallets_h": demand.production_rate_pallets_h,
        "residence_time_h": demand.residence_time_h,
        "service_factor_z": demand.service_factor_z,
        "load_length_m": storage.load_length_m,
        "load_width_m": storage.load_width_m,
        "stacking_levels": storage.stacking_levels,
        "positions_per_cell": storage.positions_per_cell,
        "missions_per_pallet": transport.missions_per_pallet,
        "round_trip_distance_m": transport.round_trip_distance_m,
        "speed_m_s": transport.speed_m_s,
        "congestion_factor": transport.congestion_factor,
        "peak_factor": transport.peak_factor,
    }
    invalid = [name for name, value in positive.items() if value <= 0]
    if invalid:
        raise ValueError(f"values must be positive: {', '.join(invalid)}")
    fractions = {
        "target_occupancy": storage.target_occupancy,
        "storage_area_utilization": storage.storage_area_utilization,
        "availability": transport.availability,
        "target_utilization": transport.target_utilization,
    }
    invalid = [name for name, value in fractions.items() if not 0.0 < value <= 1.0]
    if invalid:
        raise ValueError(f"fractions must be in (0, 1]: {', '.join(invalid)}")
    if not 0.0 <= transport.charging_fraction < 1.0:
        raise ValueError("charging_fraction must be in [0, 1)")
    if demand.demand_rate_cv < 0 or demand.lead_time_std_h < 0:
        raise ValueError("variability inputs cannot be negative")
    if storage.longitudinal_clearance_m < 0 or storage.lateral_clearance_m < 0:
        raise ValueError("storage clearances cannot be negative")
    if transport.handling_time_s < 0 or transport.redundancy_vehicles < 0:
        raise ValueError("handling time and redundancy cannot be negative")
    if design.layout is not None:
        layout = design.layout
        if not layout.wip_areas or not layout.delivery_flows:
            raise ValueError("layout requires WIP areas and delivery flows")
        if any(area.available_area_m2 <= 0 for area in layout.wip_areas):
            raise ValueError("available WIP areas must be positive")
        if any(flow.pallet_rate_h <= 0 for flow in layout.delivery_flows):
            raise ValueError("delivery flow rates must be positive")
        area_names = {area.name for area in layout.wip_areas}
        delivery_names = {flow.name for flow in layout.delivery_flows}
        if len(area_names) != len(layout.wip_areas) or len(delivery_names) != len(layout.delivery_flows):
            raise ValueError("WIP area and delivery zone names must be unique")
        if any(
            route.round_trip_distance_m <= 0
            or route.wip_area not in area_names
            or route.delivery_zone not in delivery_names
            for route in layout.route_distances
        ):
            raise ValueError("route distances must be positive and reference known zones")