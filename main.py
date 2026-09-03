"""Run a 30-minute water-temperature control simulation and save the results."""

import csv
from pathlib import Path

from controller import proportional_control
from plant import update_temperature


# Fixed Stage 1 settings. Include units in names to make calculations clear.
INITIAL_TEMPERATURE_C = 14.0
SETPOINT_C = 7.0
KP = 0.3
HEAT_LOAD_KW = 30.0
MAX_COOLING_KW = 100.0
WATER_MASS_KG = 1000.0
TIME_STEP_S = 10.0
NUMBER_OF_STEPS = 180


def main() -> None:
    """Repeat the control loop, print progress, and save the simulation data."""
    temperature_c = INITIAL_TEMPERATURE_C
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    csv_path = results_dir / "stage1.csv"

    print("Stage 1: chilled-water temperature + proportional control")
    print(f"Setpoint: {SETPOINT_C:.1f} C | Heat load: {HEAT_LOAD_KW:.1f} kW")
    print(f"{'Time (min)':>10} {'Water (C)':>12} {'Cooling (%)':>14}")

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["time_s", "temperature_c", "setpoint_c", "cooling_fraction"])

        # Record 180 temperature updates plus the initial sample at t=0.
        for step in range(NUMBER_OF_STEPS + 1):
            time_s = step * TIME_STEP_S
            cooling_fraction = proportional_control(temperature_c, SETPOINT_C, KP)

            # Record the current temperature and the command for the next step.
            writer.writerow([time_s, temperature_c, SETPOINT_C, cooling_fraction])
            if step % 6 == 0 or step == NUMBER_OF_STEPS:
                print(f"{time_s / 60:10.1f} {temperature_c:12.3f} {cooling_fraction * 100:14.1f}")

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
    print(f"Final error: {temperature_c - SETPOINT_C:.3f} C above setpoint")
    print("A proportional-only controller needs an error to balance a constant heat load.")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
