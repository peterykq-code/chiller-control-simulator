"""Compare PI saturation recovery with and without conditional anti-windup."""

import csv
from pathlib import Path

from controller import apply_cooling_permission, proportional_integral_control
from plant import (
    WATER_SPECIFIC_HEAT_KJ_PER_KG_C,
    calculate_flow_heat_transfer_kw,
    update_supply_return_temperatures,
)
from stage3_main import (
    DEFAULT_TIME_STEP_S,
    INITIAL_HEAT_LOAD_KW,
    KP,
    MASS_FLOW_KG_S,
    MAX_COOLING_KW,
    RETURN_WATER_MASS_KG,
    SETPOINT_C,
    SUPPLY_WATER_MASS_KG,
)
from stage4_main import PI_KI_PER_S


OVERLOAD_START_TIME_S = 600.0
LOAD_RECOVERY_TIME_S = 1200.0
SIMULATION_TIME_S = 3600.0
OVERLOAD_HEAT_LOAD_KW = 120.0
RECOVERY_BAND_C = 0.1
SATURATION_TOLERANCE = 1e-12


def heat_load_profile_kw(time_s: float) -> float:
    """Return the Stage 5 load: 30 kW, then 120 kW, then 30 kW."""
    if not 0.0 <= time_s <= SIMULATION_TIME_S:
        raise ValueError("time_s must be within the Stage 5 simulation.")
    if OVERLOAD_START_TIME_S <= time_s < LOAD_RECOVERY_TIME_S:
        return OVERLOAD_HEAT_LOAD_KW
    return INITIAL_HEAT_LOAD_KW


def _initial_conditions() -> tuple[float, float, float]:
    """Return the balanced 30 kW PI operating point."""
    supply_c = SETPOINT_C
    return_c = supply_c + INITIAL_HEAT_LOAD_KW / (
        MASS_FLOW_KG_S * WATER_SPECIFIC_HEAT_KJ_PER_KG_C
    )
    initial_cooling_fraction = INITIAL_HEAT_LOAD_KW / MAX_COOLING_KW
    integral_error_c_s = initial_cooling_fraction / PI_KI_PER_S
    return supply_c, return_c, integral_error_c_s


def run_experiment(
    anti_windup_enabled: bool,
    dt_s: float = DEFAULT_TIME_STEP_S,
) -> list[dict[str, float | str | bool]]:
    """Return one PI response to the overload and recovery experiment."""
    if not isinstance(anti_windup_enabled, bool):
        raise ValueError("anti_windup_enabled must be True or False.")
    if dt_s <= 0.0 or SIMULATION_TIME_S % dt_s != 0.0:
        raise ValueError("dt_s must be positive and divide the simulation time exactly.")

    supply_c, return_c, integral_error_c_s = _initial_conditions()
    samples: list[dict[str, float | str | bool]] = []
    energy_residual_kj = 0.0
    number_of_steps = int(SIMULATION_TIME_S / dt_s)
    controller_name = "PI_ANTI_WINDUP" if anti_windup_enabled else "PI_NO_ANTI_WINDUP"

    for step in range(number_of_steps + 1):
        time_s = step * dt_s
        heat_load_kw = heat_load_profile_kw(time_s)
        error_c = supply_c - SETPOINT_C
        proportional_term = KP * error_c
        integral_term = PI_KI_PER_S * integral_error_c_s
        unrestricted_command = proportional_term + integral_term
        requested_cooling_fraction, next_integral_error_c_s = (
            proportional_integral_control(
                temperature_c=supply_c,
                setpoint_c=SETPOINT_C,
                kp=KP,
                ki_per_s=PI_KI_PER_S,
                integral_error_c_s=integral_error_c_s,
                dt_s=dt_s,
                anti_windup_enabled=anti_windup_enabled,
            )
        )
        applied_cooling_fraction = apply_cooling_permission(
            requested_cooling_fraction,
            "RUNNING",
        )
        cooling_kw = applied_cooling_fraction * MAX_COOLING_KW
        flow_heat_transfer_kw = calculate_flow_heat_transfer_kw(
            MASS_FLOW_KG_S,
            supply_c,
            return_c,
        )
        samples.append(
            {
                "controller": controller_name,
                "anti_windup_enabled": anti_windup_enabled,
                "time_s": time_s,
                "supply_temperature_c": supply_c,
                "return_temperature_c": return_c,
                "setpoint_c": SETPOINT_C,
                "control_error_c": error_c,
                "proportional_term": proportional_term,
                "integral_error_c_s": integral_error_c_s,
                "integral_term": integral_term,
                "unrestricted_command": unrestricted_command,
                "heat_load_kw": heat_load_kw,
                "mass_flow_kg_s": MASS_FLOW_KG_S,
                "flow_heat_transfer_kw": flow_heat_transfer_kw,
                "requested_cooling_fraction": requested_cooling_fraction,
                "applied_cooling_fraction": applied_cooling_fraction,
                "cooling_kw": cooling_kw,
                "energy_residual_kj": energy_residual_kj,
            }
        )

        if step == number_of_steps:
            break

        next_supply_c, next_return_c = update_supply_return_temperatures(
            supply_temperature_c=supply_c,
            return_temperature_c=return_c,
            mass_flow_kg_s=MASS_FLOW_KG_S,
            heat_load_kw=heat_load_kw,
            cooling_kw=cooling_kw,
            supply_water_mass_kg=SUPPLY_WATER_MASS_KG,
            return_water_mass_kg=RETURN_WATER_MASS_KG,
            dt_s=dt_s,
        )
        stored_energy_change_kj = WATER_SPECIFIC_HEAT_KJ_PER_KG_C * (
            SUPPLY_WATER_MASS_KG * (next_supply_c - supply_c)
            + RETURN_WATER_MASS_KG * (next_return_c - return_c)
        )
        external_energy_change_kj = (heat_load_kw - cooling_kw) * dt_s
        energy_residual_kj = stored_energy_change_kj - external_energy_change_kj

        supply_c = next_supply_c
        return_c = next_return_c
        integral_error_c_s = next_integral_error_c_s

    return samples


