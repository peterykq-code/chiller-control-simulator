"""Verify the preserved Stage 3B Python-Simulink comparison evidence."""

import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SimulinkCrossValidationTests(unittest.TestCase):
    """Check the independently generated comparison trace."""

    def test_all_temperature_samples_meet_the_acceptance_limit(self) -> None:
        comparison_path = ROOT / "results" / "stage3b_comparison.csv"
        with comparison_path.open(newline="", encoding="utf-8-sig") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 181)
        self.assertEqual(float(rows[0]["time_s"]), 0.0)
        self.assertEqual(float(rows[-1]["time_s"]), 1800.0)

        maximum_supply_error_c = max(
            abs(float(row["supply_error_c"])) for row in rows
        )
        maximum_return_error_c = max(
            abs(float(row["return_error_c"])) for row in rows
        )
        self.assertLessEqual(maximum_supply_error_c, 1e-9)
        self.assertLessEqual(maximum_return_error_c, 1e-9)

    def test_summary_records_a_passing_cross_validation(self) -> None:
        summary_path = ROOT / "results" / "stage3b_summary.csv"
        with summary_path.open(newline="", encoding="utf-8-sig") as csv_file:
            summary = next(csv.DictReader(csv_file))

        self.assertEqual(summary["passed"], "1")
        self.assertLessEqual(
            float(summary["maximum_supply_error_c"]),
            float(summary["acceptance_limit_c"]),
        )
        self.assertLessEqual(
            float(summary["maximum_return_error_c"]),
            float(summary["acceptance_limit_c"]),
        )


if __name__ == "__main__":
    unittest.main()
