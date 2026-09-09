"""Verify the preserved Stage 4B Python-Simulink PI comparison evidence."""

import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_LIMIT = 1e-9


class SimulinkPIComparisonTests(unittest.TestCase):
    """Check every preserved cross-tool PI signal difference."""

    def test_all_pi_samples_meet_the_acceptance_limit(self) -> None:
        comparison_path = ROOT / "results" / "stage4b_comparison.csv"
        with comparison_path.open(newline="", encoding="utf-8-sig") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 181)
        self.assertEqual(float(rows[0]["time_s"]), 0.0)
        self.assertEqual(float(rows[-1]["time_s"]), 1800.0)

        error_fields = (
            "supply_error_c",
            "return_error_c",
            "cooling_fraction_error",
            "integral_state_error_c_s",
        )
        for field in error_fields:
            with self.subTest(field=field):
                maximum_error = max(abs(float(row[field])) for row in rows)
                self.assertLessEqual(maximum_error, ACCEPTANCE_LIMIT)

    def test_summary_records_a_passing_pi_cross_validation(self) -> None:
        summary_path = ROOT / "results" / "stage4b_summary.csv"
        with summary_path.open(newline="", encoding="utf-8-sig") as csv_file:
            summary = next(csv.DictReader(csv_file))

        self.assertEqual(int(float(summary["samples_compared"])), 181)
        self.assertEqual(summary["passed"], "1")
        limit = float(summary["acceptance_limit"])
        for field in (
            "maximum_supply_error_c",
            "maximum_return_error_c",
            "maximum_cooling_fraction_error",
            "maximum_integral_state_error_c_s",
        ):
            with self.subTest(field=field):
                self.assertLessEqual(float(summary[field]), limit)


if __name__ == "__main__":
    unittest.main()
