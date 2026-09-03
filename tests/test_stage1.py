"""Check Stage 1 scenarios; run unittest discovery from the project root."""

import unittest

from controller import proportional_control
from plant import update_temperature


class ControllerTests(unittest.TestCase):
    """Check control direction, output limits, and input validation."""

    def test_hotter_water_requests_more_cooling(self) -> None:
        """Hotter water requests more cooling for the same setpoint."""
        cooler_command = proportional_control(8.0, 7.0, 0.3)
        hotter_command = proportional_control(9.0, 7.0, 0.3)
        self.assertGreater(hotter_command, cooler_command)
        self.assertGreater(cooler_command, 0.0)

    def test_at_or_below_setpoint_requests_no_cooling(self) -> None:
        """Water at or below the setpoint requests no active cooling."""
        for temperature_c in (7.0, 6.0):
            with self.subTest(temperature_c=temperature_c):
                self.assertEqual(proportional_control(temperature_c, 7.0, 0.3), 0.0)

    def test_large_error_is_limited_to_full_cooling(self) -> None:
        """A large temperature error cannot request more than 100% cooling."""
        self.assertEqual(proportional_control(20.0, 7.0, 0.3), 1.0)

    def test_invalid_gain_is_rejected(self) -> None:
        """Zero, negative, and non-finite gains are invalid Stage 1 settings."""
        for kp in (0.0, -0.3, float("nan"), float("inf")):
            with self.subTest(kp=kp):
                with self.assertRaises(ValueError):
                    proportional_control(10.0, 7.0, kp)

    def test_nonfinite_temperature_is_rejected(self) -> None:
        """Reject non-finite temperatures instead of producing a normal command."""
        with self.assertRaises(ValueError):
            proportional_control(float("nan"), 7.0, 0.3)
        with self.assertRaises(ValueError):
            proportional_control(10.0, float("inf"), 0.3)


class PlantTests(unittest.TestCase):
    """Check the plant energy balance and physical parameter validation."""

    def test_heat_without_cooling_warms_water(self) -> None:
        """Adding 418 kJ to 1000 kg of water raises its temperature by 0.1 C."""
        result = update_temperature(10.0, 0.0, 41.8, 100.0, 1000.0, 10.0)
        self.assertAlmostEqual(result, 10.1)

    def test_cooling_without_heat_lowers_temperature(self) -> None:
        """Removing 418 kJ from 1000 kg of water lowers its temperature by 0.1 C."""
        result = update_temperature(10.0, 1.0, 0.0, 41.8, 1000.0, 10.0)
        self.assertAlmostEqual(result, 9.9)

    def test_balanced_heat_and_cooling_keep_temperature_constant(self) -> None:
        """A 30 kW heat load and 30 kW of cooling keep the temperature constant."""
        result = update_temperature(10.0, 0.3, 30.0, 100.0, 1000.0, 10.0)
        self.assertAlmostEqual(result, 10.0)

    def test_invalid_physical_inputs_are_rejected(self) -> None:
        """Reject invalid commands, physical parameters, and non-finite inputs."""
        valid_inputs = {
            "temperature_c": 10.0,
            "cooling_fraction": 0.3,
            "heat_load_kw": 30.0,
            "max_cooling_kw": 100.0,
            "water_mass_kg": 1000.0,
            "dt_s": 10.0,
        }
        invalid_cases = (
            ("cooling_fraction", -0.1),
            ("cooling_fraction", 1.1),
            ("heat_load_kw", -1.0),
            ("max_cooling_kw", 0.0),
            ("water_mass_kg", 0.0),
            ("dt_s", -1.0),
            ("temperature_c", float("nan")),
            ("heat_load_kw", float("inf")),
        )
        for name, value in invalid_cases:
            with self.subTest(parameter=name, value=value):
                inputs = valid_inputs.copy()
                inputs[name] = value
                with self.assertRaises(ValueError):
                    update_temperature(**inputs)


class ClosedLoopTests(unittest.TestCase):
    """Connect the controller and plant to check the complete simulation."""

    def test_default_case_settles_with_proportional_offset(self) -> None:
        """The default case cools steadily from 14 C to about 8 C at 30% cooling."""
        temperature_c = 14.0
        for _ in range(180):
            cooling_fraction = proportional_control(temperature_c, 7.0, 0.3)
            next_temperature_c = update_temperature(
                temperature_c, cooling_fraction, 30.0, 100.0, 1000.0, 10.0
            )
            self.assertLessEqual(next_temperature_c, temperature_c)
            self.assertGreaterEqual(next_temperature_c, 8.0)
            temperature_c = next_temperature_c

        self.assertAlmostEqual(temperature_c, 8.0, places=4)
        self.assertAlmostEqual(proportional_control(temperature_c, 7.0, 0.3), 0.3, places=4)
