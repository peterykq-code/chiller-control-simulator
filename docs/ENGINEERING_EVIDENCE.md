# Engineering Evidence Register

## Purpose

This register links technical claims to reviewable project evidence. It supports
portfolio explanations and later private competency mapping. It is not an
Engineers Australia assessment outcome or a claim that a competency has been
demonstrated to a required level.

Each major feature should preserve this chain:

```text
Requirement -> theory -> engineering decision -> implementation
            -> test -> result -> interpretation
```

## EV-CHILLER-S1-001 — Water-temperature model and proportional control

- **Status:** Implemented and tested in the Stage 1 baseline commit.
- **Requirement:** Simulate a defined water mass under heat load and bounded
  cooling, then calculate a proportional cooling request from temperature error.
- **Theory:** `m * Cp * delta_T = (Q_load - Q_cooling) * delta_t` and
  `u = clamp(Kp * (T - T_set), 0, 1)`.
- **Engineering decision:** Begin with one transparent thermal state and an
  explicit time step before adding hydraulic and equipment detail.
- **Implementation:** `plant.py`, `controller.py`, and `main.py`.
- **Verification:** Ten automated tests cover direction, saturation, invalid
  inputs, one-step energy balance, and the connected Stage 1 response.
- **Result:** With a 30 kW load, 100 kW maximum cooling, and `Kp = 0.3 / degC`,
  the response settles near 8 degC for a 7 degC setpoint at about 30% cooling.
- **Interpretation:** The 1 degC offset is expected because proportional control
  needs that error to request the 30% cooling that balances the load.
- **Limitations:** One well-mixed water mass, fixed load and capacity,
  instantaneous cooling response, and no separate supply/return temperatures.

## EV-CHILLER-S2-001 — Equipment state sequence and cooling permission

- **Status:** Implemented and tested in the Stage 2 operating-sequence commit.
- **Requirement:** Prevent cooling until the equipment is ready, reproduce a
  start/stop sequence, and latch a fault when required chilled-water flow is lost.
- **Theory:** Sequential control separates continuous cooling demand from discrete
  equipment permission. Commands, permissives, timeout, and reset determine the
  state before the demand reaches the thermal model.
- **Engineering decision:** Use OFF, STARTING, RUNNING, and FAULT states. Permit
  cooling only in RUNNING, give flow loss priority over normal stop, and require
  restored flow plus reset before leaving FAULT.
- **Implementation:** `controller.py` and `main.py`.
- **Verification:** Fourteen Stage 2 tests cover permission, state transitions,
  scenario timing, and independent recalculation of every thermal step. The full
  suite contains 24 passing tests.
- **Result:** The 30-minute experiment records 181 samples and reproduces start,
  flow proof, normal stop, restart, flow loss, latched fault, restoration, and
  reset. It ends in OFF at approximately 14.862 degC.
- **Interpretation:** A 100% cooling request can result in 0% applied cooling while
  the equipment is OFF, STARTING, or FAULT. Demand and operating permission are
  therefore separate signals.
- **Limitations:** Flow is a scripted Boolean input. Pump status, alarm delay,
  anti-cycling, hydraulics, and site-specific reset requirements are not modelled.

## EV-CHILLER-S3-001 — Physics and validation foundation

- **Status:** Implemented and verified locally.
- **Requirement and acceptance criterion:** Represent mass-flow heat transfer
  with separate CHWS and CHWR states. For a reproducible 30 to 50 kW load step,
  final temperatures must be within 0.02 degC of the analytical steady state,
  the maximum total-energy residual must be at most `1e-9 kJ`, and 5 s versus
  10 s time steps must differ by at most 0.02 degC at the final sample.
- **Engineering question:** How should mass flow, chilled-water supply/return
  temperatures, thermal storage, and a load disturbance be represented within a
  defined system boundary?
- **Theory:** `Q_flow = m_dot * Cp * (T_return - T_supply)`,
  `M_supply * Cp * dT_supply/dt = Q_flow - Q_chiller`, and
  `M_return * Cp * dT_return/dt = Q_load - Q_flow`. Adding the two node
  balances cancels the internal flow term and gives total stored-energy change
  equal to `Q_load - Q_chiller`.
- **System boundary and assumptions:** The boundary contains one well-mixed
  supply node and one well-mixed return node. Building heat enters the return
  node, the chiller removes heat from the supply node, and water flow transfers
  heat internally. Constant flow, constant node masses, instantaneous
  proportional control, and no pipe or equipment dynamics are assumed.
