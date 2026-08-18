import sys
from dataclasses import replace
from pathlib import Path


SIMULATOR_ROOT = (
    Path(__file__).resolve().parents[1]
    / "informes"
    / "ingecart-marketing-kit"
    / "ingecart-marketing-kit"
)
sys.path.insert(0, str(SIMULATOR_ROOT))

from plant_simulator.wip_storage_design import (  # noqa: E402
    DeliveryFlow,
    EvidenceClass,
    FacilityLayout,
    ParameterEvidence,
    RouteDistance,
    StorageGeometry,
    TransportDemand,
    WIPArea,
    WIPDemand,
    WIPStorageDesignInput,
    calculate_wip_storage_design,
    configure_plant_for_wip_design,
)
from plant_simulator.models import (  # noqa: E402
    ConverterLine,
    PlantConfig,
    PlantType,
    TransportConfig,
)
from plant_simulator.simulation_engine import SimulationEngine  # noqa: E402


def _reference_design(stacking_levels: int) -> WIPStorageDesignInput:
    return WIPStorageDesignInput(
        demand=WIPDemand(
            production_rate_pallets_h=30.0,
            residence_time_h=2.0,
            demand_rate_cv=0.10,
            lead_time_std_h=0.10,
            service_factor_z=1.645,
        ),
        storage=StorageGeometry(
            load_length_m=2.0,
            load_width_m=1.2,
            longitudinal_clearance_m=0.1,
            lateral_clearance_m=0.1,
            stacking_levels=stacking_levels,
            target_occupancy=0.85,
            storage_area_utilization=0.60,
            positions_per_cell=6,
        ),
        transport=TransportDemand(
            missions_per_pallet=2.0,
            round_trip_distance_m=120.0,
            speed_m_s=1.2,
            handling_time_s=60.0,
            availability=0.95,
            charging_fraction=0.15,
            congestion_factor=1.20,
            target_utilization=0.80,
            peak_factor=1.20,
            redundancy_vehicles=1,
        ),
        evidence={
            "round_trip_distance_m": ParameterEvidence(
                EvidenceClass.ENGINEERING_ESTIMATE,
                "AMR_FLEET_CORRUGATED_USECASES.html",
                "layout INGECART 120m",
                0.70,
            )
        },
    )


def test_dimensions_wip_storage_and_fleet_from_explicit_inputs():
    design = _reference_design(stacking_levels=1)
    result = calculate_wip_storage_design(design)

    assert result.average_wip_pallets == 60.0
    assert result.safety_wip_pallets == 11.035
    assert result.peak_wip_pallets == 71.035
    assert result.storage_positions == 84
    assert result.wip_cells == 14
    assert result.gross_storage_area_m2 == 382.2
    assert result.mission_cycle_time_s == 192.0
    assert result.fleet_without_redundancy == 6
    assert result.fleet_size == 7
    assert result.evidence["round_trip_distance_m"].classification is EvidenceClass.ENGINEERING_ESTIMATE


def test_available_areas_and_route_distances_drive_minimum_amr_solution():
    design = replace(
        _reference_design(stacking_levels=1),
        layout=FacilityLayout(
            wip_areas=(
                WIPArea("near", available_area_m2=200.0),
                WIPArea("far", available_area_m2=220.0),
            ),
            delivery_flows=(
                DeliveryFlow("converter_a", pallet_rate_h=18.0),
                DeliveryFlow("converter_b", pallet_rate_h=12.0),
            ),
            route_distances=(
                RouteDistance("near", "converter_a", round_trip_distance_m=50.0),
                RouteDistance("near", "converter_b", round_trip_distance_m=150.0),
                RouteDistance("far", "converter_a", round_trip_distance_m=170.0),
                RouteDistance("far", "converter_b", round_trip_distance_m=60.0),
            ),
        ),
    )

    result = calculate_wip_storage_design(design)

    assert result.layout_feasible is True
    assert result.available_storage_area_m2 == 420.0
    assert result.area_deficit_m2 == 0.0
    assert result.weighted_round_trip_distance_m < 120.0
    assert result.zone_allocations["near"] > result.zone_allocations["far"]
    assert result.fleet_size <= 7

    configured = configure_plant_for_wip_design(PlantConfig(), design, result)
    engine = SimulationEngine(configured)
    engine._initialize()
    assert configured.transport.route_profile == list(result.route_profile)
    assert engine._transport.route_profile == list(result.route_profile)
    assert engine._transport.cycle_time_s < 160.0


