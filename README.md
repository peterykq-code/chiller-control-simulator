# Chiller Control Simulator

A small Python project for learning controls software engineering through a simplified chilled-water system. **Stage 1 implements a water-temperature model, a proportional controller, and automated tests.**

The project is an independent educational simulation. It is not connected to physical equipment and does not represent SMARDT's actual control software. The water is represented by one well-mixed thermal mass with a single temperature; supply and return temperatures are not modelled separately.

## Run the simulation

The project uses only the Python standard library. It has been tested with Python 3.12.13, and no third-party packages are required.

Open a terminal in the project root, the folder containing `main.py`. In VS Code, use **Terminal > New Terminal** and select PowerShell on Windows. The examples below use `python` to refer to your configured Python interpreter.

```powershell
python main.py
```

The program calculates 30 minutes of simulated operation without waiting for 30 minutes of real time. It prints progress once per simulated minute and saves all 181 samples to `results/stage1.csv`. Running it again replaces that generated CSV file.

The terminal displays the cooling command as a percentage. The CSV stores it as a fraction: `0.3` means 30% cooling.

## How the control loop works

```text
Current water temperature + temperature setpoint
                     |
                     v
controller.py: calculate a cooling command from 0% to 100%
                     |
                     v
plant.py: calculate the water temperature 10 seconds later
                     |
                     +---- feed the updated temperature into the next cycle

main.py: run the loop and record the results
```

In control engineering, the *plant* is the system being controlled. In this project, it is the simplified water-temperature model.

The controller recalculates its command once per simulation step. The command is held constant for that step. The default controller update interval and plant calculation step are both 10 seconds; this is a modelling choice, not a measured property of a real chiller.

## Project files and functions

| File | Purpose | Main entry point |
| --- | --- | --- |
| `plant.py` | Calculate the water-temperature change | `update_temperature()` |
| `controller.py` | Calculate a cooling command from temperature error | `proportional_control()` |
| `main.py` | Configure the experiment, run the loop, and save data | `main()` |
| `tests/test_stage1.py` | Check control direction, energy balance, limits, and closed-loop behaviour | Individual `test_...()` methods |
| `README.md` | Explain the model, code, and verification steps | This document |
| `AGENTS.md` | Define the teaching workflow and project conventions | Collaboration guidance |
| `.gitignore` | Exclude caches and reproducible results from version control | Git ignore rules |
| `results/stage1.csv` | Store generated time-series data | Created by `main.py` |

### Water-temperature model: `update_temperature()`

Inputs are the current temperature, cooling fraction, external heat load, maximum cooling capacity, water mass, and time-step duration. The output is the temperature at the end of that step, in degrees Celsius.

The model uses an energy balance:

```text
cooling_kw = cooling_fraction * max_cooling_kw
net_heat_kw = heat_load_kw - cooling_kw
thermal_capacity_kj_per_c = water_mass_kg * water_specific_heat
temperature_change_c = net_heat_kw * dt_s / thermal_capacity_kj_per_c
next_temperature_c = temperature_c + temperature_change_c
```

The specific heat of water is approximated as 4.18 kJ/(kg * degree Celsius). Since 1 kW equals 1 kJ/s, multiplying the net heat rate by the step duration gives an energy change in kJ. Dividing by the thermal capacity gives a temperature change in degrees Celsius.

For example, a 30 kW heat load and 100 kW of cooling produce a net heat rate of -70 kW. Over 10 seconds, 1000 kg of water loses 700 kJ and cools by approximately 0.167 degrees. Starting at 14 degrees Celsius, the next temperature is approximately 13.833 degrees Celsius.

The update uses the explicit Euler form with a fixed time step. The model assumes well-mixed water, a constant external heat load, and an immediate cooling response proportional to the command. `cooling_fraction` represents a fraction of cooling capacity, not compressor speed or electrical power consumption.

### Proportional controller: `proportional_control()`

Inputs are the current water temperature, temperature setpoint, and proportional gain `kp`. The output is a cooling fraction between `0.0` and `1.0`.

```text
error_c = temperature_c - setpoint_c
requested_cooling = kp * error_c
cooling_fraction = clamp(requested_cooling, 0.0, 1.0)
```

Here, `clamp` describes output limiting; the implementation uses `max(0.0, min(1.0, requested_cooling))`. The `min` call sets the upper limit, and the `max` call sets the lower limit.

This is a cooling controller, so a positive temperature error increases the cooling request. With water at 9 degrees Celsius, a setpoint of 7 degrees Celsius, and `kp = 0.3`, the error is 2 degrees and the command is `0.6`, or 60%. Water at or below the setpoint requests zero cooling. The model has no active heating actuator.

Both the controller and plant reject non-finite numerical inputs. This controller also requires a positive gain. Input-validation errors are separate from equipment alarms or a FAULT state.

### Simulation runner: `main()`

This function takes no arguments and reads the settings at the top of `main.py`. It returns no calculated value; its outputs are terminal messages and the generated CSV file.

At each sample time, it reads the current simulated temperature, calculates the cooling command, and records both. It then advances the water model by one step, holding that command constant. The last sample records the final temperature and corresponding command without advancing beyond the end of the simulation.

