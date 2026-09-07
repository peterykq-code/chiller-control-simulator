"""Run the Stage 3 chilled-water load-step experiment."""

import csv
from pathlib import Path

from controller import apply_cooling_permission, proportional_control
from plant import (
    WATER_SPECIFIC_HEAT_KJ_PER_KG_C,
    calculate_flow_heat_transfer_kw,
    update_supply_return_temperatures,
)


SETPOINT_C = 7.0
KP = 0.3
MAX_COOLING_KW = 100.0
MASS_FLOW_KG_S = 5.0
SUPPLY_WATER_MASS_KG = 500.0
RETURN_WATER_MASS_KG = 500.0
INITIAL_HEAT_LOAD_KW = 30.0
FINAL_HEAT_LOAD_KW = 50.0
LOAD_STEP_TIME_S = 600.0
SIMULATION_TIME_S = 1800.0
DEFAULT_TIME_STEP_S = 10.0


def heat_load_profile_kw(time_s: float) -> float:
    """Return the building heat load at the given simulation time, in kW."""
    if time_s < LOAD_STEP_TIME_S:
        return INITIAL_HEAT_LOAD_KW
    return FINAL_HEAT_LOAD_KW


def analytical_steady_state(heat_load_kw: float) -> tuple[float, float]:
    """Return the unsaturated P-control steady-state supply and return temperatures."""
    required_cooling_fraction = heat_load_kw / MAX_COOLING_KW
    supply_temperature_c = SETPOINT_C + required_cooling_fraction / KP
    return_temperature_c = supply_temperature_c + heat_load_kw / (
        MASS_FLOW_KG_S * WATER_SPECIFIC_HEAT_KJ_PER_KG_C
    )
    return supply_temperature_c, return_temperature_c


def _sample(
    time_s: float,
    supply_temperature_c: float,
    return_temperature_c: float,
    energy_residual_kj: float,
) -> dict[str, float]:
    """Build one traceable result row from the current plant state."""
    heat_load_kw = heat_load_profile_kw(time_s)
    requested_cooling_fraction = proportional_control(
        supply_temperature_c,
        SETPOINT_C,
        KP,
    )
    applied_cooling_fraction = apply_cooling_permission(
        requested_cooling_fraction,
        "RUNNING",
    )
    cooling_kw = applied_cooling_fraction * MAX_COOLING_KW
    flow_heat_transfer_kw = calculate_flow_heat_transfer_kw(
        MASS_FLOW_KG_S,
        supply_temperature_c,
        return_temperature_c,
    )
    return {
        "time_s": time_s,
        "supply_temperature_c": supply_temperature_c,
        "return_temperature_c": return_temperature_c,
        "heat_load_kw": heat_load_kw,
        "mass_flow_kg_s": MASS_FLOW_KG_S,
        "flow_heat_transfer_kw": flow_heat_transfer_kw,
        "requested_cooling_fraction": requested_cooling_fraction,
        "applied_cooling_fraction": applied_cooling_fraction,
        "cooling_kw": cooling_kw,
        "energy_residual_kj": energy_residual_kj,
    }


def run_experiment(dt_s: float = DEFAULT_TIME_STEP_S) -> list[dict[str, float]]:
    """Return the complete two-node response for a reproducible load step."""
    if dt_s <= 0.0 or SIMULATION_TIME_S % dt_s != 0.0:
        raise ValueError("dt_s must be positive and divide the simulation time exactly.")

    supply_temperature_c, return_temperature_c = analytical_steady_state(
        INITIAL_HEAT_LOAD_KW,
    )
    samples = [
        _sample(
            0.0,
            supply_temperature_c,
            return_temperature_c,
            0.0,
        )
    ]
    number_of_steps = int(SIMULATION_TIME_S / dt_s)

    for step in range(number_of_steps):
        time_s = step * dt_s
        current = _sample(
            time_s,
            supply_temperature_c,
            return_temperature_c,
            0.0,
        )
        next_supply_c, next_return_c = update_supply_return_temperatures(
            supply_temperature_c=supply_temperature_c,
            return_temperature_c=return_temperature_c,
            mass_flow_kg_s=MASS_FLOW_KG_S,
            heat_load_kw=current["heat_load_kw"],
            cooling_kw=current["cooling_kw"],
            supply_water_mass_kg=SUPPLY_WATER_MASS_KG,
            return_water_mass_kg=RETURN_WATER_MASS_KG,
            dt_s=dt_s,
        )

        stored_energy_change_kj = WATER_SPECIFIC_HEAT_KJ_PER_KG_C * (
            SUPPLY_WATER_MASS_KG * (next_supply_c - supply_temperature_c)
            + RETURN_WATER_MASS_KG * (next_return_c - return_temperature_c)
        )
        external_energy_change_kj = (
            current["heat_load_kw"] - current["cooling_kw"]
        ) * dt_s
        energy_residual_kj = (
            stored_energy_change_kj - external_energy_change_kj
        )

        supply_temperature_c = next_supply_c
        return_temperature_c = next_return_c
        samples.append(
            _sample(
                (step + 1) * dt_s,
                supply_temperature_c,
                return_temperature_c,
                energy_residual_kj,
            )
        )

    return samples


