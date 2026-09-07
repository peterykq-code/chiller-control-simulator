# Stage 3 Engineering Basis

## Purpose

Stage 3 tests whether a small, explainable chilled-water model can represent
mass-flow heat transfer and separate chilled-water supply and return
temperatures. The result is an educational controls-development model, not a
building design, equipment-selection, or commissioning calculation.

## System boundary

```text
                         building heat load
                                |
                                v
chiller cooling <-- supply node <-- flow heat <-- return node
```

The model boundary contains two well-mixed water masses:

- The supply node represents water leaving the chiller and entering the load.
- The return node represents water leaving the load and returning to the chiller.
- The building load adds heat to the return node.
- The chiller removes heat from the supply node.
- Mass flow transfers heat from the warmer return node toward the supply node.

## Variables and units

| Variable | Meaning | Unit |
| --- | --- | --- |
| `T_supply` | Chilled-water supply temperature, CHWS | degC |
| `T_return` | Chilled-water return temperature, CHWR | degC |
| `m_dot` | Chilled-water mass flow | kg/s |
| `Cp` | Water specific heat | kJ/(kg * degC) |
| `Q_load` | Heat added by the building | kW = kJ/s |
| `Q_chiller` | Heat removed by the chiller | kW = kJ/s |
| `Q_flow` | Heat carried between the two nodes | kW = kJ/s |
| `M_supply`, `M_return` | Water represented by each node | kg |
| `dt` | Numerical time step | s |

## Equations

Heat carried by water flow is:

```text
Q_flow = m_dot * Cp * (T_return - T_supply)
```

The two dynamic energy balances are:

```text
M_supply * Cp * dT_supply/dt = Q_flow - Q_chiller
M_return * Cp * dT_return/dt = Q_load - Q_flow
```

The program uses an explicit Euler update:

```text
next_T_supply = T_supply + (Q_flow - Q_chiller) * dt / (M_supply * Cp)
next_T_return = T_return + (Q_load - Q_flow) * dt / (M_return * Cp)
```

Adding both node balances cancels the internal `Q_flow` term:

```text
total stored-energy change = (Q_load - Q_chiller) * dt
```

This total balance is the main conservation check.

## Parameter basis

| Parameter | Value | Basis |
| --- | ---: | --- |
| CHWS setpoint | 7 degC | Retained educational Stage 1 setting |
| Proportional gain | 0.3 / degC | Retained Stage 1 controller setting |
| Maximum cooling | 100 kW | Retained educational Stage 1 capacity |
| Initial/final load | 30/50 kW | Defined disturbance for comparison |
| Mass flow | 5 kg/s | Assumed educational value |
| Supply/return water mass | 500/500 kg | Splits the previous 1000 kg total mass |
| Water specific heat | 4.18 kJ/(kg * degC) | Engineering approximation used in all stages |
| Default time step | 10 s | Retained simulation step; compared with 5 s |
| Simulation duration | 1800 s | Gives 1200 s of response after the load step |

These values support a reproducible learning experiment. They are not selected
from a real building, pump curve, chiller schedule, or commissioning record.

## Analytical steady state

At steady state:

```text
Q_flow = Q_load = Q_chiller
```

For unsaturated proportional control:

```text
T_supply = setpoint + (Q_load / maximum_cooling) / Kp
T_return = T_supply + Q_load / (m_dot * Cp)
```

At 50 kW, the analytical values are approximately:

```text
T_supply = 8.667 degC
T_return = 11.059 degC
```

The supply temperature remains above the 7 degC setpoint because proportional
control needs a non-zero error to request 50% cooling.

## Experiment and acceptance criteria

The model starts at the analytical 30 kW steady state. At 600 s, the building
load increases to 50 kW. Equipment is held in RUNNING so the experiment isolates
thermal and controller response from the already-tested Stage 2 start/fault
sequence.

The implementation passes when:

1. Final CHWS and CHWR are each within 0.02 degC of the analytical values.
2. Maximum total-energy residual is no greater than `1e-9 kJ`.
3. Final 5 s and 10 s time-step results differ by no more than 0.02 degC.

## Verified result

The 10 s experiment produces 181 samples. Final CHWS is 8.665 degC and final
CHWR is 11.055 degC. CHWS enters and remains in a +/-0.1 degC band around its
analytical final value after 420 s. Maximum energy residual is approximately
`3.5e-12 kJ`. The largest final-temperature difference between 5 s and 10 s
steps is approximately `0.0003 degC`. All acceptance criteria pass.

## Limitations

- Both nodes are perfectly mixed.
- Flow and maximum cooling capacity are constant.
- Pipe heat loss, pump heat, transport delay, sensors, valves, and refrigerant
  dynamics are excluded.
- The proportional controller retains steady-state offset.
- Results have not been compared with measured plant data.

## Interview explanation

Stage 3 replaces one overall water temperature with supply and return nodes.
The building adds heat to the return node, water flow carries it toward the
supply node, and the chiller removes heat there. I checked the implementation
against an analytical steady state, confirmed total-energy conservation, and
repeated the experiment with a smaller time step to check numerical sensitivity.