def calculate_metrics(
    samples: list[dict[str, float | str | bool]],
) -> dict[str, float | None]:
    """Return saturation, recovery, error, and conservation metrics."""
    if len(samples) < 2:
        raise ValueError("At least two samples are required.")

    dt_s = float(samples[1]["time_s"]) - float(samples[0]["time_s"])
    after_overload = [
        sample for sample in samples
        if float(sample["time_s"]) >= OVERLOAD_START_TIME_S
    ]
    after_recovery = [
        sample for sample in samples
        if float(sample["time_s"]) >= LOAD_RECOVERY_TIME_S
    ]
    recovery_errors = [float(sample["control_error_c"]) for sample in after_recovery]

    saturation_release_time_s: float | None = None
    for sample in after_recovery:
        if float(sample["applied_cooling_fraction"]) < 1.0 - SATURATION_TOLERANCE:
            saturation_release_time_s = (
                float(sample["time_s"]) - LOAD_RECOVERY_TIME_S
            )
            break

    recovery_settling_time_s: float | None = None
    for index, sample in enumerate(after_recovery):
        if all(
            abs(float(item["control_error_c"])) <= RECOVERY_BAND_C
            for item in after_recovery[index:]
        ):
            recovery_settling_time_s = (
                float(sample["time_s"]) - LOAD_RECOVERY_TIME_S
            )
            break

    return {
        "maximum_supply_temperature_c": max(
            float(sample["supply_temperature_c"]) for sample in after_overload
        ),
        "minimum_recovery_supply_temperature_c": min(
            float(sample["supply_temperature_c"]) for sample in after_recovery
        ),
        "recovery_undershoot_c": max(0.0, -min(recovery_errors)),
        "saturation_release_time_s": saturation_release_time_s,
        "recovery_settling_time_s": recovery_settling_time_s,
        "recovery_integrated_absolute_error_c_s": sum(
            abs(error) * dt_s for error in recovery_errors[:-1]
        ),
        "maximum_integral_error_c_s": max(
            float(sample["integral_error_c_s"]) for sample in after_overload
        ),
        "saturated_duration_s": sum(
            dt_s
            for sample in after_overload[:-1]
            if float(sample["applied_cooling_fraction"])
            >= 1.0 - SATURATION_TOLERANCE
        ),
        "maximum_cooling_fraction": max(
            float(sample["applied_cooling_fraction"]) for sample in samples
        ),
        "final_error_c": float(samples[-1]["control_error_c"]),
        "maximum_energy_residual_kj": max(
            abs(float(sample["energy_residual_kj"])) for sample in samples
        ),
    }