- **Alternatives and trade-offs:** A one-node model cannot expose CHWS/CHWR
  temperature difference or mass-flow heat transfer. A detailed hydraulic or
  refrigerant model would add parameters without current validation data. The
  selected two-node model adds the required physics while remaining auditable.
- **Engineering decision:** Use two 500 kg water nodes, 5 kg/s mass flow,
  `Cp = 4.18 kJ/(kg * degC)`, a 7 degC CHWS setpoint, and the existing bounded
  P controller. Begin at the analytical 30 kW steady state, then apply a 50 kW
  load at 600 s over a 1800 s experiment.
- **Implementation:** `plant.py`, `stage3_main.py`, `plot_stage3.py`, and
  `tests/test_stage3.py`.
- **Verification:** Eight new tests cover the flow equation, zero-flow response,
  balanced heat rates, total-energy conservation, analytical offset, load-step
  convergence, and time-step sensitivity. `stage3_main.py` independently
  calculates acceptance metrics and writes 181 result samples.
- **Quantitative result:** All 32 project tests pass. Final CHWS is 8.665 degC
  against 8.667 degC analytical; final CHWR is 11.055 degC against 11.059 degC
  analytical. The CHWS enters a +/-0.1 degC band after 420 s. Maximum energy
  residual is about `3.5e-12 kJ`, and the 5 s versus 10 s final-temperature
  difference is about `0.0003 degC`. All defined acceptance checks pass.
- **Interpretation:** The model reproduces the expected increase in CHWS,
  CHWR, cooling demand, and flow-carried heat after the building load rises.
  Agreement with the analytical target and small time-step difference support
  the implementation within the stated simplified boundary.
- **Limitations and uncertainty:** Parameters are educational assumptions, not
  site data. Constant mass flow, two lumped water states, and omitted transport,
  sensor, actuator, pump, pipe-loss, and refrigerant dynamics limit use to
  learning and control-development evidence.
- **Learner explanation checkpoint:** Explain where load heat enters, where
  chiller heat leaves, why `Q_flow` cancels from the total balance, and why P
  control retains a steady-state CHWS offset.

Detailed derivation and parameter basis are in
`docs/STAGE3_ENGINEERING_BASIS.md`. Raw evidence is in `results/stage3.csv`, and
the generated result plot is `docs/stage3-load-step-results.svg`.

## EV-CHILLER-S3B-001 — Python-Simulink cross-validation

- **Status:** Implemented and verified locally.
- **Requirement and acceptance criterion:** Recreate the Stage 3A discrete
  two-node model in Simulink with the same parameters, sample time, initial
  conditions, controller, and load step. Compare 181 CHWS and CHWR samples;
  maximum absolute differences must each be no greater than `1e-9 degC`.
- **Engineering question:** Does a second engineering modelling tool reproduce
  the Python thermal response when both implement the stated equations?
- **Theory:** Both implementations use the documented supply and return energy
  balances, explicit 10-second updates, mass-flow heat transfer, and bounded
  proportional control.
- **System boundary and assumptions:** Identical to Stage 3A. This activity
  changes the implementation tool, not the physical boundary or parameters.
- **Alternatives and trade-offs:** Replotting Python data in MATLAB would only
  verify data import. A separate Simulink block model exercises the equations
  through a second execution path while remaining simple enough to inspect.
- **Engineering decision:** Generate a reviewable `.slx` model from a MATLAB
  script so the block structure is both visual and reproducible. Log Simulink
  signals to MATLAB, import the Python CSV, and compare aligned samples.
- **Implementation:** `matlab/build_stage3b_model.m`,
  `matlab/stage3b_chilled_water.slx`, and
  `matlab/run_stage3b_validation.m`.
- **Verification:** The MATLAB script asserts sample count, timestamps, and the
  temperature-difference limit before writing evidence. Two Python tests then
  read the preserved MATLAB CSV files and enforce the same acceptance result.
- **Quantitative result:** The generated `results/stage3b_summary.csv` records
  the measured maximum CHWS and CHWR differences and the `1e-9 degC` limit.
  The Stage 3B commit is created only after the MATLAB assertion and all 34
  Python tests pass.
- **Interpretation:** Agreement shows that the documented discrete equations
  were transferred consistently between Python and Simulink. It reduces the
  chance of a tool-specific implementation error.
- **Limitations and uncertainty:** Both tools implement the same assumptions,
  so agreement is not validation against a real chiller plant. It does not
  remove parameter or model-form uncertainty.
