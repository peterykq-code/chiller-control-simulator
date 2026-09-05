"""Run a 30-minute chiller state-and-temperature simulation."""

import csv
from pathlib import Path

from controller import (
    apply_cooling_permission,
    proportional_control,
    update_equipment_state,
)
from plant import update_temperature


# Fixed experiment settings. Include units in names to make calculations clear.
INITIAL_TEMPERATURE_C = 14.0
SETPOINT_C = 7.0
KP = 0.3
HEAT_LOAD_KW = 30.0
MAX_COOLING_KW = 100.0
WATER_MASS_KG = 1000.0
TIME_STEP_S = 10.0
NUMBER_OF_STEPS = 180
STARTUP_TIMEOUT_S = 30.0

# Deterministic educational scenario. Commands are one-scan pulses.
START_COMMAND_TIMES_S = (60.0, 720.0)
STOP_COMMAND_TIME_S = 600.0
FLOW_PROOF_PERIODS_S = ((80.0, 600.0), (740.0, 890.0), (950.0, 960.0))
RESET_COMMAND_TIME_S = 960.0


def scenario_inputs(time_s: float) -> tuple[bool, bool, bool, bool]:
    """Return start, stop, flow, and reset inputs for the demonstration."""
    start_command = time_s in START_COMMAND_TIMES_S
    stop_command = time_s == STOP_COMMAND_TIME_S
    flow_proven = any(start <= time_s <= end for start, end in FLOW_PROOF_PERIODS_S)
    reset_command = time_s == RESET_COMMAND_TIME_S
    return start_command, stop_command, flow_proven, reset_command


def main() -> None:
    """Run the control loop, print state changes, and save simulation data."""
    temperature_c = INITIAL_TEMPERATURE_C
    equipment_state = "OFF"
    startup_elapsed_s = 0.0
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / "stage2.csv"

    print("Stage 2: chiller operating sequence and cooling permission")
    print(f"Setpoint: {SETPOINT_C:.1f} C | Heat load: {HEAT_LOAD_KW:.1f} kW")
    print(
        f"{'Time (min)':>10} {'Water (C)':>11} {'State':>10} "
        f"{'Request (%)':>13} {'Cooling (%)':>13}"
    )

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "time_s",
            "temperature_c",
            "setpoint_c",
            "equipment_state",
            "requested_cooling_fraction",
            "cooling_fraction",
            "start_command",
            "stop_command",
            "flow_proven",
            "reset_command",
        ])

        for step in range(NUMBER_OF_STEPS + 1):
            time_s = step * TIME_STEP_S
            start_command, stop_command, flow_proven, reset_command = scenario_inputs(time_s)

            if equipment_state == "STARTING":
                startup_elapsed_s += TIME_STEP_S
            else:
                startup_elapsed_s = 0.0
            startup_timed_out = startup_elapsed_s >= STARTUP_TIMEOUT_S

            previous_state = equipment_state
            equipment_state = update_equipment_state(
                current_state=equipment_state,
                start_command=start_command,
                stop_command=stop_command,
                flow_proven=flow_proven,
                startup_timed_out=startup_timed_out,
                reset_command=reset_command,
            )
            if equipment_state != "STARTING":
                startup_elapsed_s = 0.0

            requested_cooling_fraction = proportional_control(
                temperature_c, SETPOINT_C, KP,
            )
            cooling_fraction = apply_cooling_permission(
                requested_cooling_fraction, equipment_state,
            )

            writer.writerow([
                time_s,
                temperature_c,
                SETPOINT_C,
                equipment_state,
                requested_cooling_fraction,
                cooling_fraction,
                start_command,
                stop_command,
                flow_proven,
                reset_command,
            ])

            state_changed = equipment_state != previous_state
            if step % 6 == 0 or state_changed or step == NUMBER_OF_STEPS:
                print(
                    f"{time_s / 60:10.1f} {temperature_c:11.3f} "
                    f"{equipment_state:>10} {requested_cooling_fraction * 100:13.1f} "
                    f"{cooling_fraction * 100:13.1f}"
                )

            if step < NUMBER_OF_STEPS:
                temperature_c = update_temperature(
                    temperature_c=temperature_c,
                    cooling_fraction=cooling_fraction,
                    heat_load_kw=HEAT_LOAD_KW,
                    max_cooling_kw=MAX_COOLING_KW,
                    water_mass_kg=WATER_MASS_KG,
                    dt_s=TIME_STEP_S,
                )

    print(f"\nFinal temperature: {temperature_c:.3f} C")
    print(f"Final state: {equipment_state}")
    print("Cooling is applied only while the equipment state is RUNNING.")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
