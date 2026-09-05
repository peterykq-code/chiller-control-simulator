"""Verify the Stage 2 operating sequence and cooling permission."""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main as simulation
from controller import (
    apply_cooling_permission,
    proportional_control,
    update_equipment_state,
)
from plant import update_temperature


class CoolingPermissionTests(unittest.TestCase):
    """Check how equipment state affects the controller request."""

    def test_only_running_permits_cooling(self) -> None:
        """OFF, STARTING, and FAULT block an otherwise valid request."""
        for state in ("OFF", "STARTING", "FAULT"):
            with self.subTest(state=state):
                self.assertEqual(apply_cooling_permission(0.6, state), 0.0)
        self.assertEqual(apply_cooling_permission(0.6, "RUNNING"), 0.6)

    def test_running_preserves_zero_partial_and_full_requests(self) -> None:
        """RUNNING permits the requested fraction without changing it."""
        for request in (0.0, 0.6, 1.0):
            with self.subTest(request=request):
                self.assertEqual(apply_cooling_permission(request, "RUNNING"), request)

    def test_invalid_request_is_rejected_before_permission(self) -> None:
        """A blocked state must not conceal invalid numerical inputs."""
        for state in ("OFF", "RUNNING"):
            for request in (-0.1, 1.1, float("nan"), float("inf")):
                with self.subTest(state=state, request=request):
                    with self.assertRaises(ValueError):
                        apply_cooling_permission(request, state)

    def test_unsupported_permission_state_is_rejected(self) -> None:
        """Unknown states are configuration errors, not normal OFF states."""
        for state in ("", "off", "STOPPING"):
            with self.subTest(state=state):
                with self.assertRaises(ValueError):
                    apply_cooling_permission(0.6, state)

    def test_off_water_warms_despite_full_controller_request(self) -> None:
        """A 30 kW heat load adds 300 kJ in 10 s when cooling is blocked."""
        requested = proportional_control(14.0, 7.0, 0.3)
        applied = apply_cooling_permission(requested, "OFF")
        next_temperature = update_temperature(
            14.0, applied, 30.0, 100.0, 1000.0, 10.0,
        )
        self.assertEqual(requested, 1.0)
        self.assertEqual(applied, 0.0)
        self.assertAlmostEqual(next_temperature, 14.0 + 300.0 / 4180.0)


class EquipmentStateTransitionTests(unittest.TestCase):
    """Check normal startup, stop, fault, and reset decisions."""

    def state_after(
        self,
        current_state: str,
        *,
        start: bool = False,
        stop: bool = False,
        flow: bool = False,
        timed_out: bool = False,
        reset: bool = False,
    ) -> str:
        """Call the state function with explicit readable test inputs."""
        return update_equipment_state(
            current_state=current_state,
            start_command=start,
            stop_command=stop,
            flow_proven=flow,
            startup_timed_out=timed_out,
            reset_command=reset,
        )

    def test_startup_waits_for_flow_then_runs(self) -> None:
        """A start request enters STARTING, which waits for confirmed flow."""
        self.assertEqual(self.state_after("OFF", start=True), "STARTING")
        self.assertEqual(self.state_after("STARTING"), "STARTING")
        self.assertEqual(self.state_after("STARTING", flow=True), "RUNNING")

    def test_startup_timeout_enters_fault(self) -> None:
        """Failure to prove flow before the deadline causes FAULT."""
        self.assertEqual(
            self.state_after("STARTING", timed_out=True),
            "FAULT",
        )

    def test_stop_command_returns_active_states_to_off(self) -> None:
        """A normal stop cancels startup or stops running equipment."""
        self.assertEqual(self.state_after("STARTING", stop=True), "OFF")
        self.assertEqual(self.state_after("RUNNING", stop=True, flow=True), "OFF")

    def test_running_flow_loss_has_fault_priority(self) -> None:
        """Loss of required flow records FAULT even with a simultaneous stop."""
        self.assertEqual(self.state_after("RUNNING"), "FAULT")
        self.assertEqual(
            self.state_after("RUNNING", stop=True),
            "FAULT",
        )

    def test_fault_latches_until_safe_reset(self) -> None:
        """FAULT remains active until reset is requested after flow returns."""
        self.assertEqual(self.state_after("FAULT", flow=True), "FAULT")
        self.assertEqual(self.state_after("FAULT", reset=True), "FAULT")
        self.assertEqual(
            self.state_after("FAULT", flow=True, reset=True),
            "OFF",
        )

    def test_invalid_state_inputs_are_rejected(self) -> None:
        """Unsupported states and non-Boolean signals are rejected."""
        with self.assertRaises(ValueError):
            self.state_after("STOPPING")
        valid_inputs = {
            "current_state": "OFF",
            "start_command": False,
            "stop_command": False,
            "flow_proven": False,
            "startup_timed_out": False,
            "reset_command": False,
        }
        for input_name in (
            "start_command",
            "stop_command",
            "flow_proven",
            "startup_timed_out",
            "reset_command",
        ):
            with self.subTest(input_name=input_name):
                inputs = valid_inputs.copy()
                inputs[input_name] = 1
                with self.assertRaises(ValueError):
                    update_equipment_state(**inputs)


