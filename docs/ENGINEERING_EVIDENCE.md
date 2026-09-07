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
