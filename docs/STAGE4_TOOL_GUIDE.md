# Stage 4A Tool Guide

## VS Code

VS Code is the editor used to inspect the Python controller, experiment, tests,
CSV evidence, and generated SVG figure. Press `Ctrl+P` and enter a filename to
open it quickly.

Start with these files:

- `controller.py`: P and PI calculations, validation, and anti-windup.
- `stage4_main.py`: common load disturbance, metrics, acceptance checks, and
  CSV output.
- `tests/test_stage4.py`: automated controller and experiment checks.
- `plot_stage4.py`: dependency-free evidence plot.

## Python

From the repository root in the VS Code PowerShell terminal, run:

```powershell
python stage4_main.py
python plot_stage4.py
python -m unittest discover -s tests -v
```

`stage4_main.py` performs the repeated 10-second calculations. It creates:

- `results/stage4.csv`: every P and PI sample and its engineering quantities.
- `results/stage4_summary.csv`: compact performance metrics.

`plot_stage4.py` reads those verified CSV files and creates:

- `docs/stage4-p-vs-pi-results.svg`.

The plot script uses only the Python standard library. SVG is a scalable image
format that remains clear when viewed in a browser or GitHub README.

## Reading the evidence

In the upper plot, the P trace remains above the 7 degC setpoint, while the PI
trace returns to the blue +/-0.1 degC settling band. In the lower plot, PI first
requests slightly more cooling, then approaches the 50% output needed to balance
the final 50 kW load.

In `stage4_summary.csv`:

- `final_error_c` shows the remaining setpoint error.
- `overshoot_c` shows how far temperature fell below setpoint.
- `settling_time_s` is blank when the controller never entered the band.
- `integrated_absolute_error_c_s` measures total post-step tracking error.
- `control_output_total_variation` records cumulative command movement.
- `maximum_energy_residual_kj` checks the retained plant energy balance.

## MATLAB and Simulink

Stage 4A is implemented and verified in Python. MATLAB and Simulink are not
required to run it. A later Stage 4B can recreate the PI controller and compare
its sample-by-sample response with this Python reference before PLC translation.