With the default settings, 180 temperature updates plus the initial sample produce 181 records from 0 to 1800 seconds. Each CSV row contains `time_s`, `temperature_c`, `setpoint_c`, and `cooling_fraction`.

| Setting | Default | Meaning |
| --- | --- | --- |
| `INITIAL_TEMPERATURE_C` | 14.0 degrees Celsius | Initial water temperature |
| `SETPOINT_C` | 7.0 degrees Celsius | Desired water temperature |
| `KP` | 0.3 per degree Celsius | Cooling fraction requested per degree of error, before limiting |
| `HEAT_LOAD_KW` | 30.0 kW | Constant rate of external heat entering the water |
| `MAX_COOLING_KW` | 100.0 kW | Cooling capacity at a 100% command |
| `WATER_MASS_KG` | 1000.0 kg | Water mass represented by the model |
| `TIME_STEP_S` | 10.0 s | Simulated time per update |
| `NUMBER_OF_STEPS` | 180 | Number of temperature updates, representing 30 minutes |

## Understanding the default result

The water cools from 14 degrees Celsius towards approximately **8 degrees Celsius**, while the cooling command approaches **30%**. The setpoint remains 7 degrees Celsius, leaving a steady-state error of approximately 1 degree.

This offset is expected for the proportional-only controller under the constant heat load. Holding the temperature steady requires 30 kW of cooling to balance the 30 kW heat load. With a maximum capacity of 100 kW, that requires a cooling fraction of `0.3`. A gain of `0.3` needs a temperature error of 1 degree to produce that command.

```text
Required cooling fraction = 30 / 100 = 0.3
Required temperature error = 0.3 / 0.3 = 1 degree Celsius
Equilibrium temperature = 7 + 1 = 8 degrees Celsius
```

At exactly the setpoint, the proportional command would be zero while the external heat load continued to warm the water. The equilibrium calculation above applies to the default case, where the required cooling is within the available capacity. Integral control can be studied in a later stage; it is not implemented here.

## Run the tests

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

`unittest` is included with Python. The test classes group related scenarios. Each test describes an expected behaviour and checks the actual result against it.

| Test method | Behaviour checked |
| --- | --- |
| `test_hotter_water_requests_more_cooling` | Higher water temperature requests more cooling |
| `test_at_or_below_setpoint_requests_no_cooling` | Water at or below the setpoint requests zero cooling |
| `test_large_error_is_limited_to_full_cooling` | A large error is limited to a 100% cooling command |
| `test_invalid_gain_is_rejected` | Invalid proportional gains raise an error |
| `test_nonfinite_temperature_is_rejected` | Non-finite temperature values are rejected |
| `test_heat_without_cooling_warms_water` | A known energy input raises the temperature by the expected amount |
| `test_cooling_without_heat_lowers_temperature` | A known energy removal lowers the temperature by the expected amount |
| `test_balanced_heat_and_cooling_keep_temperature_constant` | Equal heating and cooling keep the temperature unchanged |
| `test_invalid_physical_inputs_are_rejected` | Invalid physical parameters and commands raise an error |
| `test_default_case_settles_with_proportional_offset` | The connected controller and plant settle near 8 degrees Celsius at 30% cooling |

`assertEqual` checks equality, and `assertAlmostEqual` allows for floating-point rounding. `assertGreater` and `assertLessEqual` check ordering. `assertRaises` checks that an expected exception occurs; rejecting an invalid input is a successful test outcome. `subTest` identifies individual cases within a parameterized test, and `**inputs` passes a dictionary's names and values as function arguments.

The suite contains 10 test methods covering controller behaviour, plant behaviour, and a complete closed-loop scenario. Passing them verifies the specified simulation cases; it does not establish real-equipment performance or commissioning results.

## Reading the Python code

`def` defines a function, and `return` passes a result back to its caller. An annotation such as `temperature_c: float` describes the expected input type; `-> float` describes the return type, while `-> None` means there is no returned calculation result. Type hints do not enforce input validation on their own.

`import` makes functionality from another file or the standard library available. `math.isfinite()` rejects NaN and infinity, while `all(...)` requires every supplied check to pass. `raise ValueError(...)` reports an invalid numerical input or configuration.

`for` repeats a block of code. `range(181)` produces the integers 0 through 180. With the default 10-second step, `step % 6 == 0` prints progress every six steps, or once per simulated minute.

`with ... open(...)` closes the output file automatically when the block finishes. `Path(__file__).resolve().parent` locates the project folder so results are saved beside the code. The `if __name__ == "__main__":` block runs the experiment when `main.py` is executed directly, without running it automatically when imported.

## Learning scope

The first milestone is being able to explain the controller's inputs and output, the plant energy balance, and the reason for the default steady-state offset. Version control can then preserve each understood and verified step.

Possible later stages include OFF/STARTING/RUNNING/FAULT states, alarm handling, additional tests, and an educational Structured Text translation. Introduce one concept at a time after the current stage is understood.

Stage 1 currently has no equipment state machine, equipment alarms, HMI, industrial communications, or PLC implementation. Portfolio and interview descriptions should match the features that have actually been implemented and understood.
