# Stage 3B Python-Simulink Cross-Validation

## Purpose

Stage 3B independently recreates the Stage 3A chilled-water equations in
Simulink and compares every CHWS and CHWR sample with the Python reference.
This checks that the model behaviour follows the stated engineering equations
rather than one software implementation alone.

## Requirement and acceptance criterion

The Simulink model must use the same boundary, parameters, 10-second sample
time, initial state, controller, and 30-to-50 kW load step as Python Stage 3A.
It must produce 181 samples from 0 to 1800 seconds. Maximum absolute CHWS and
CHWR differences must each be no greater than `1e-9 degC`.

## Model structure

The generated model `matlab/stage3b_chilled_water.slx` contains:

- Two `Unit Delay` blocks for the discrete CHWS and CHWR states.
- A `Step` block for the 30-to-50 kW building load disturbance.
- `Sum` and `Gain` blocks for the supply and return energy balances.
- A proportional controller with `Gain` and `Saturation` blocks.
- `To Workspace` blocks that export temperatures and heat rates for validation.

The implementation follows:

```text
Q_flow = m_dot * Cp * (T_return - T_supply)
next_T_supply = T_supply + (Q_flow - Q_chiller) * dt / (M_supply * Cp)
next_T_return = T_return + (Q_load - Q_flow) * dt / (M_return * Cp)
```

## Reproduction

From MATLAB, with the repository as the current folder:

```matlab
addpath("matlab")
build_stage3b_model
run_stage3b_validation
```

The first command creates the `.slx` file. The second runs Simulink, imports
`results/stage3.csv`, compares every temperature sample, asserts the acceptance
limit, and writes CSV and PNG evidence.

## Evidence outputs

- `matlab/stage3b_chilled_water.slx`: reviewable Simulink block model.
- `results/stage3b_comparison.csv`: sample-by-sample Python and Simulink values.
- `results/stage3b_summary.csv`: maximum differences and pass/fail result.
- `docs/stage3b-python-simulink-comparison.png`: comparison plot.

## Limitations

Cross-validation checks agreement between two implementations of the same
equations. It does not validate those equations against real plant measurements.
Both implementations retain the same two-node, constant-flow, instantaneous
control, and fixed-parameter assumptions documented in Stage 3A.
