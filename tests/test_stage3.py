"""Verify the Stage 3 two-node chilled-water energy balance."""

import unittest

from plant import (
    WATER_SPECIFIC_HEAT_KJ_PER_KG_C,
    calculate_flow_heat_transfer_kw,
    update_supply_return_temperatures,
)
from stage3_main import (
    analytical_steady_state,
    calculate_metrics,
    run_experiment,
)


class FlowHeatTransferTests(unittest.TestCase):
    """Check the heat-transfer equation and its engineering direction."""

    def test_warmer_return_water_carries_heat_toward_supply(self) -> None:
        result_kw = calculate_flow_heat_transfer_kw(5.0, 7.0, 9.0)

        self.assertAlmostEqual(result_kw, 41.8)

    def test_zero_flow_carries_no_heat(self) -> None:
        result_kw = calculate_flow_heat_transfer_kw(0.0, 7.0, 9.0)

        self.assertEqual(result_kw, 0.0)


class TwoNodePlantTests(unittest.TestCase):
    """Check supply/return response and conservation of total energy."""

    def test_zero_flow_load_heats_only_the_return_node(self) -> None:
        next_supply_c, next_return_c = update_supply_return_temperatures(
            supply_temperature_c=7.0,
            return_temperature_c=9.0,
            mass_flow_kg_s=0.0,
            heat_load_kw=30.0,
            cooling_kw=0.0,
            supply_water_mass_kg=500.0,
            return_water_mass_kg=500.0,
            dt_s=10.0,
        )

        self.assertEqual(next_supply_c, 7.0)
        self.assertAlmostEqual(next_return_c, 9.0 + 300.0 / (500.0 * 4.18))

    def test_balanced_node_heat_rates_hold_both_temperatures(self) -> None:
        next_supply_c, next_return_c = update_supply_return_temperatures(
            supply_temperature_c=7.0,
            return_temperature_c=9.0,
            mass_flow_kg_s=5.0,
            heat_load_kw=41.8,
            cooling_kw=41.8,
            supply_water_mass_kg=500.0,
            return_water_mass_kg=500.0,
            dt_s=10.0,
        )

        self.assertAlmostEqual(next_supply_c, 7.0)
        self.assertAlmostEqual(next_return_c, 9.0)

    def test_total_stored_energy_matches_external_net_heat(self) -> None:
        supply_c = 7.0
        return_c = 10.0
        supply_mass_kg = 400.0
        return_mass_kg = 600.0
        heat_load_kw = 30.0
        cooling_kw = 40.0
        dt_s = 10.0

        next_supply_c, next_return_c = update_supply_return_temperatures(
            supply_temperature_c=supply_c,
            return_temperature_c=return_c,
            mass_flow_kg_s=4.0,
            heat_load_kw=heat_load_kw,
            cooling_kw=cooling_kw,
            supply_water_mass_kg=supply_mass_kg,
            return_water_mass_kg=return_mass_kg,
            dt_s=dt_s,
        )

        stored_energy_change_kj = WATER_SPECIFIC_HEAT_KJ_PER_KG_C * (
            supply_mass_kg * (next_supply_c - supply_c)
            + return_mass_kg * (next_return_c - return_c)
        )
        expected_external_energy_kj = (heat_load_kw - cooling_kw) * dt_s

        self.assertAlmostEqual(
            stored_energy_change_kj,
            expected_external_energy_kj,
        )


class Stage3ExperimentTests(unittest.TestCase):
    """Check the analytical target and numerical acceptance criteria."""

    def test_load_step_converges_to_the_analytical_steady_state(self) -> None:
        metrics = calculate_metrics(run_experiment(10.0))

        self.assertLessEqual(metrics["final_supply_difference_c"], 0.02)
        self.assertLessEqual(metrics["final_return_difference_c"], 0.02)
        self.assertLessEqual(metrics["maximum_energy_residual_kj"], 1e-9)

    def test_five_and_ten_second_steps_give_similar_final_temperatures(self) -> None:
        metrics_10_s = calculate_metrics(run_experiment(10.0))
        metrics_5_s = calculate_metrics(run_experiment(5.0))

        self.assertLessEqual(
            abs(metrics_10_s["final_supply_c"] - metrics_5_s["final_supply_c"]),
            0.02,
        )
        self.assertLessEqual(
            abs(metrics_10_s["final_return_c"] - metrics_5_s["final_return_c"]),
            0.02,
        )

    def test_analytical_target_has_expected_p_control_offset(self) -> None:
        supply_c, return_c = analytical_steady_state(50.0)

        self.assertAlmostEqual(supply_c, 8.6666666667)
        self.assertAlmostEqual(return_c - supply_c, 50.0 / (5.0 * 4.18))


if __name__ == "__main__":
    unittest.main()
