# Engineering Gap Audit

Audit date: 2026-09-06
Repository baseline: `b453674 Complete Stage 2 chiller operating sequence and tests`

## Purpose and scope

This audit assesses the current repository as engineering evidence and as a
portfolio project for graduate systems, controls, automation, BMS, integration,
commissioning, and building-services roles. It reviews what is implemented now,
identifies the most important engineering gaps, and selects one bounded next
sprint. It does not claim that this project replaces accredited university study,
manufacturer design data, site commissioning, or professional competency
assessment.

The prioritisation rule is:

```text
engineering depth > user interface
validation > feature count
realistic control logic > visual effects
documented assumptions > hidden constants
quantitative results > qualitative claims
one complete system lifecycle > disconnected features
```

## Current engineering baseline

The repository currently implements:

- A single, well-mixed 1000 kg water thermal mass.
- A discrete energy-balance update using water specific heat:
  `C * dT/dt = Q_load - Q_cooling`, evaluated with a 10-second explicit step.
- A fixed 30 kW heat load and a maximum 100 kW cooling capacity.
- A saturated proportional controller using temperature error.
- Separate requested and applied cooling fractions.
- OFF, STARTING, RUNNING, and FAULT states.
- Flow proof, startup timeout, normal stop, running flow-loss priority, fault
  latching, and reset after flow restoration.
- A deterministic 30-minute scenario with 181 recorded samples.
- 24 automated tests covering controller direction and limits, physical input
  validation, one-step energy balances, the Stage 1 closed loop, state
  transitions, cooling permission, scenario timing, and an independent
  recalculation of every Stage 2 temperature step.
- English documentation of equations, inputs, outputs, assumptions, limitations,
  and the demonstration sequence.

The temperature curve is calculated from an energy balance; it is not manually
drawn or fitted. However, the cooling plant is represented as an instantaneous
fraction of fixed rated capacity, and the flow signal is a Boolean scenario input
rather than a hydraulic result.

## Model classification

**Current classification: simplified engineering model, at an early level.**

It is more than a toy because it conserves thermal energy within its stated
boundary, carries units, produces a closed-loop response, separates control
demand from equipment permission, and verifies those behaviours with tests.

It is not yet a reasonably defensible chilled-water-system simulation for design,
equipment selection, energy prediction, controls tuning, or commissioning. The
model has no separate chilled-water supply and return temperatures, mass flow,
pump model, heat-exchanger behaviour, chiller performance map, transport delay,
sensor dynamics, or electrical-power calculation. The numerical constants are
useful for teaching but are not yet tied to a documented design case or measured
system.

## Capability scores

Scores describe the repository in its present state, not the learner's overall
ability.

| Area | Score | Evidence and limitation |
| --- | ---: | --- |
| Physical modelling | 4/10 | Uses a dimensionally consistent lumped energy balance, but has one thermal node and instantaneous cooling capacity. |
| Thermodynamics/fluid mechanics | 3/10 | Uses water heat capacity and heat rates; does not yet model mass flow or `Q = m_dot * Cp * delta_T`. |
| Dynamic systems modelling | 4/10 | Simulates a time-stepped state response and new equilibrium; no lag, delay, state-space formulation, or timestep study. |
| Control engineering | 4/10 | Includes saturated P control, feedback, state gating, and a visible steady-state offset; no PI/PID comparison or performance metrics. |
| BMS realism | 4/10 | Includes operating states, permissive logic, flow proof, timeout, fault latch, and reset; pump status and anti-cycling are absent. |
| Fault diagnostics | 1/10 | Injected loss of flow causes FAULT, but there is no separate detection rule, alarm record, diagnosis, or fallback strategy. |
| Energy analysis | 1/10 | Thermal heat rates are available, but electrical input, COP, auxiliary energy, and cumulative energy are not calculated. |
| Systems engineering | 2/10 | Interfaces and limitations are documented; formal requirements, acceptance criteria, traceability, trade studies, and FMEA are absent. |
| Verification and validation | 6/10 | Strong implementation tests and independent step checks; no reference data, analytical transient comparison, sensitivity study, or formal acceptance report. |
| Engineering documentation | 6/10 | README explains operation, equations, tests, and limitations; parameter rationale, derivation, architecture, requirements, and decision records need depth. |
| Software architecture | 6/10 | Plant, controller, runner, and tests are separated and readable; string states, scripted inputs, and global constants limit growth. |

