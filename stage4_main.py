"""Compare proportional and proportional-integral chilled-water control."""

import csv
from pathlib import Path

from controller import (
    apply_cooling_permission,
    proportional_control,
    proportional_integral_control,
)
from plant import (
    WATER_SPECIFIC_HEAT_KJ_PER_KG_C,
    calculate_flow_heat_transfer_kw,
    update_supply_return_temperatures,
)
from stage3_main import (
    DEFAULT_TIME_STEP_S,
    FINAL_HEAT_LOAD_KW,
    INITIAL_HEAT_LOAD_KW,
    KP,
    LOAD_STEP_TIME_S,
    MASS_FLOW_KG_S,
    MAX_COOLING_KW,
    RETURN_WATER_MASS_KG,
    SETPOINT_C,
    SIMULATION_TIME_S,
    SUPPLY_WATER_MASS_KG,
    analytical_steady_state,
    heat_load_profile_kw,
)


PI_KI_PER_S = 0.001
SETTLING_BAND_C = 0.1
PI_FINAL_ERROR_LIMIT_C = 0.05
PI_OVERSHOOT_LIMIT_C = 0.2
PI_IAE_RATIO_LIMIT = 0.25


def _initial_conditions(controller_name: str) -> tuple[float, float, float]:
    """Return balanced CHWS, CHWR, and integral state for one controller."""
    if controller_name == "P":
        supply_c, return_c = analytical_steady_state(INITIAL_HEAT_LOAD_KW)
        return supply_c, return_c, 0.0
    if controller_name == "PI":
        supply_c = SETPOINT_C
        return_c = supply_c + INITIAL_HEAT_LOAD_KW / (
            MASS_FLOW_KG_S * WATER_SPECIFIC_HEAT_KJ_PER_KG_C
        )
        initial_cooling_fraction = INITIAL_HEAT_LOAD_KW / MAX_COOLING_KW
        integral_error_c_s = initial_cooling_fraction / PI_KI_PER_S
        return supply_c, return_c, integral_error_c_s
    raise ValueError("controller_name must be 'P' or 'PI'.")


def _control_scan(
    controller_name: str,
    supply_temperature_c: float,
    integral_error_c_s: float,
    dt_s: float,
) -> tuple[float, float, float, float]:
    """Return command, next integral state, P term, and current I term."""
    error_c = supply_temperature_c - SETPOINT_C
    proportional_term = KP * error_c

    if controller_name == "P":
        command = proportional_control(supply_temperature_c, SETPOINT_C, KP)
        return command, integral_error_c_s, proportional_term, 0.0

    command, next_integral_error_c_s = proportional_integral_control(
        temperature_c=supply_temperature_c,
        setpoint_c=SETPOINT_C,
        kp=KP,
        ki_per_s=PI_KI_PER_S,
        integral_error_c_s=integral_error_c_s,
        dt_s=dt_s,
    )
    integral_term = PI_KI_PER_S * integral_error_c_s
    return (
        command,
        next_integral_error_c_s,
        proportional_term,
        integral_term,
    )


def run_experiment(
    controller_name: str,
    dt_s: float = DEFAULT_TIME_STEP_S,
) -> list[dict[str, float | str]]:
    """Return one controller response to the defined Stage 3 load disturbance."""
    if controller_name not in ("P", "PI"):
        raise ValueError("controller_name must be 'P' or 'PI'.")
    if dt_s <= 0.0 or SIMULATION_TIME_S % dt_s != 0.0:
        raise ValueError("dt_s must be positive and divide the simulation time exactly.")

    supply_c, return_c, integral_error_c_s = _initial_conditions(controller_name)
    samples: list[dict[str, float | str]] = []
    energy_residual_kj = 0.0
    number_of_steps = int(SIMULATION_TIME_S / dt_s)

    for step in range(number_of_steps + 1):
        time_s = step * dt_s
        heat_load_kw = heat_load_profile_kw(time_s)
        (
            requested_cooling_fraction,
            next_integral_error_c_s,
            proportional_term,
            integral_term,
        ) = _control_scan(
            controller_name,
            supply_c,
            integral_error_c_s,
            dt_s,
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
                "time_s": time_s,
                "supply_temperature_c": supply_c,
                "return_temperature_c": return_c,
                "setpoint_c": SETPOINT_C,
                "control_error_c": supply_c - SETPOINT_C,
                "proportional_term": proportional_term,
                "integral_error_c_s": integral_error_c_s,
                "integral_term": integral_term,
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
    samples: list[dict[str, float | str]],
) -> dict[str, float | None]:
    """Return setpoint-response and control-effort metrics after the load step."""
    if len(samples) < 2:
        raise ValueError("At least two samples are required.")

    dt_s = float(samples[1]["time_s"]) - float(samples[0]["time_s"])
    post_step = [
        sample for sample in samples if float(sample["time_s"]) >= LOAD_STEP_TIME_S
    ]
    final = post_step[-1]
    errors_c = [float(sample["control_error_c"]) for sample in post_step]
    commands = [float(sample["applied_cooling_fraction"]) for sample in post_step]
    settling_time_s: float | None = None

    for index, sample in enumerate(post_step):
        if all(
            abs(float(item["control_error_c"])) <= SETTLING_BAND_C
            for item in post_step[index:]
        ):
            settling_time_s = float(sample["time_s"]) - LOAD_STEP_TIME_S
            break

    return {
        "final_supply_c": float(final["supply_temperature_c"]),
        "final_return_c": float(final["return_temperature_c"]),
        "final_error_c": float(final["control_error_c"]),
        "peak_absolute_error_c": max(abs(error) for error in errors_c),
        "overshoot_c": max(0.0, -min(errors_c)),
        "settling_time_s": settling_time_s,
        "integrated_absolute_error_c_s": sum(
            abs(error) * dt_s for error in errors_c[:-1]
        ),
        "maximum_cooling_fraction": max(commands),
        "control_output_total_variation": sum(
            abs(current - previous)
            for previous, current in zip(commands, commands[1:])
        ),
        "maximum_energy_residual_kj": max(
            abs(float(sample["energy_residual_kj"])) for sample in samples
        ),
    }


