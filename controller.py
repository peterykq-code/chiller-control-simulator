"""Stage 1: calculate a proportional cooling command from water temperature."""

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