## Engineers Australia Stage 1 evidence

This is an informal project mapping only. Final competency assessment depends on
the complete academic and professional evidence submitted to Engineers Australia.

| Element | Current evidence | Reason |
| --- | --- | --- |
| PE1.1 Engineering knowledge and fundamentals | Moderate | Applies energy conservation, heat capacity, feedback control, and basic operating logic, but the physical system is highly simplified. |
| PE1.2 Mathematics, numerical analysis, statistics, and computing | Moderate | Uses a discrete dynamic calculation, numerical simulation, Python, and automated checks; no convergence, uncertainty, or sensitivity analysis. |
| PE1.3 Specialist engineering knowledge | Weak | Chilled-water hydraulics, heat transfer, equipment performance, control tuning, and BMS practice are not yet developed in depth. |
| PE1.6 Professional engineering practice | Weak | Limitations and safety boundaries are stated, but there are no formal requirements, risk analysis, standards, FMEA, or engineering decision record. |
| PE2.1 Application of established engineering methods to complex problem solving | Moderate | Integrates a plant, controller, state sequence, disturbance through flow loss, and verification; the problem boundary and alternatives remain narrow. |
| PE2.2 Fluent application of engineering tools | Moderate | Demonstrates Python, Git, CSV outputs, plotting, and automated tests; specialised modelling, requirements, and commissioning tools are not represented. |
| PE2.3 Engineering synthesis and design processes | Weak | Contains a working control sequence but lacks measurable requirements, option comparison, trade-offs, and traceable design decisions. |

## Most important engineering gaps

1. **The physical boundary is not defined precisely.** The model does not state
   whether its 1000 kg represents an evaporator, buffer tank, distribution loop,
   or combined equivalent thermal capacitance. This makes parameter justification
   and validation difficult.
2. **Flow is not part of the thermal calculation.** `flow_proven` is Boolean, while
   the plant calculation does not use mass flow or separate supply and return
   temperatures. Reduced flow therefore cannot affect delta-T or heat transfer.
3. **The plant responds instantaneously to cooling command.** There is thermal
   inertia in the water mass, but no actuator, chiller, sensor, or transport lag.
4. **The normal experiment has a fixed heat load.** It demonstrates state events,
   but not a defined load step followed by temperature deviation, control response,
   plant response, and recovery.
5. **Controller performance is visual rather than quantitative.** Steady-state
   offset is understood, but rise time, settling time, peak deviation, recovery
   time, control effort, and disturbance rejection are not calculated.
6. **Verification proves the code's stated equations, not the equations' adequacy.**
   There is no timestep convergence study, parameter sensitivity, independent
   reference case, or comparison against a closed-form result.
7. **The sequence omits important lifecycle constraints.** Pump command/status,
   minimum on/off time, anti-short-cycling, deadband, alarm records, and controlled
   restart are not represented.
8. **Fault handling begins after a Boolean event is injected.** Detection,
   persistence/debounce, alarm generation, consequence, and fallback have not been
   separated.
9. **There is no electrical-energy model.** A cooling fraction cannot currently be
   converted to compressor power, pump power, COP, or operating cost.
10. **Engineering decisions are not traceable.** Requirements, acceptance tests,
    verification results, hazards, and design decisions are not linked.

## Prioritised development direction

### P0 — establish a defensible engineering foundation

#### P0.1 Define the model boundary, variables, assumptions, and parameter basis

- Why: the meaning of the current thermal mass and capacity must be explicit
  before new equations are added.
- Engineering value: makes the model falsifiable and prevents hidden physical
  assumptions.
- EA evidence: strengthens PE1.2, PE1.3, PE2.1, and PE2.3.
- Career value: demonstrates engineering judgement and clear handover material.
- Likely modules: new `docs/ENGINEERING_MODEL.md`, then `README.md`; no control-code
  change is required initially.