def test_route_assignment_is_global_minimum_not_greedy_nearest_first():
    design = replace(
        _reference_design(stacking_levels=1),
        layout=FacilityLayout(
            wip_areas=(
                WIPArea("area_a", available_area_m2=191.1),
                WIPArea("area_b", available_area_m2=191.1),
            ),
            delivery_flows=(
                DeliveryFlow("destination_x", pallet_rate_h=15.0),
                DeliveryFlow("destination_y", pallet_rate_h=15.0),
            ),
            route_distances=(
                RouteDistance("area_a", "destination_x", round_trip_distance_m=1.0),
                RouteDistance("area_a", "destination_y", round_trip_distance_m=2.0),
                RouteDistance("area_b", "destination_x", round_trip_distance_m=2.0),
                RouteDistance("area_b", "destination_y", round_trip_distance_m=100.0),
            ),
        ),
    )

    result = calculate_wip_storage_design(design)

    assert result.weighted_round_trip_distance_m == 2.0
    assert {(route["wip_area"], route["delivery_zone"]) for route in result.route_profile} == {
        ("area_a", "destination_y"),
        ("area_b", "destination_x"),
    }


def test_two_high_storage_reduces_floor_positions_but_not_transport_demand():
    amr_one_high = calculate_wip_storage_design(_reference_design(stacking_levels=1))
    traditional_input = _reference_design(stacking_levels=2)
    traditional_input = replace(
        traditional_input,
        transport=replace(traditional_input.transport, redundancy_vehicles=0),
    )
    traditional_two_high = calculate_wip_storage_design(traditional_input)

    assert traditional_two_high.storage_positions == 42
    assert traditional_two_high.gross_storage_area_m2 == 191.1
    assert traditional_two_high.mission_rate_h == amr_one_high.mission_rate_h


def test_dimensioned_parameters_are_consumed_by_simulation_engine():
    source_config = PlantConfig()
    design = _reference_design(stacking_levels=1)

    configured = configure_plant_for_wip_design(source_config, design)
    engine = SimulationEngine(configured)
    engine._initialize()

    assert source_config.storage.buffer_capacity_pallets == 150
    assert configured.storage.buffer_capacity_pallets == 72
    assert engine._storages["buffer"].capacity == 72
    assert engine._transport is not None
    assert engine._transport.num_vehicles == 7
    assert engine._transport.speed_ms == 1.2
    assert engine._transport.trip_distance_m == 120.0
    assert engine._transport.load_time_s == 60.0
    assert engine._transport.missions_per_pallet == 2.0


def test_transport_cycle_capacity_limits_converter_throughput():
    constrained = PlantConfig(
        plant_type=PlantType.CONVERTER_ONLY,
        converters=[ConverterLine(speed_units_per_hour=3000)],
        transport=TransportConfig(
            num_forklifts=1,
            forklift_speed_ms=1.2,
            round_trip_distance_m=120.0,
            handling_time_s=60.0,
            missions_per_pallet=2.0,
        ),
        simulation_duration_hours=0.1,
    )
    dimensioned = replace(
        constrained,
        transport=replace(constrained.transport, num_forklifts=7),
    )

    constrained_result = SimulationEngine(constrained, seed=7).run()
    dimensioned_result = SimulationEngine(dimensioned, seed=7).run()

    assert constrained_result.total_units_converted < dimensioned_result.total_units_converted
    assert constrained_result.transport_utilization == 100.0
    assert dimensioned_result.transport_utilization < 100.0