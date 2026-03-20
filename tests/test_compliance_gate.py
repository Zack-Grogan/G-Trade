from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


class ComplianceGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path(__file__).resolve().parents[1] / "scripts" / "compliance_gate.py"

    def test_compliance_gate_fails_without_ack(self) -> None:
        env = os.environ.copy()
        env.pop("COMPLIANCE_GATE_ACK", None)
        result = subprocess.run(
            [sys.executable, str(self.script)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Compliance gate", result.stdout)

    def test_compliance_gate_passes_with_ack(self) -> None:
        env = os.environ.copy()
        env["COMPLIANCE_GATE_ACK"] = "1"
        result = subprocess.run(
            [sys.executable, str(self.script)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("gate passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
