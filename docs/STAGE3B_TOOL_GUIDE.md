# Stage 3B MATLAB and Simulink Tool Guide

## MATLAB

MATLAB runs commands, reads CSV data, compares numerical results, creates plots,
and reports pass/fail evidence. Set the repository as MATLAB's Current Folder,
then run:

```matlab
addpath("matlab")
run_stage3b_validation
```

The command runs the saved Simulink model and compares its output with
`results/stage3.csv`.

## Simulink

Simulink represents the equations as connected blocks. Open the model with:

```matlab
open_system("matlab/stage3b_chilled_water.slx")
```

The main blocks are:

- `Unit Delay`: stores the previous CHWS or CHWR value for one 10-second step.
- `Step`: changes the building load from 30 to 50 kW at 600 seconds.
- `Sum`: calculates temperature error and net heat rates.
- `Gain`: applies `Kp`, cooling capacity, flow heat transfer, and thermal mass.
- `Saturation`: limits cooling demand to the 0-to-100% range.
- `To Workspace`: sends model signals back to MATLAB for comparison.

Click **Run** in Simulink to execute the model. The Stop Time is 1800 seconds of
simulated time; it does not wait for 30 minutes of real time.

## Rebuilding the model

The `.slx` model is generated from code so every block and parameter is
reproducible:

```matlab
addpath("matlab")
build_stage3b_model
```

Run this after intentionally changing the builder. It replaces the generated
`.slx` file with a new model using the parameters in the script.

## Reading the validation result

`run_stage3b_validation` creates:

- `results/stage3b_comparison.csv`: every Python and Simulink sample.
- `results/stage3b_summary.csv`: maximum errors and pass/fail status.
- `docs/stage3b-python-simulink-comparison.png`: visual comparison.

`Cross-validation: PASS` means both temperature traces remain within the stated
acceptance limit. It proves consistent implementation across the two tools; it
does not prove agreement with real equipment.