def evaluate_acceptance(
    no_aw_samples: list[dict[str, float | str | bool]],
    anti_windup_samples: list[dict[str, float | str | bool]],
    anti_windup_5_s_samples: list[dict[str, float | str | bool]],
) -> tuple[dict[str, bool], dict[str, float | None], dict[str, float | None]]:
    """Return defined Stage 5 checks and the 10-second metrics."""
    no_aw = calculate_metrics(no_aw_samples)
    anti_windup = calculate_metrics(anti_windup_samples)
    anti_windup_5_s = calculate_metrics(anti_windup_5_s_samples)
    timestep_difference_c = abs(
        float(anti_windup["final_error_c"])
        - float(anti_windup_5_s["final_error_c"])
    )
    anti_windup["timestep_final_error_difference_c"] = timestep_difference_c

    no_aw_release = no_aw["saturation_release_time_s"]
    aw_release = anti_windup["saturation_release_time_s"]
    no_aw_settling = no_aw["recovery_settling_time_s"]
    aw_settling = anti_windup["recovery_settling_time_s"]
    all_commands = [
        float(sample["applied_cooling_fraction"])
        for sample in no_aw_samples + anti_windup_samples
    ]

    checks = {
        "both controllers reach saturation": (
            float(no_aw["maximum_cooling_fraction"]) >= 1.0 - SATURATION_TOLERANCE
            and float(anti_windup["maximum_cooling_fraction"])
            >= 1.0 - SATURATION_TOLERANCE
        ),
        "bounded cooling commands": all(0.0 <= value <= 1.0 for value in all_commands),
        "anti-windup limits integral growth": (
            float(anti_windup["maximum_integral_error_c_s"])
            <= 0.6 * float(no_aw["maximum_integral_error_c_s"])
        ),
        "anti-windup releases saturation sooner": (
            aw_release is not None
            and no_aw_release is not None
            and float(aw_release) + 180.0 <= float(no_aw_release)
        ),
        "anti-windup reduces recovery error": (
            float(anti_windup["recovery_integrated_absolute_error_c_s"])
            <= 0.5 * float(no_aw["recovery_integrated_absolute_error_c_s"])
        ),
        "anti-windup limits recovery undershoot": (
            float(anti_windup["recovery_undershoot_c"]) <= 1.0
            and float(anti_windup["recovery_undershoot_c"])
            <= 0.3 * float(no_aw["recovery_undershoot_c"])
        ),
        "anti-windup recovery settles sooner": (
            aw_settling is not None
            and no_aw_settling is not None
            and float(aw_settling) + 60.0 <= float(no_aw_settling)
        ),
        "anti-windup final error": abs(float(anti_windup["final_error_c"])) <= 0.05,
        "energy conservation": max(
            float(no_aw["maximum_energy_residual_kj"]),
            float(anti_windup["maximum_energy_residual_kj"]),
        ) <= 1e-9,
        "anti-windup time-step sensitivity": timestep_difference_c <= 0.02,
    }
    return checks, no_aw, anti_windup


def write_results(
    no_aw_samples: list[dict[str, float | str | bool]],
    anti_windup_samples: list[dict[str, float | str | bool]],
    csv_path: Path,
) -> None:
    """Write aligned controller samples to one CSV file."""
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(no_aw_samples[0]))
        writer.writeheader()
        writer.writerows(no_aw_samples)
        writer.writerows(anti_windup_samples)


def write_summary(
    no_aw_metrics: dict[str, float | None],
    anti_windup_metrics: dict[str, float | None],
    csv_path: Path,
) -> None:
    """Write compact metrics for both Stage 5 controller cases."""
    metric_names = list(no_aw_metrics)
    metric_names.extend(name for name in anti_windup_metrics if name not in no_aw_metrics)
    fieldnames = ["controller", *metric_names]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"controller": "PI_NO_ANTI_WINDUP", **no_aw_metrics})
        writer.writerow({"controller": "PI_ANTI_WINDUP", **anti_windup_metrics})


def main() -> None:
    """Run, verify, report, and save the Stage 5A comparison."""
    no_aw_samples = run_experiment(False)
    anti_windup_samples = run_experiment(True)
    anti_windup_5_s_samples = run_experiment(True, 5.0)
    checks, no_aw, anti_windup = evaluate_acceptance(
        no_aw_samples,
        anti_windup_samples,
        anti_windup_5_s_samples,
    )

    root = Path(__file__).resolve().parent
    results_path = root / "results" / "stage5.csv"
    summary_path = root / "results" / "stage5_summary.csv"
    write_results(no_aw_samples, anti_windup_samples, results_path)
    write_summary(no_aw, anti_windup, summary_path)

    def formatted_time(value: float | None) -> str:
        return "not achieved" if value is None else f"{float(value):.0f} s"

    print("Stage 5A: PI saturation and anti-windup recovery")
    print(
        "Saturation release after load recovery: "
        f"without {formatted_time(no_aw['saturation_release_time_s'])} | "
        f"with {formatted_time(anti_windup['saturation_release_time_s'])}"
    )
    print(
        "Recovery settling time: "
        f"without {formatted_time(no_aw['recovery_settling_time_s'])} | "
        f"with {formatted_time(anti_windup['recovery_settling_time_s'])}"
    )
    print(
        "Recovery undershoot: "
        f"without {float(no_aw['recovery_undershoot_c']):.3f} C | "
        f"with {float(anti_windup['recovery_undershoot_c']):.3f} C"
    )
    print(
        "Maximum integral state: "
        f"without {float(no_aw['maximum_integral_error_c_s']):.1f} C s | "
        f"with {float(anti_windup['maximum_integral_error_c_s']):.1f} C s"
    )
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(checks.values()):
        raise RuntimeError("Stage 5A acceptance checks did not all pass.")
    print(f"Saved: {results_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
