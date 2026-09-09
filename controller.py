"""Calculate cooling control and simple equipment-state decisions."""

import math


def proportional_control(
    temperature_c: float,
    setpoint_c: float,
    kp: float,
) -> float:
    """Return a cooling command between 0.0 and 1.0.

    temperature_c: current measured water temperature, in degrees Celsius.
    setpoint_c: desired water temperature, in degrees Celsius.
    kp: proportional gain, in 1/degree Celsius. A gain of 0.3 requests
        30% cooling per degree above the setpoint, before output limiting.
    """
    if not all(math.isfinite(value) for value in (temperature_c, setpoint_c, kp)):
        raise ValueError("Controller inputs must be finite numbers.")
    if kp <= 0.0:
        raise ValueError("kp must be positive.")

    # Cooling control: a higher temperature should request more cooling.
    error_c = temperature_c - setpoint_c
    requested_cooling = kp * error_c

    # Limit the actuator command to the available cooling range: 0% to 100%.
    return max(0.0, min(1.0, requested_cooling))


def proportional_integral_control(
    temperature_c: float,
    setpoint_c: float,
    kp: float,
    ki_per_s: float,
    integral_error_c_s: float,
    dt_s: float,
) -> tuple[float, float]:
    """Return a bounded PI cooling command and the integral state for the next scan.

    temperature_c: current measured water temperature, in degrees Celsius.
    setpoint_c: desired water temperature, in degrees Celsius.
    kp: proportional gain, in 1/degree Celsius.
    ki_per_s: integral gain, in 1/(degree Celsius * second).
    integral_error_c_s: accumulated temperature error, in degree Celsius seconds.
    dt_s: controller scan interval, in seconds.

    Conditional integration prevents the integral state from growing when the
    output is saturated and the current error would drive it farther outside
    the available 0% to 100% cooling range.
    """
    values = (
        temperature_c,
        setpoint_c,
        kp,
        ki_per_s,
        integral_error_c_s,
        dt_s,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("PI controller inputs must be finite numbers.")
    if kp <= 0.0 or ki_per_s <= 0.0 or dt_s <= 0.0:
        raise ValueError("kp, ki_per_s and dt_s must be positive.")

    error_c = temperature_c - setpoint_c
    unrestricted_command = kp * error_c + ki_per_s * integral_error_c_s
    requested_cooling = max(0.0, min(1.0, unrestricted_command))

    saturated_high = unrestricted_command >= 1.0 and error_c > 0.0
    saturated_low = unrestricted_command <= 0.0 and error_c < 0.0
    if saturated_high or saturated_low:
        next_integral_error_c_s = integral_error_c_s
    else:
        next_integral_error_c_s = integral_error_c_s + error_c * dt_s

    return requested_cooling, next_integral_error_c_s


def update_equipment_state(
    current_state: str,
    start_command: bool,
    stop_command: bool,
    flow_proven: bool,
    startup_timed_out: bool,
    reset_command: bool,
) -> str:
    """Return the state after evaluating one control-scan decision.

    current_state: state before this decision; OFF, STARTING, RUNNING, or FAULT.
    start_command: momentary True value requests that OFF equipment should start.
    stop_command: momentary True value requests a normal stop.
    flow_proven: True means chilled-water flow is confirmed.
    startup_timed_out: True means the allowed startup wait has expired.
    reset_command: momentary True value clears FAULT only after flow is restored.
    This function does not calculate elapsed time.
    """
    if current_state not in ("OFF", "STARTING", "RUNNING", "FAULT"):
        raise ValueError("current_state must be OFF, STARTING, RUNNING, or FAULT.")
    commands = (
        start_command,
        stop_command,
        flow_proven,
        startup_timed_out,
        reset_command,
    )
    if not all(isinstance(command, bool) for command in commands):
        raise ValueError("State-decision commands must be True or False.")

    if current_state == "OFF" and start_command:
        return "STARTING"
    if current_state == "STARTING":
        if stop_command:
            return "OFF"
        if flow_proven:
            return "RUNNING"
        if startup_timed_out:
            return "FAULT"
    if current_state == "RUNNING":
        # Loss of a required running condition has priority over a normal stop.
        if not flow_proven:
            return "FAULT"
        if stop_command:
            return "OFF"
    if current_state == "FAULT" and reset_command and flow_proven:
        return "OFF"
    return current_state


def apply_cooling_permission(
    requested_cooling_fraction: float,
    state: str,
) -> float:
    """Return the cooling fraction allowed by the equipment state.

    requested_cooling_fraction: dimensionless fraction from 0.0 to 1.0.
    state: only "RUNNING" permits cooling; all other supported states block it.
    The returned fraction is suitable for update_temperature().
    This function does not change the equipment state.
    """
    if not math.isfinite(requested_cooling_fraction):
        raise ValueError("Requested cooling fraction must be finite.")
    if not 0.0 <= requested_cooling_fraction <= 1.0:
        raise ValueError("Requested cooling fraction must be between 0.0 and 1.0.")
    if state not in ("OFF", "STARTING", "RUNNING", "FAULT"):
        raise ValueError("state must be OFF, STARTING, RUNNING, or FAULT.")

    if state != "RUNNING":
        return 0.0
    return requested_cooling_fraction