class SimulationRunnerTests(unittest.TestCase):
    """Run the actual entry point with isolated generated files."""

    def run_experiment(self) -> tuple[list[dict[str, str]], str]:
        """Return Stage 2 CSV rows and console output from a temporary run."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            results_dir = temporary_root / "results"
            results_dir.mkdir()
            baseline = results_dir / "stage1.csv"
            baseline.write_text("Preserved Stage 1 baseline\n", encoding="utf-8")
            output = io.StringIO()
            with (
                patch.object(simulation, "__file__", str(temporary_root / "main.py")),
                redirect_stdout(output),
            ):
                simulation.main()
            self.assertEqual(
                baseline.read_text(encoding="utf-8"),
                "Preserved Stage 1 baseline\n",
            )
            with (results_dir / "stage2.csv").open(
                newline="", encoding="utf-8",
            ) as csv_file:
                rows = list(csv.DictReader(csv_file))
        return rows, output.getvalue()

    def test_runner_records_expected_sequence(self) -> None:
        """The demonstration visits normal stop, restart, fault, and reset."""
        rows, output = self.run_experiment()
        by_time = {float(row["time_s"]): row for row in rows}
        expected_states = {
            0.0: "OFF",
            60.0: "STARTING",
            70.0: "STARTING",
            80.0: "RUNNING",
            600.0: "OFF",
            720.0: "STARTING",
            740.0: "RUNNING",
            900.0: "FAULT",
            950.0: "FAULT",
            960.0: "OFF",
            1800.0: "OFF",
        }
        self.assertEqual(len(rows), 181)
        self.assertEqual(
            [float(row["time_s"]) for row in rows],
            list(range(0, 1801, 10)),
        )
        for time_s, expected_state in expected_states.items():
            with self.subTest(time_s=time_s):
                self.assertEqual(by_time[time_s]["equipment_state"], expected_state)
        for state in ("STARTING", "RUNNING", "FAULT"):
            self.assertIn(state, output)

    def test_runner_applies_cooling_only_while_running(self) -> None:
        """Applied cooling follows demand only in RUNNING."""
        rows, _ = self.run_experiment()
        for row in rows:
            requested = float(row["requested_cooling_fraction"])
            applied = float(row["cooling_fraction"])
            if row["equipment_state"] == "RUNNING":
                self.assertEqual(applied, requested)
            else:
                self.assertEqual(applied, 0.0)

    def test_runner_temperature_follows_independent_energy_balance(self) -> None:
        """Every recorded applied command predicts the following temperature."""
        rows, _ = self.run_experiment()
        for current, following in zip(rows, rows[1:]):
            temperature_c = float(current["temperature_c"])
            cooling_fraction = float(current["cooling_fraction"])
            net_heat_kw = 30.0 - cooling_fraction * 100.0
            expected_next = temperature_c + net_heat_kw * 10.0 / 4180.0
            self.assertAlmostEqual(
                float(following["temperature_c"]),
                expected_next,
            )


if __name__ == "__main__":
    unittest.main()