def evaluate_acceptance(
    p_samples: list[dict[str, float | str]],
    pi_samples: list[dict[str, float | str]],
    pi_5_s_samples: list[dict[str, float | str]],
) -> tuple[dict[str, bool], dict[str, float | None], dict[str, float | None]]:
    """Return named acceptance checks and the 10-second controller metrics."""
    p_metrics = calculate_metrics(p_samples)
    pi_metrics = calculate_metrics(pi_samples)
    pi_5_s_metrics = calculate_metrics(pi_5_s_samples)
    pi_timestep_difference_c = abs(
        float(pi_metrics["final_supply_c"])
        - float(pi_5_s_metrics["final_supply_c"])
    )

    all_commands = [
        float(sample["applied_cooling_fraction"])
        for sample in p_samples + pi_samples
    ]
    checks = {
        "bounded cooling command": all(0.0 <= value <= 1.0 for value in all_commands),
        "energy conservation": max(
            float(p_metrics["maximum_energy_residual_kj"]),
            float(pi_metrics["maximum_energy_residual_kj"]),
        )
        <= 1e-9,
        "PI final setpoint error": abs(float(pi_metrics["final_error_c"]))
        <= PI_FINAL_ERROR_LIMIT_C,
        "PI overshoot": float(pi_metrics["overshoot_c"]) <= PI_OVERSHOOT_LIMIT_C,
        "PI settling": pi_metrics["settling_time_s"] is not None,
        "PI integrated error improvement": float(
            pi_metrics["integrated_absolute_error_c_s"]
        )
        <= PI_IAE_RATIO_LIMIT
        * float(p_metrics["integrated_absolute_error_c_s"]),
        "PI time-step sensitivity": pi_timestep_difference_c <= 0.02,
    }
    pi_metrics["timestep_final_supply_difference_c"] = pi_timestep_difference_c
    return checks, p_metrics, pi_metrics


def write_results(
    p_samples: list[dict[str, float | str]],
    pi_samples: list[dict[str, float | str]],
    csv_path: Path,
) -> None:
    """Write aligned P and PI samples to one traceable CSV file."""
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(p_samples[0]))
        writer.writeheader()
        writer.writerows(p_samples)
        writer.writerows(pi_samples)


def write_summary(
    p_metrics: dict[str, float | None],
    pi_metrics: dict[str, float | None],
    csv_path: Path,
) -> None:
    """Write one compact metric row for each controller."""
    metric_names = list(p_metrics)
    metric_names.extend(name for name in pi_metrics if name not in p_metrics)
    fieldnames = ["controller", *metric_names]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"controller": "P", **p_metrics})
        writer.writerow({"controller": "PI", **pi_metrics})


def main() -> None:
    """Run, verify, report, and save the Stage 4A comparison."""
    p_samples = run_experiment("P")
    pi_samples = run_experiment("PI")
    pi_5_s_samples = run_experiment("PI", 5.0)
    checks, p_metrics, pi_metrics = evaluate_acceptance(
        p_samples,
        pi_samples,
        pi_5_s_samples,
    )

    root = Path(__file__).resolve().parent
    results_path = root / "results" / "stage4.csv"
    summary_path = root / "results" / "stage4_summary.csv"
    write_results(p_samples, pi_samples, results_path)
    write_summary(p_metrics, pi_metrics, summary_path)

    iae_reduction_percent = 100.0 * (
        1.0
        - float(pi_metrics["integrated_absolute_error_c_s"])
        / float(p_metrics["integrated_absolute_error_c_s"])
    )
    settling_time_s = pi_metrics["settling_time_s"]
    settling_text = (
        "not achieved"
        if settling_time_s is None
        else f"{float(settling_time_s):.0f} s"
    )
    print("Stage 4A: proportional versus PI control")
    print(f"P final CHWS error: {float(p_metrics['final_error_c']):.3f} C")
    print(f"PI final CHWS error: {float(pi_metrics['final_error_c']):.3f} C")
    print(f"PI settling time within +/-0.1 C: {settling_text}")
    print(f"PI overshoot: {float(pi_metrics['overshoot_c']):.3f} C")
    print(f"Integrated absolute error reduction: {iae_reduction_percent:.1f}%")
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(checks.values()):
        raise RuntimeError("Stage 4A acceptance checks did not all pass.")
    print(f"Saved: {results_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
