# Chiller Control Simulator

An educational Python project for learning controls software engineering through a simplified chilled-water system.

Stage 1 established a lumped water-temperature model, proportional control, and ten automated tests. Stage 2 adds an equipment operating sequence with OFF, STARTING, RUNNING, and FAULT states, cooling permission, flow proof, startup timeout, normal stop, fault priority, and safe reset.

This is an independent learning simulation. It is not connected to physical equipment and does not represent any manufacturer's control software.

## Run the simulation

The project uses only the Python standard library and has been tested with Python 3.12.13.

From the project root:

```powershell
python main.py
```

The program calculates 30 minutes of operation using 10-second simulation steps. It does not wait for 30 minutes of real time. Results are written to `results/stage2.csv`; the existing Stage 1 result remains separate.

Run all tests with:

```powershell
python -m unittest discover -s tests -v
```

## Demonstration scenario

The scenario is deterministic so every state transition can be reproduced and tested.

| Simulated time | Input event | Resulting state | Cooling permission |
| ---: | --- | --- | --- |
| 0 s | Initial condition | OFF | Blocked |
| 60 s | Start command | STARTING | Blocked |
| 80 s | Flow proven | RUNNING | Permitted |
| 600 s | Normal stop command | OFF | Blocked |
| 720 s | Second start command | STARTING | Blocked |
| 740 s | Flow proven | RUNNING | Permitted |
| 900 s | Flow lost while running | FAULT | Blocked |
| 950 s | Flow restored | FAULT remains latched | Blocked |
| 960 s | Reset with flow restored | OFF | Blocked |

The water begins at 14 degrees Celsius with a constant 30 kW heat load. It warms while cooling is blocked, cools while the equipment is RUNNING, and warms again after the fault and reset. The default run ends in OFF at approximately 14.862 degrees Celsius.

## Control sequence

```text
temperature + setpoint
        |
        v
proportional_control() ------> requested cooling
                                      |
commands + flow + timer               |
        |                             |
        v                             v
update_equipment_state() ---> apply_cooling_permission()
        |                             |
        v                             v
equipment state              applied cooling
                                      |
                                      v
                           update_temperature()
```

Only RUNNING permits the requested cooling fraction. OFF, STARTING, and FAULT apply zero cooling.

### State-transition rules

| Current state | Condition | Next state |
| --- | --- | --- |
| OFF | Start command | STARTING |
| OFF | No start command | OFF |
| STARTING | Stop command | OFF |
| STARTING | Flow proven | RUNNING |
| STARTING | Flow not proven and timeout not reached | STARTING |
| STARTING | Startup timed out without flow | FAULT |
| RUNNING | Flow lost | FAULT |
| RUNNING | Flow proven and stop command | OFF |
| RUNNING | Flow proven and no stop command | RUNNING |
| FAULT | Reset command and flow restored | OFF |
| FAULT | Any other condition | FAULT |

Flow loss has priority over a simultaneous normal stop so the abnormal event is recorded as FAULT. A fault remains latched until its required condition is restored and a reset is requested.

## Main functions

| File | Function | Inputs | Output |
| --- | --- | --- | --- |
| `controller.py` | `proportional_control()` | Water temperature and setpoint in degrees Celsius; gain in 1/degree Celsius | Requested cooling fraction from 0.0 to 1.0 |
| `controller.py` | `update_equipment_state()` | Current state and Boolean start, stop, flow, timeout, and reset signals | Next equipment state |
| `controller.py` | `apply_cooling_permission()` | Requested cooling fraction and equipment state | Applied cooling fraction from 0.0 to 1.0 |
| `plant.py` | `update_temperature()` | Temperature, applied cooling, heat load, capacity, water mass, and time step | Temperature after one step |
| `main.py` | `scenario_inputs()` | Simulation time in seconds | Reproducible command and flow signals |
| `main.py` | `main()` | Fixed experiment settings | Terminal output and `results/stage2.csv` |

The CSV records time, water temperature, setpoint, state, requested cooling, applied cooling, and the Boolean scenario inputs. This makes the reason for each response traceable.

## Proportional cooling request

```text
error_c = temperature_c - setpoint_c
requested_cooling = kp * error_c
requested_cooling_fraction = clamp(requested_cooling, 0.0, 1.0)
```

For 9 degrees Celsius water, a 7 degree setpoint, and `kp = 0.3`:

```text
error = 9 - 7 = 2 degrees Celsius
request = 0.3 * 2 = 0.6 = 60%
```

The request expresses temperature demand. It is not automatically the cooling applied to the water.

## Equipment permission

```text
RUNNING                    -> applied cooling = requested cooling
OFF, STARTING, or FAULT    -> applied cooling = 0
```

This separation is the main Stage 2 controls concept. Equipment readiness and protective states can override a valid temperature-control request.

## Water-temperature model

The plant is one well-mixed 1000 kg water mass. Water specific heat is approximated as 4.18 kJ/(kg * degree Celsius).

```text
cooling_kw = applied_cooling_fraction * max_cooling_kw
net_heat_kw = heat_load_kw - cooling_kw
thermal_capacity_kj_per_c = water_mass_kg * 4.18
temperature_change_c = net_heat_kw * dt_s / thermal_capacity_kj_per_c
next_temperature_c = temperature_c + temperature_change_c
```

With cooling blocked, the 30 kW load adds 300 kJ in one 10-second step:

```text
temperature change = 30 * 10 / (1000 * 4.18)
                   = 0.07177 degrees Celsius
```

## Verification

The test suite contains 24 test methods:

- 10 retained Stage 1 tests for proportional control, the energy balance, validation, and the original closed loop.
- 5 cooling-permission tests for supported states, boundaries, invalid inputs, and a connected thermal example.
- 6 state-transition tests for startup, timeout, stop, running flow loss, fault priority, reset, and validation.
- 3 runner tests that execute the real entry point in temporary directories, verify all 181 timestamps and key states, preserve a Stage 1 baseline file, check permission on every row, and independently recalculate every temperature step.

Passing these scenarios verifies the stated educational model. It does not establish real-equipment performance, safety certification, or commissioning results.

## Project limitations

- Supply and return temperatures are not modelled separately.
- Heat load, water mass, and maximum cooling capacity are fixed.
- Commands and flow changes follow a scripted educational scenario.
- Pumps, valves, refrigerant behaviour, compressor dynamics, electrical power, anti-recycle timers, and sensor noise are not modelled.
- STARTING represents flow-proof waiting only.
- FAULT represents simplified loss of chilled-water flow; manufacturer protections are not reproduced.
- The reset rule is an educational choice and not a site-specific operating sequence.

## Portfolio explanation

A concise description of the completed stage is:

> I extended a Python chilled-water simulation with a tested equipment state machine. The controller calculates cooling demand, while OFF, STARTING, RUNNING, and FAULT states determine whether cooling is permitted. The scenario demonstrates flow proof, normal stop, restart, running flow loss, fault latching, and safe reset, with each thermal step checked by automated tests.

The code, data, tests, and documentation should be presented as learning evidence. Any public post should distinguish this simulation from hardware commissioning or a manufacturer's actual control logic.
