"""Stage 1: update chilled-water temperature using an energy balance."""

import math


# Approximate specific heat: raising 1 kg of water by 1 degree requires 4.18 kJ.
WATER_SPECIFIC_HEAT_KJ_PER_KG_C = 4.18


def update_temperature(
    temperature_c: float,
    cooling_fraction: float,
    heat_load_kw: float,
    max_cooling_kw: float,
    water_mass_kg: float,
    dt_s: float,
) -> float:
    """Return the water temperature after dt_s seconds, in degrees Celsius.

    temperature_c: current water temperature, in degrees Celsius.
    cooling_fraction: cooling command; 0.0 means off and 1.0 means full capacity.
    heat_load_kw: rate of heat entering the water from an external load, in kW.
    max_cooling_kw: cooling capacity available at a full command, in kW.
    water_mass_kg: total mass of water represented by the model, in kg.
    dt_s: duration represented by this simulation step, in seconds.

    Assume well-mixed water and an immediate cooling response. All inputs
    remain constant during this step.
    """
    values = (
        temperature_c,
        cooling_fraction,
        heat_load_kw,
        max_cooling_kw,
        water_mass_kg,
        dt_s,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Plant inputs must be finite numbers.")
    if not 0.0 <= cooling_fraction <= 1.0:
        raise ValueError("cooling_fraction must be between 0.0 and 1.0.")
    if heat_load_kw < 0.0:
        raise ValueError("heat_load_kw must be non-negative.")
    if max_cooling_kw <= 0.0 or water_mass_kg <= 0.0 or dt_s <= 0.0:
        raise ValueError("max_cooling_kw, water_mass_kg and dt_s must be positive.")

    cooling_kw = cooling_fraction * max_cooling_kw
    net_heat_kw = heat_load_kw - cooling_kw
    thermal_capacity_kj_per_c = water_mass_kg * WATER_SPECIFIC_HEAT_KJ_PER_KG_C

    # 1 kW = 1 kJ/s. A negative net heat rate lowers the water temperature.
    temperature_change_c = net_heat_kw * dt_s / thermal_capacity_kj_per_c
    return temperature_c + temperature_change_c


def calculate_flow_heat_transfer_kw(
    mass_flow_kg_s: float,
    supply_temperature_c: float,
    return_temperature_c: float,
) -> float:
    """Return heat carried from the return node to the supply node, in kW.

    Positive heat transfer means the return water is warmer than the supply
    water. The equation is mass_flow * Cp * (return - supply).
    """
    values = (mass_flow_kg_s, supply_temperature_c, return_temperature_c)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Flow heat-transfer inputs must be finite numbers.")
    if mass_flow_kg_s < 0.0:
        raise ValueError("mass_flow_kg_s must be non-negative.")

    temperature_difference_c = return_temperature_c - supply_temperature_c
    return mass_flow_kg_s * WATER_SPECIFIC_HEAT_KJ_PER_KG_C * temperature_difference_c


def update_supply_return_temperatures(
    supply_temperature_c: float,
    return_temperature_c: float,
    mass_flow_kg_s: float,
    heat_load_kw: float,
    cooling_kw: float,
    supply_water_mass_kg: float,
    return_water_mass_kg: float,
    dt_s: float,
) -> tuple[float, float]:
    """Return the next supply and return temperatures after one time step.

    The model has two well-mixed water nodes. The building load adds heat to
    the return node, the chiller removes heat from the supply node, and water
    flow transfers heat from return to supply.
    """
    other_values = (
        heat_load_kw,
        cooling_kw,
        supply_water_mass_kg,
        return_water_mass_kg,
        dt_s,
    )
    if not all(math.isfinite(value) for value in other_values):
        raise ValueError("Two-node plant inputs must be finite numbers.")
    if heat_load_kw < 0.0 or cooling_kw < 0.0:
        raise ValueError("heat_load_kw and cooling_kw must be non-negative.")
    if supply_water_mass_kg <= 0.0 or return_water_mass_kg <= 0.0 or dt_s <= 0.0:
        raise ValueError("Water masses and dt_s must be positive.")

    flow_heat_transfer_kw = calculate_flow_heat_transfer_kw(
        mass_flow_kg_s,
        supply_temperature_c,
        return_temperature_c,
    )
    supply_net_heat_kw = flow_heat_transfer_kw - cooling_kw
    return_net_heat_kw = heat_load_kw - flow_heat_transfer_kw

    supply_temperature_change_c = (
        supply_net_heat_kw
        * dt_s
        / (supply_water_mass_kg * WATER_SPECIFIC_HEAT_KJ_PER_KG_C)
    )
    return_temperature_change_c = (
        return_net_heat_kw
        * dt_s
        / (return_water_mass_kg * WATER_SPECIFIC_HEAT_KJ_PER_KG_C)
    )
    return (
        supply_temperature_c + supply_temperature_change_c,
        return_temperature_c + return_temperature_change_c,
    )
