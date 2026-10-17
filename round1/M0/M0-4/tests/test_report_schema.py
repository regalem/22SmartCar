"""M0-4: report.json 结构契约测试（现场判分依赖此结构）。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG = """timeout: 10

tasks:
  - name: A
    duration: 0.01
    success_rate: 1.0
    dependencies: []

  - name: B
    duration: 0.01
    success_rate: 0.0
    dependencies: ["A"]

  - name: C
    duration: 0.01
    success_rate: 1.0
    dependencies: ["B"]
"""


class TestReportSchema(unittest.TestCase):
    def test_report_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = work / "tasks.yaml"
            report = work / "report.json"
            config.write_text(CONFIG, encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scheduler.py"),
                    "--config", str(config),
                    "--seed", "1",
                    "--report", str(report),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(report.is_file(), "report.json was not created")
            data = json.loads(report.read_text(encoding="utf-8"))

        self.assertIsInstance(data.get("timeout"), bool)
        self.assertIsInstance(data.get("total_duration"), (int, float))
        self.assertNotIsInstance(data.get("total_duration"), bool)
        self.assertIsInstance(data.get("tasks"), list)
        self.assertEqual([t.get("name") for t in data["tasks"]], ["A", "B", "C"])

        allowed = {"SUCCESS", "FAILED", "SKIPPED", "TIMEOUT"}
        for task in data["tasks"]:
            for key in ("name", "status", "attempts", "duration", "started_at", "ended_at"):
                self.assertIn(key, task, "missing key %r in %r" % (key, task))
            self.assertIn(task["status"], allowed)
            self.assertIsInstance(task["attempts"], int)
            self.assertGreaterEqual(task["attempts"], 0)
            self.assertLessEqual(task["attempts"], 3)

        by_name = {t["name"]: t for t in data["tasks"]}
        self.assertEqual(by_name["A"]["status"], "SUCCESS")
        self.assertEqual(by_name["B"]["status"], "SKIPPED")
        self.assertEqual(by_name["B"]["attempts"], 3)
        self.assertEqual(by_name["C"]["status"], "SKIPPED")
        self.assertIsInstance(by_name["A"]["started_at"], (int, float))
        self.assertIsInstance(by_name["A"]["ended_at"], (int, float))


if __name__ == "__main__":
    unittest.main()