#### P0.2 Add a flow-based CHWS/CHWR relationship

- Why: mass flow and temperature difference are central to chilled-water heat
  transfer.
- Engineering value: introduces `Q = m_dot * Cp * (T_return - T_supply)` and makes
  reduced-flow scenarios physically meaningful.
- EA evidence: strengthens thermodynamics, fluids, mathematical modelling, and
  synthesis evidence.
- Career value: improves relevance to HVAC, BMS trend analysis, balancing, and
  commissioning discussions.
- Likely modules: `plant.py`, `main.py`, `tests/test_stage3.py`, CSV fields, and
  model documentation.

#### P0.3 Define a load-step experiment, acceptance criteria, and metrics

- Why: a controller should be assessed against a defined disturbance rather than
  only by visual inspection.
- Engineering value: measures maximum deviation, steady-state error, recovery or
  settling time, and integrated control effort.
- EA evidence: strengthens PE1.2, PE2.1, PE2.2, and PE2.3.
- Career value: provides quantitative controls and commissioning evidence.
- Likely modules: a small experiment/metrics module, `main.py`, tests, result CSV,
  and documentation.

#### P0.4 Validate the numerical model, not only the code

- Why: a passing implementation can still represent an unsuitable equation or
  timestep.
- Engineering value: adds analytical comparison for a defined case, timestep
  sensitivity, conservation residuals, and boundary-case checks.
- EA evidence: directly strengthens PE1.2, PE2.1, and PE2.2.
- Career value: demonstrates verification discipline used in modelling, FAT/SAT,
  and commissioning.
- Likely modules: `tests/test_stage3.py`, validation result files, and
  `docs/VALIDATION.md`.

### P1 — increase controls, systems, and reliability value

1. Compare P and PI control after the Stage 3 plant and metrics are stable. Add
   anti-windup only if saturation produces a demonstrated windup problem.
2. Add pump command/status, flow-proof delay, minimum run time, minimum off time,
   deadband, and anti-short-cycling as a traceable BMS sequence.
3. Create numbered functional requirements with acceptance criteria and a
   requirement-to-test-to-result traceability matrix.
4. Turn pump/flow failure into the first diagnostic case because it reuses the
   existing flow permissive. Separate fault cause, detection, alarm, latched
   response, reset condition, and mitigation; record the case in a small FMEA.
5. Add a bounded electrical model for chiller and pump power, then report thermal
   energy, electrical energy, and COP with explicit assumptions.

### P2 — advanced extensions

- Multi-chiller staging and lead/lag rotation.
- Variable-speed pumping and pump-power comparison.
- Feedforward, cascade control, or PID after P/PI comparison shows a need.
- Condenser-side condition and degraded-capacity models.
- Structured Text/FBD translation, HMI, alarms, trends, and industrial
  communications after the Python requirements and tests are stable.
- Parameter calibration against suitable public or measured data.

## Features to defer

The following may look impressive but would add little engineering evidence at
the current stage:

- A dashboard, animated process graphic, or polished user interface.
- Machine learning, cloud services, or a database.
- Many fault types without one complete detection-to-response lifecycle.
- Multi-chiller staging before one chiller has a defensible plant model.
- PID tuning before a load disturbance and performance metrics exist.
- Vendor-specific BMS or chiller logic without authoritative documentation.
- PLC/Structured Text translation before the sequence requirements are stable.

## Recommended next sprint: Stage 3 physics and validation foundation

The next sprint should contain only these five linked deliverables:

1. Define the system boundary and a variable/unit/assumption table.
2. Derive the current capacitance equation and the proposed
   `Q = m_dot * Cp * delta_T` relationship before editing code.
3. Add chilled-water supply temperature, return temperature, and mass flow to one
   reproducible load-step experiment.
4. Add quantitative metrics and explicit acceptance criteria for that experiment.
5. Verify energy conservation and timestep sensitivity, then document the result.

The first teaching and implementation task is item 1: agree what physical volume
the thermal state represents. P, PI, and PID comparison should begin only after
this Stage 3 baseline is defined and verified.