def calculate_metrics(samples: list[dict[str, float]]) -> dict[str, float]:
    """Return quantitative checks for the load-step experiment."""
    analytical_supply_c, analytical_return_c = analytical_steady_state(
        FINAL_HEAT_LOAD_KW,
    )
    final = samples[-1]
    post_step_samples = [
        sample for sample in samples if sample["time_s"] >= LOAD_STEP_TIME_S
    ]
    settling_tolerance_c = 0.1
    settling_time_s = SIMULATION_TIME_S - LOAD_STEP_TIME_S

    for index, sample in enumerate(post_step_samples):
        remaining = post_step_samples[index:]
        if all(
            abs(item["supply_temperature_c"] - analytical_supply_c)
            <= settling_tolerance_c
            for item in remaining
        ):
            settling_time_s = sample["time_s"] - LOAD_STEP_TIME_S
            break

    return {
        "analytical_final_supply_c": analytical_supply_c,
        "analytical_final_return_c": analytical_return_c,
        "final_supply_c": final["supply_temperature_c"],
        "final_return_c": final["return_temperature_c"],
        "final_supply_difference_c": abs(
            final["supply_temperature_c"] - analytical_supply_c
        ),
        "final_return_difference_c": abs(
            final["return_temperature_c"] - analytical_return_c
        ),
        "maximum_energy_residual_kj": max(
            abs(sample["energy_residual_kj"]) for sample in samples
        ),
        "settling_time_s": settling_time_s,
        "final_supply_error_c": final["supply_temperature_c"] - SETPOINT_C,
    }


def write_results(
    samples: list[dict[str, float]],
    csv_path: Path,
) -> None:
    """Write Stage 3 samples to a CSV file."""
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)


def main() -> None:
    """Run, validate, print, and save the Stage 3 experiment."""
    samples_10_s = run_experiment(DEFAULT_TIME_STEP_S)
    samples_5_s = run_experiment(5.0)
    metrics = calculate_metrics(samples_10_s)
    metrics_5_s = calculate_metrics(samples_5_s)
    timestep_supply_difference_c = abs(
        metrics["final_supply_c"] - metrics_5_s["final_supply_c"]
    )
    timestep_return_difference_c = abs(
        metrics["final_return_c"] - metrics_5_s["final_return_c"]
    )

    acceptance_checks = {
        "energy conservation": metrics["maximum_energy_residual_kj"] <= 1e-9,
        "analytical supply temperature": metrics["final_supply_difference_c"] <= 0.02,
        "analytical return temperature": metrics["final_return_difference_c"] <= 0.02,
        "time-step sensitivity": max(
            timestep_supply_difference_c,
            timestep_return_difference_c,
        )
        <= 0.02,
    }

    csv_path = Path(__file__).resolve().parent / "results" / "stage3.csv"
    write_results(samples_10_s, csv_path)

    print("Stage 3: two-node chilled-water load-step experiment")
    print(
        f"Load step: {INITIAL_HEAT_LOAD_KW:.0f} to {FINAL_HEAT_LOAD_KW:.0f} kW "
        f"at {LOAD_STEP_TIME_S / 60:.0f} min"
    )
    print(
        f"Final CHWS: {metrics['final_supply_c']:.3f} C "
        f"(analytical {metrics['analytical_final_supply_c']:.3f} C)"
    )
    print(
        f"Final CHWR: {metrics['final_return_c']:.3f} C "
        f"(analytical {metrics['analytical_final_return_c']:.3f} C)"
    )
    print(f"Supply settling time: {metrics['settling_time_s']:.0f} s")
    print(
        "Maximum energy residual: "
        f"{metrics['maximum_energy_residual_kj']:.3e} kJ"
    )
    print(
        "5 s versus 10 s final-temperature difference: "
        f"{max(timestep_supply_difference_c, timestep_return_difference_c):.3e} C"
    )
    for name, passed in acceptance_checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
