"""Verify the Stage 5A PI saturation and anti-windup experiment."""

import unittest

from controller import proportional_integral_control
from stage5_main import (
    LOAD_RECOVERY_TIME_S,
    OVERLOAD_HEAT_LOAD_KW,
    OVERLOAD_START_TIME_S,
    SIMULATION_TIME_S,
    calculate_metrics,
    evaluate_acceptance,
    heat_load_profile_kw,
    run_experiment,
)


class AntiWindupControllerTests(unittest.TestCase):
    """Check the controlled comparison at high output saturation."""

    def test_conditional_integration_prevents_saturated_growth(self) -> None:
        protected_command, protected_integral = proportional_integral_control(
            temperature_c=10.0,
            setpoint_c=7.0,
            kp=0.3,
            ki_per_s=0.001,
            integral_error_c_s=500.0,
            dt_s=10.0,
            anti_windup_enabled=True,
        )
        unprotected_command, unprotected_integral = proportional_integral_control(
            temperature_c=10.0,
            setpoint_c=7.0,
            kp=0.3,
            ki_per_s=0.001,
            integral_error_c_s=500.0,
            dt_s=10.0,
            anti_windup_enabled=False,
        )

        self.assertEqual(protected_command, 1.0)
        self.assertEqual(unprotected_command, 1.0)
        self.assertEqual(protected_integral, 500.0)
        self.assertEqual(unprotected_integral, 530.0)

    def test_anti_windup_option_requires_a_boolean(self) -> None:
        with self.assertRaises(ValueError):
            proportional_integral_control(
                temperature_c=10.0,
                setpoint_c=7.0,
                kp=0.3,
                ki_per_s=0.001,
                integral_error_c_s=500.0,
                dt_s=10.0,
                anti_windup_enabled=1,
            )


class Stage5ExperimentTests(unittest.TestCase):
    """Check the overload scenario and its quantitative engineering claims."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.no_aw_samples = run_experiment(False)
        cls.anti_windup_samples = run_experiment(True)
        cls.anti_windup_5_s_samples = run_experiment(True, 5.0)
        cls.checks, cls.no_aw_metrics, cls.anti_windup_metrics = evaluate_acceptance(
            cls.no_aw_samples,
            cls.anti_windup_samples,
            cls.anti_windup_5_s_samples,
        )

    def test_load_profile_has_defined_overload_and_recovery_boundaries(self) -> None:
        self.assertEqual(heat_load_profile_kw(OVERLOAD_START_TIME_S - 10.0), 30.0)
        self.assertEqual(heat_load_profile_kw(OVERLOAD_START_TIME_S), OVERLOAD_HEAT_LOAD_KW)
        self.assertEqual(heat_load_profile_kw(LOAD_RECOVERY_TIME_S - 10.0), OVERLOAD_HEAT_LOAD_KW)
        self.assertEqual(heat_load_profile_kw(LOAD_RECOVERY_TIME_S), 30.0)
        with self.assertRaises(ValueError):
            heat_load_profile_kw(SIMULATION_TIME_S + 10.0)

    def test_both_cases_start_balanced_and_reach_full_cooling(self) -> None:
        for samples in (self.no_aw_samples, self.anti_windup_samples):
            with self.subTest(controller=samples[0]["controller"]):
                self.assertEqual(len(samples), 361)
                self.assertAlmostEqual(float(samples[0]["supply_temperature_c"]), 7.0)
                self.assertAlmostEqual(float(samples[0]["cooling_kw"]), 30.0)
                self.assertEqual(
                    max(float(sample["applied_cooling_fraction"]) for sample in samples),
                    1.0,
                )

    def test_anti_windup_improves_the_defined_recovery_metrics(self) -> None:
        claimed_checks = (
            "anti-windup limits integral growth",
            "anti-windup releases saturation sooner",
            "anti-windup reduces recovery error",
            "anti-windup limits recovery undershoot",
            "anti-windup recovery settles sooner",
            "anti-windup final error",
        )
        for name in claimed_checks:
            with self.subTest(check=name):
                self.assertTrue(self.checks[name])

    def test_outputs_are_bounded_and_total_energy_is_conserved(self) -> None:
        self.assertTrue(self.checks["both controllers reach saturation"])
        self.assertTrue(self.checks["bounded cooling commands"])
        self.assertTrue(self.checks["energy conservation"])

    def test_anti_windup_result_is_time_step_insensitive(self) -> None:
        metrics_10_s = calculate_metrics(self.anti_windup_samples)
        metrics_5_s = calculate_metrics(self.anti_windup_5_s_samples)
        self.assertLessEqual(
            abs(
                float(metrics_10_s["final_error_c"])
                - float(metrics_5_s["final_error_c"])
            ),
            0.02,
        )
        self.assertTrue(self.checks["anti-windup time-step sensitivity"])


if __name__ == "__main__":
    unittest.main()
