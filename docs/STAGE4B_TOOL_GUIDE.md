# Stage 4B Tool Guide

## MATLAB and Simulink

MATLAB runs the build and validation scripts. Simulink stores the same PI
controller and two-node plant equations as connected engineering blocks.

Close any open copy of `stage4b_pi_control` before rebuilding it. From MATLAB,
run:

```matlab
addpath("matlab")
build_stage4b_model
run_stage4b_validation
```

`build_stage4b_model` creates `matlab/stage4b_pi_control.slx` and closes it.
`run_stage4b_validation` opens the model in memory, simulates 30 minutes in
10-second steps, compares it with Python, writes evidence, and closes it again.

To inspect the finished block diagram:

```matlab
open_system("matlab/stage4b_pi_control.slx")
```

`1/z` is a `Unit Delay`: its output is the value saved from the previous
controller scan. CHWS, CHWR, and the integral error are state variables, so each
has a delay block.

## VS Code and Python

In the VS Code PowerShell terminal, run the complete Python suite with:

```powershell
python -m unittest discover -s tests -v
```

The Stage 4B tests read the MATLAB-generated CSV files. They do not run MATLAB;
this keeps the Python test suite fast while preserving the independent result.

Use `Ctrl+P` in VS Code to inspect:

- `matlab/build_stage4b_model.m`: block creation and signal connections.
- `matlab/run_stage4b_validation.m`: cross-tool assertions and plots.
- `results/stage4b_comparison.csv`: all aligned samples and differences.
- `results/stage4b_summary.csv`: maximum differences and pass/fail result.
- `tests/test_stage4b.py`: independent evidence checks.

## Git

Git records the scripts, generated model, comparison data, plot, documentation,
and tests together. The commit should be created only after MATLAB assertions
and all Python tests pass. Uploading to GitHub remains a separate user-approved
step.