- **Learner explanation checkpoint:** Explain the purpose of each block group,
  why the same load step is used, and the difference between cross-tool
  verification and validation against measured plant data.

## EV-CHILLER-S4A-001 — Proportional versus PI control

- **Status:** Implemented and verified locally.
- **Requirement and acceptance criterion:** Compare P and PI control under the
  same 30 to 50 kW load step. PI final CHWS error must be at most 0.05 degC,
  overshoot at most 0.2 degC, and IAE at most 25% of the P result. PI must enter
  and remain within +/-0.1 degC before the experiment ends. Commands must remain
  between 0 and 1, total-energy residual must remain at most `1e-9 kJ`, and 5 s
  versus 10 s final PI CHWS must differ by at most 0.02 degC.
- **Engineering question:** How much does integral action improve CHWS setpoint
  tracking, and what additional tuning and saturation risks does it introduce?
- **Theory:** `u_P = clamp(Kp * e, 0, 1)` and
  `u_PI = clamp(Kp * e + Ki * integral(e dt), 0, 1)`. P needs nonzero error to
  maintain load-balancing output. PI can retain that output in its integral
  state while instantaneous error returns toward zero.
- **System boundary and assumptions:** The Stage 3 two-node model, parameters,
  load profile, duration, and RUNNING permission are retained. Sensor, actuator,
  transport, pump, and refrigerant dynamics remain outside the boundary.
- **Alternatives and trade-offs:** Increasing `Kp` alone can reduce offset but
  changes response sensitivity and cannot remove the theoretical P-only offset.
  PI adds zero-error load balancing but introduces an integral state, tuning,
  overshoot risk, and windup risk. PID is deferred because derivative action is
  unnecessary for the current evidence question and would add noise sensitivity.
- **Engineering decision:** Retain `Kp = 0.3 / degC` and use
  `Ki = 0.001 / (degC s)`. Start each controller at its balanced 30 kW operating
  point. Initialise PI with a 30% integral bias to avoid an artificial startup
  transient. Use conditional integration for anti-windup.
- **Implementation:** `controller.py`, `stage4_main.py`, `plot_stage4.py`, and
  `tests/test_stage4.py`.
- **Verification:** Nine new tests check PI calculation, invalid inputs,
  anti-windup in both directions, balanced initial conditions, response criteria,
  integrated error, command limits, retained energy conservation, and 5 s versus
  10 s sensitivity. The full suite contains 43 tests.
- **Quantitative result:** P final CHWS error is 1.665 degC and does not enter the
  setpoint band. PI final error is -0.004 degC, settling time is 800 s, overshoot
  is 0.004 degC, and IAE falls from 1840.9 to 206.2 degC s, an 88.8% reduction.
  PI maximum command is 52.6%. Maximum energy residual is below `3.6e-12 kJ`;
  5 s versus 10 s final PI CHWS differs by about 0.0017 degC. All checks pass.
- **Interpretation:** Integral action stores the cooling contribution needed to
  balance the final load, removing the P-only steady-state offset for this
  experiment. The improved result depends on the selected gain and simplified
  dynamics; it is not proof of performance on a real plant.
- **Limitations and uncertainty:** `Ki` is evaluated for one deterministic load
  step with fixed flow and capacity. There is no noise, delay, actuator rate
  limit, equipment cycling, parameter uncertainty study, or measured plant data.
- **Learner explanation checkpoint:** Explain why P needs offset, how the
  integral state supplies output at zero error, what IAE and settling time mean,
  and how conditional integration reduces windup.

Detailed definitions and results are in `docs/STAGE4_ENGINEERING_BASIS.md`.
Raw evidence is in `results/stage4.csv` and `results/stage4_summary.csv`; the
generated figure is `docs/stage4-p-vs-pi-results.svg`.

## Entry template

```markdown
## EV-PROJECT-STAGE-NNN — Evidence title

- **Status:** Planned / Implemented / Verified / Inconclusive.
- **Date and commit:**
- **Requirement and acceptance criterion:**
- **Engineering question:**
- **Theory, equations, and units:**
- **System boundary and assumptions:**
- **Alternatives and trade-offs:**
- **Engineering decision and rationale:**
- **Implementation links:**
- **Verification method:**
- **Quantitative result and pass/fail:**
- **Interpretation:**
- **Limitations and uncertainty:**
- **Learner contribution and explanation checkpoint:**
```

Keep academic records, assessment correspondence, personal competency mappings,
and Career Episode drafts in a separate private location. Review AI-assisted
material against the code, calculations, and result data before using it in an
interview or formal submission.
