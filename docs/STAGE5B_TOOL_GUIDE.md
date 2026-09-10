# Stage 5B Tool Guide

## MATLAB and Simulink

MATLAB builds and runs the model; Simulink provides the independent block-based
implementation of the exercised PI anti-windup controller and two-node plant.

Close any open copy of `stage5b_pi_anti_windup` before rebuilding it. From
MATLAB, run:

```matlab
addpath("matlab")
build_stage5b_model
run_stage5b_validation
```

The model simulates 60 minutes in 10-second steps. The overload starts at
10 minutes and recovery starts at 20 minutes. The validation compares every
sample with the protected PI rows in `results/stage5.csv`.

To inspect the finished block diagram:

```matlab
open_system("matlab/stage5b_pi_anti_windup.slx")
```

The `Relational Operator` and `Logical Operator` blocks identify saturation
that the current error would worsen. The `Switch` then either holds the current
integral state or passes the candidate `I + error * dt` value to its `1/z`
storage block.

## VS Code and Python

In the VS Code PowerShell terminal, run the complete suite with:

```powershell
python -m unittest discover -s tests -v
```

The Stage 5B tests read the MATLAB-generated evidence files. Use `Ctrl+P` in VS
Code to inspect:

- `matlab/build_stage5b_model.m`: blocks and signal connections.
- `matlab/run_stage5b_validation.m`: assertions, metrics, and plot generation.
- `results/stage5b_comparison.csv`: all aligned samples and differences.
- `results/stage5b_summary.csv`: maximum differences and pass/fail result.
- `tests/test_stage5b.py`: independent preserved-evidence checks.

## Git

Git records the scripts, generated model, comparison data, plot, documentation,
and tests together. The release script commits only after MATLAB assertions and
all Python tests pass. Uploading to GitHub remains a separate user-approved
step.
