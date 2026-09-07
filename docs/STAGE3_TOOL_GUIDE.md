# Stage 3 Tool Guide

This guide explains what each project tool does and how to use it from the
project folder in the VS Code PowerShell terminal.

## VS Code

VS Code is the editor used to read the Python code, documentation, test files,
CSV results, and Git changes.

Open the project from PowerShell:

```powershell
code .
```

Use `Ctrl+P` to open a file by name. Useful Stage 3 files are `plant.py`,
`stage3_main.py`, `tests/test_stage3.py`, and
`docs/STAGE3_ENGINEERING_BASIS.md`.

## Python simulation

Python performs the repeated energy-balance calculations. Run the Stage 3
experiment with:

```powershell
python stage3_main.py
```

The terminal shows the final CHWS and CHWR temperatures, settling time,
energy-conservation residual, time-step comparison, and PASS/FAIL results. The
program also writes `results/stage3.csv`.

## Automated tests

Python's built-in `unittest` tool checks expected behaviour automatically:

```powershell
python -m unittest discover -s tests -v
```

Read the final lines first. `Ran 32 tests` followed by `OK` means all current
Stage 1, Stage 2, and Stage 3 tests passed. A failure identifies the test name,
expected result, and actual result.

## CSV results

`results/stage3.csv` is the numerical evidence. Each row represents one
simulation sample. The main columns are:

- `time_s`: simulated time in seconds.
- `supply_temperature_c`: CHWS temperature.
- `return_temperature_c`: CHWR temperature.
- `heat_load_kw`: building heat input.
- `flow_heat_transfer_kw`: heat carried by water flow.
- `cooling_kw`: heat removed by the chiller.
- `energy_residual_kj`: error in the total-energy check.

Open the file in VS Code or Excel. At `time_s = 600`, confirm that
`heat_load_kw` changes from 30 to 50 kW. The temperatures then move toward the
new steady state.

## Result plot

Generate the engineering plot from the CSV with:

```powershell
python plot_stage3.py
```

The output is `docs/stage3-load-step-results.svg`. Open it in a browser or use
VS Code's image preview. The upper panel shows CHWS and CHWR; the lower panel
compares building load, chiller cooling, and flow-carried heat.

## Git checks

Git records what changed and preserves the engineering development history.

Show the current branch and any uncommitted files:

```powershell
git status --short --branch
```

Review code and documentation changes before a commit:

```powershell
git diff
```

Show recent commits:

```powershell
git --no-pager log --oneline -5
```

`git commit` saves a local version. `git push` publishes commits to GitHub and
should only be run after the local result has been reviewed.

## Interview checkpoint

Be able to explain these four points in your own words:

1. Python repeats the two energy-balance equations over time.
2. Tests compare the code with expected physical and numerical behaviour.
3. CSV preserves the numerical evidence behind the plot.
4. Git preserves the history of the engineering decisions and implementation.
