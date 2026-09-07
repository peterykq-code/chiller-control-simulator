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

- **Status:** Planned; this is not completed evidence.
- **Engineering question:** How should mass flow, chilled-water supply/return
  temperatures, thermal storage, and a load disturbance be represented within a
  defined system boundary?
- **Required theory:** `Q = m_dot * Cp * (T_return - T_supply)`, thermal
  capacitance, state definitions, and explicit time integration.
- **Required decisions:** Physical meaning of the thermal state, parameter basis,
  load-side and chiller-side interfaces, timestep, and acceptance limits.
- **Required verification:** Dimensional checks, an analytical reference case,
  energy-conservation residual, timestep sensitivity, and quantitative load-step
  response metrics.
- **Completion condition:** Equations, assumptions, implementation, tests, data,
  plots, acceptance results, interpretation, uncertainty, and limitations are
  linked here.

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
