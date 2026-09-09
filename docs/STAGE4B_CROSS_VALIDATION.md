# Stage 4B Python-Simulink PI Cross-Validation

## Purpose

Stage 4B checks whether a separately assembled Simulink block model reproduces
the Stage 4A Python PI response. It changes the implementation tool while
retaining the same plant boundary, equations, controller gains, initial
conditions, load disturbance, sample time, and simulation duration.

## Compared signals and acceptance criterion

The validation aligns all 181 samples from 0 to 1800 s and compares:

- CHWS temperature, in degC.
- CHWR temperature, in degC.
- Applied cooling fraction, from 0 to 1.
- Integral-error state, in degC s.

The maximum absolute difference for every signal must be no greater than
`1e-9` in that signal's native units. Timestamp differences must be no greater
than `1e-12 s`.

## Simulink structure

The controller uses these standard blocks:

- `Sum` calculates `CHWS - setpoint`.
- `Gain` blocks calculate `Kp * error`, `Ki * integral state`, and
  `error * dt`.
- `Unit Delay` stores the integral state from one 10-second scan to the next.
- `Sum` combines the P and I contributions.
- `Saturation` limits the cooling request to 0 through 1.

The supply and return energy-balance blocks are retained from Stage 3B. A second
pair of `Unit Delay` blocks stores CHWS and CHWR.

## Scope of anti-windup evidence

The defined 30 to 50 kW experiment reaches a maximum PI command of about 52.6%,
so output saturation does not occur. The Simulink trace therefore validates the
normal unsaturated PI calculation and integral-state timing. It does not claim
to cross-validate conditional anti-windup.

Stage 4A Python tests separately exercise high saturation, frozen integration,
and integration that drives the command back toward the available range. A
future saturation experiment would be required before claiming cross-tool
anti-windup agreement.

## Reproducibility and evidence

`matlab/build_stage4b_model.m` generates the reviewable `.slx` file.
`matlab/run_stage4b_validation.m` runs it, imports the PI rows from
`results/stage4.csv`, asserts the limits, and writes:

- `results/stage4b_comparison.csv`.
- `results/stage4b_summary.csv`.
- `docs/stage4b-python-simulink-comparison.png`.

Two Python tests independently read the preserved MATLAB CSV files and enforce
the same sample count and signal-difference limits.

## Interpretation and limitations

Agreement supports consistent transfer of the documented discrete PI and
two-node energy-balance equations between Python and Simulink. It reduces the
risk of a tool-specific implementation or timing error.

Both tools still share the same simplified assumptions. Agreement is not
validation against real plant data and does not address sensors, actuator
dynamics, transport delays, changing flow, equipment cycling, or robustness to
model uncertainty.
