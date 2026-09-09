# Stage 4A Engineering Basis

## Purpose

Stage 4A compares proportional (P) and proportional-integral (PI) control on
the verified Stage 3 two-node chilled-water model. Both controllers experience
the same 30 to 50 kW building-load step. The comparison uses defined response
metrics rather than visual judgement alone.

## Control terminology

- **Setpoint:** desired CHWS temperature, 7 degC.
- **Control error:** measured CHWS minus setpoint, in degC.
- **Proportional term:** immediate response `Kp * error`.
- **Integral state:** accumulated error over time, in degC s.
- **Integral term:** retained controller contribution `Ki * integral state`.
- **Steady-state error:** error remaining after the response has settled.
- **Overshoot:** amount by which CHWS falls below the setpoint during recovery.
- **Settling time:** time after the load step until CHWS enters and remains
  within the defined setpoint band.
- **Integrated absolute error (IAE):** total absolute error accumulated after
  the load step, in degC s. Lower is better for this comparison.
- **Anti-windup:** logic that stops the integral state growing when the command
  is saturated and the error would drive it farther beyond the output limit.

## Controller equations and units

The retained P controller is:

```text
error_c = CHWS - setpoint
P_command = clamp(Kp * error_c, 0, 1)
```

The PI controller is:

```text
unrestricted_command = Kp * error_c + Ki * integral_error_c_s
PI_command = clamp(unrestricted_command, 0, 1)
integral_error_next = integral_error_c_s + error_c * dt_s
```

`Kp` has units `1/degC`; `Ki` has units `1/(degC s)`. Both commands are
dimensionless fractions, where 0 is no cooling and 1 is 100% available cooling.

Conditional integration holds the integral state if the unrestricted command
is above 1 with positive error or below 0 with negative error. Error that drives
the command back toward the available range is still integrated.

## System boundary and retained assumptions

The Stage 3 physical boundary and parameters are unchanged:

| Parameter | Value |
| --- | ---: |
| CHWS setpoint | 7 degC |
| `Kp` | 0.3 1/degC |
| `Ki` | 0.001 1/(degC s) |
| Maximum cooling | 100 kW |
| Water mass flow | 5 kg/s |
| Supply-node water mass | 500 kg |
| Return-node water mass | 500 kg |
| Initial / final building load | 30 / 50 kW |
| Load-step time | 600 s |
| Simulation duration | 1800 s |
| Default time step | 10 s |

The equipment is held in RUNNING to isolate continuous control behaviour. Flow,
capacity, sensor response, and actuator response remain ideal and constant.

## Initial-condition decision

Each controller begins at its own balanced 30 kW operating point. The P case
starts at 8 degC CHWS because a 1 degC error with `Kp = 0.3` requests 30%
cooling. The PI case starts at the 7 degC setpoint with an integral bias that
requests the same 30% cooling despite zero instantaneous error.

This avoids an artificial startup transient and makes the experiment a load
disturbance comparison. The different initial temperatures are consequences of
the two controllers' steady-state behaviour, not different plant parameters.

## Metrics and acceptance criteria

| Check | Acceptance criterion |
| --- | --- |
| Cooling command | Every P and PI sample remains between 0 and 1 |
| Energy conservation | Maximum residual at most `1e-9 kJ` |
| PI final CHWS error | Absolute value at most 0.05 degC |
| PI overshoot | At most 0.2 degC below setpoint |
| PI settling | Enters and remains within +/-0.1 degC before simulation end |
| PI IAE | At most 25% of P IAE |
| PI time-step sensitivity | 5 s versus 10 s final CHWS differs by at most 0.02 degC |

These are project-defined educational criteria for a reproducible comparison.
They are not commissioning requirements for a real plant.

## Quantitative result

With the 10-second step, P finishes with a `1.665 degC` CHWS error and does not
enter the +/-0.1 degC setpoint band. PI finishes with a `-0.004 degC` error,
settles within the band 800 s after the load step, and has `0.004 degC`
overshoot. PI reduces IAE from `1840.9 degC s` to `206.2 degC s`, an 88.8%
reduction. Its maximum command is 52.6%, so the normal comparison does not reach
the actuator limit. Separate unit tests exercise anti-windup at saturation.

Maximum energy residual remains below `3.6e-12 kJ`. Changing the PI time step
from 10 s to 5 s changes final CHWS by about `0.0017 degC`. All defined checks
pass.

## Engineering interpretation

P needs a positive CHWS error to maintain the 50% cooling that balances the
final load. PI stores the required cooling contribution in its integral state,
so the instantaneous error can return close to zero. This improves setpoint
tracking, but it adds tuning and saturation-management responsibilities.

The selected `Ki` gives a stable response for this experiment. It is not a
general optimum and has not been validated over different loads, flow rates,
delays, noise, equipment dynamics, or real plant data.
