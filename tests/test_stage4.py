"""Verify the Stage 4A proportional-versus-PI control experiment."""

import unittest

from controller import proportional_integral_control
from stage4_main import (
    PI_FINAL_ERROR_LIMIT_C,
    PI_IAE_RATIO_LIMIT,
    PI_KI_PER_S,
    PI_OVERSHOOT_LIMIT_C,
    calculate_metrics,
    evaluate_acceptance,
    run_experiment,
)


class PIControllerTests(unittest.TestCase):
    """Check PI calculation, validation, and conditional anti-windup."""

    def test_integral_bias_supplies_cooling_at_zero_error(self) -> None:
        command, next_integral = proportional_integral_control(
            temperature_c=7.0,
            setpoint_c=7.0,
            kp=0.3,
            ki_per_s=PI_KI_PER_S,
            integral_error_c_s=300.0,
            dt_s=10.0,
        )

        self.assertAlmostEqual(command, 0.3)
        self.assertAlmostEqual(next_integral, 300.0)

    def test_saturation_prevents_further_positive_windup(self) -> None:
        command, next_integral = proportional_integral_control(
            temperature_c=17.0,
            setpoint_c=7.0,
            kp=0.3,
            ki_per_s=PI_KI_PER_S,
            integral_error_c_s=500.0,
            dt_s=10.0,
        )

        self.assertEqual(command, 1.0)
        self.assertEqual(next_integral, 500.0)

    def test_error_toward_available_range_is_allowed_to_unwind(self) -> None:
        command, next_integral = proportional_integral_control(
            temperature_c=6.0,
            setpoint_c=7.0,
            kp=0.3,
            ki_per_s=PI_KI_PER_S,
            integral_error_c_s=2000.0,
            dt_s=10.0,
        )

        self.assertEqual(command, 1.0)
        self.assertEqual(next_integral, 1990.0)

    def test_invalid_pi_inputs_are_rejected(self) -> None:
        invalid_cases = [
            {"kp": 0.0},
            {"ki_per_s": 0.0},
            {"dt_s": 0.0},
            {"integral_error_c_s": float("inf")},
        ]
        valid = {
            "temperature_c": 8.0,
            "setpoint_c": 7.0,
            "kp": 0.3,
            "ki_per_s": PI_KI_PER_S,
            "integral_error_c_s": 0.0,
            "dt_s": 10.0,
        }

        for replacement in invalid_cases:
            with self.subTest(replacement=replacement):
                inputs = {**valid, **replacement}
                with self.assertRaises(ValueError):
                    proportional_integral_control(**inputs)


class Stage4ExperimentTests(unittest.TestCase):
    """Check response metrics and retained physical verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.p_samples = run_experiment("P")
        cls.pi_samples = run_experiment("PI")
        cls.pi_5_s_samples = run_experiment("PI", 5.0)
        cls.checks, cls.p_metrics, cls.pi_metrics = evaluate_acceptance(
            cls.p_samples,
            cls.pi_samples,
            cls.pi_5_s_samples,
        )

    def test_controllers_begin_at_balanced_30_kw_operating_points(self) -> None:
        self.assertAlmostEqual(
            float(self.p_samples[0]["cooling_kw"]),
            30.0,
        )
        self.assertAlmostEqual(
            float(self.pi_samples[0]["cooling_kw"]),
            30.0,
        )
        self.assertAlmostEqual(
            float(self.pi_samples[0]["supply_temperature_c"]),
            7.0,
        )

    def test_pi_meets_setpoint_response_criteria(self) -> None:
        self.assertLessEqual(
            abs(float(self.pi_metrics["final_error_c"])),
            PI_FINAL_ERROR_LIMIT_C,
        )
        self.assertLessEqual(
            float(self.pi_metrics["overshoot_c"]),
            PI_OVERSHOOT_LIMIT_C,
        )
        self.assertIsNotNone(self.pi_metrics["settling_time_s"])
        self.assertIsNone(self.p_metrics["settling_time_s"])

    def test_pi_reduces_integrated_error_relative_to_p(self) -> None:
        self.assertLessEqual(
            float(self.pi_metrics["integrated_absolute_error_c_s"]),
            PI_IAE_RATIO_LIMIT
            * float(self.p_metrics["integrated_absolute_error_c_s"]),
        )

    def test_outputs_are_bounded_and_energy_is_conserved(self) -> None:
        self.assertTrue(self.checks["bounded cooling command"])
        self.assertTrue(self.checks["energy conservation"])

    def test_pi_result_is_time_step_insensitive(self) -> None:
        metrics_10_s = calculate_metrics(self.pi_samples)
        metrics_5_s = calculate_metrics(self.pi_5_s_samples)

        self.assertLessEqual(
            abs(
                float(metrics_10_s["final_supply_c"])
                - float(metrics_5_s["final_supply_c"])
            ),
            0.02,
        )


if __name__ == "__main__":
    unittest.main()
