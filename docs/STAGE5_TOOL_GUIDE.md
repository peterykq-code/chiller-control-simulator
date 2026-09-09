# Stage 5A Tool Guide

## VS Code

Open the project folder and inspect `stage5_main.py`. It defines the overload
profile, runs the protected and unprotected PI cases, calculates recovery
metrics, applies acceptance checks, and writes CSV evidence.

## Python

From the project root in a PowerShell terminal:

```powershell
python stage5_main.py
```

This produces `results/stage5.csv` and `results/stage5_summary.csv`. The detailed
CSV contains every 10-second sample. The summary contains the saturation,
integral-growth, recovery, conservation, and time-step metrics.

Regenerate the result figure with:

```powershell
python plot_stage5.py
```

Open the figure in VS Code with:

```powershell
code -r .\docs\stage5-anti-windup-results.svg
```

## Automated tests

Run all retained and new tests with:

```powershell
python -m unittest discover -s tests -v
```

Stage 5 tests confirm that the overload reaches full cooling, the protected
integrator stops growing in the saturated direction, the defined recovery
metrics improve, commands remain bounded, energy is conserved, and the result
is insensitive to the tested time-step change.

## Git

Inspect local changes with:

```powershell
git status --short --branch
git diff --check
git diff
```

`git status` lists changed files. `git diff --check` detects whitespace errors.
`git diff` shows the exact code and documentation changes before a commit.
