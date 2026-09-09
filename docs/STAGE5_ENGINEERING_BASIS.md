# Stage 5A Engineering Basis

## Purpose

Stage 5A tests PI behaviour when the requested cooling reaches the physical
0% to 100% command limit. It compares the retained conditional anti-windup
controller with an intentionally unprotected PI benchmark under the same
overload and recovery disturbance.

## Control terminology

- **Output saturation:** the calculated controller demand exceeds the available
  actuator range and is limited to 0% or 100%.
- **Integral windup:** accumulated error continues growing while the output is
  saturated and cannot deliver the requested extra action.
- **Conditional anti-windup:** integration is held when it would drive an
  already saturated command farther outside the available range. Integration
  toward the valid range remains allowed.
- **Saturation release time:** time after the load returns to 30 kW until the
  cooling command first falls below 100%.
- **Recovery undershoot:** maximum amount by which CHWS falls below its 7 degC
  setpoint after the overload ends.
- **Recovery settling time:** time after load recovery until CHWS enters and
  remains within +/-0.1 degC.
- **Recovery IAE:** accumulated absolute CHWS error after load recovery, in
  degC s. Lower is better for this experiment.

## Controller equation

Both cases use:

```text
error = CHWS - setpoint
unrestricted_command = Kp * error + Ki * integral_state
cooling_command = clamp(unrestricted_command, 0, 1)
```

The unprotected comparison always applies:

```text
integral_next = integral_state + error * dt
```

Conditional anti-windup holds the integral state if the unrestricted command
is at or above 1 with positive error, or at or below 0 with negative error.
This is a simple clamping method. Back-calculation is a valid alternative but
adds another tuning parameter and is unnecessary for this evidence question.

## Scenario and system boundary

| Parameter | Value |
| --- | ---: |
| CHWS setpoint | 7 degC |
| Initial / recovery load | 30 kW |
| Overload | 120 kW |
| Maximum cooling | 100 kW |
| Overload interval | 600 to 1200 s |
| Simulation duration | 3600 s |
| Default time step | 10 s |
| `Kp` | 0.3 1/degC |
| `Ki` | 0.001 1/(degC s) |
| Water mass flow | 5 kg/s |

The 120 kW overload deliberately exceeds the 100 kW cooling capacity. Both
cases begin at the same balanced 30 kW condition and use the same Stage 3
two-node plant. Equipment is held in RUNNING so the experiment isolates
continuous-controller saturation. Sensors, actuator dynamics, transport delay,
equipment cycling, refrigerant behaviour, and plant safety logic remain outside
the model boundary.

## Requirements and acceptance criteria

| Check | Project acceptance criterion |
| --- | --- |
| Saturation exercised | Both cases reach 100% cooling |
| Output limit | Every command remains between 0 and 1 |
| Integral growth | Anti-windup peak state at most 60% of unprotected PI |
| Saturation release | Anti-windup exits 100% at least 180 s earlier |
| Recovery IAE | Anti-windup at most 50% of unprotected PI |
| Recovery undershoot | At most 1 degC and at most 30% of unprotected PI |
| Recovery settling | Anti-windup settles at least 60 s earlier |
| Final CHWS error | Anti-windup absolute error at most 0.05 degC |
| Energy conservation | Maximum residual at most `1e-9 kJ` |
| Time-step sensitivity | 5 s versus 10 s final error differs by at most 0.02 degC |

These thresholds are educational experiment criteria, not commissioning or
manufacturer limits.

## Quantitative result

Both controllers reach the 100% output limit. Without anti-windup, the integral
state reaches `1827.3 degC s`; conditional anti-windup limits it to
`629.8 degC s`. After the load returns to 30 kW, the protected PI exits full
cooling in 160 s instead of 390 s.

The unprotected controller overcools CHWS by 2.996 degC, reaching approximately
4.004 degC. The protected case limits undershoot to 0.612 degC. Recovery IAE
falls from approximately `2127.9 degC s` to `879.7 degC s`, and settling time
improves from 1270 s to 1170 s. Final protected error is approximately
0.0013 degC.

All commands remain bounded. Maximum energy residual is below `2.7e-12 kJ`,
and changing the protected case from a 10-second to a 5-second time step changes
final error by approximately `0.0003 degC`. All defined checks pass.

## Interpretation and limitations

Saturation makes the actuator unable to follow additional controller demand.
Continuing to integrate that unmet demand stores an excessive cooling bias. The
bias keeps the unprotected controller at full output after the overload has
ended, causing a much larger low-temperature excursion. Conditional integration
reduces this stored bias and produces earlier release with less overcooling.

The experiment uses ideal signals and one deterministic overload. It does not
establish safe leaving-water limits, freezing protection, real chiller response,
or performance under noise and delays. Stage 5B would be required to reproduce
the exercised anti-windup logic in Simulink and claim cross-tool agreement.
