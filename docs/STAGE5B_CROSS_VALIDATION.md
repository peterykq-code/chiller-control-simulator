# Stage 5B Python-Simulink Anti-Windup Cross-Validation

## Purpose

Stage 5B checks whether a separately assembled Simulink block model reproduces
the Stage 5A Python controller while conditional anti-windup is actively
holding and releasing the integral state. The plant, gains, initial conditions,
load profile, cooling limit, sample time, and duration remain identical.

## Exercised scenario

The plant starts balanced at a 30 kW load. At 600 s the load rises to 120 kW,
which exceeds the 100 kW cooling capacity and forces the controller to its upper
limit. At 1200 s the load returns to 30 kW, allowing the controller to recover.

The Simulink logic holds the integral state when either condition is true:

```text
unrestricted command >= 1 and error > 0
unrestricted command <= 0 and error < 0
```

Otherwise it applies `I_next = I + error * dt`. This matches the Python
conditional-integration rule.

## Compared signals and acceptance criterion

The validation aligns all 361 samples from 0 to 3600 s and compares:

- CHWS temperature, in degC.
- CHWR temperature, in degC.
- Applied cooling fraction, from 0 to 1.
- Integral-error state, in degC s.

The maximum absolute difference for every signal must be no greater than
`1e-9` in that signal's native units. Timestamp differences must be no greater
than `1e-12 s`.

The validation also checks two Stage 5A recovery results: the protected
controller must leave high saturation 160 s after load recovery and limit the
CHWS undershoot to approximately 0.612 degC.

## Simulink structure

Standard `Relational Operator`, `Logical Operator`, and `Switch` blocks decide
whether the `Unit Delay` holding the integral state receives its current value
or the candidate updated value. The P and I paths then feed `Sum` and
`Saturation` blocks. The two-node CHWS/CHWR energy balance is retained from
Stage 3B.

## Reproducibility and evidence

`matlab/build_stage5b_model.m` generates the reviewable `.slx` file.
`matlab/run_stage5b_validation.m` runs it, imports the protected PI rows from
`results/stage5.csv`, asserts the limits, and writes:

- `results/stage5b_comparison.csv`.
- `results/stage5b_summary.csv`.
- `docs/stage5b-python-simulink-comparison.png`.

Two Python tests independently read the preserved MATLAB CSV files and enforce
the sample count, signal limits, saturation-release time, and undershoot.

## Interpretation and limitations

Agreement supports consistent transfer of the exercised conditional-integration
logic, discrete state timing, and two-node plant equations between Python and
Simulink. It reduces the risk of a tool-specific implementation error.

Both implementations retain the same ideal deterministic assumptions. This is
not validation against plant data and does not establish freezing protection,
safe equipment operation, controller robustness, or commissioning performance.
