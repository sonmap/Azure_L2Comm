"""Offline integration checks: wrapper path normalization, manifests and Pod lifecycle."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh"
ARGS = ["20261025", "20261025", "20261025", "120000", "0", "2", "8",
        "/mnt/batch_gke/l2/rsvp/GP_L2RSVP_001_1/python", "python", "bq_auth_smoke.py"]

class Integration(unittest.TestCase):
    def environment(self):
        env = os.environ.copy()
        env.update(DOCKER_IMAGE="test.azurecr.io/python-bq-batch:v1",
                   NFS_SERVER="10.253.10.4", DRY_RUN="1", PROGRAM_ID="integration")
        return env

    def test_dry_run_contract(self):
        result = subprocess.run([str(WRAPPER), *ARGS], env=self.environment(),
                                capture_output=True, text=True, check=True)
        self.assertIn("cd /home/jupyter/GP_L2RSVP_001_1/python", result.stdout)
        self.assertIn("server: 10.253.10.4", result.stdout)
        self.assertIn("image: test.azurecr.io/python-bq-batch:v1", result.stdout)
        self.assertIn('value: "/home/jupyter/.oefj"', result.stdout)
        self.assertNotIn("docker.pkg.dev", result.stdout)

    def test_missing_image_is_rejected(self):
        env = self.environment()
        env.pop("DOCKER_IMAGE")
        result = subprocess.run([str(WRAPPER), *ARGS], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ACR image URI", result.stderr)

    def test_terminal_phase_lifecycle(self):
        for phase in ("Succeeded", "Failed"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                kubectl = folder / "kubectl"
                kubectl.write_text("""#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
with open(os.environ["CALLS"], "a") as out: out.write(json.dumps(a) + "\\n")
if "get" in a and "pod" in a and "-o" in a:
    print(os.environ["PHASE"], end="")
elif "logs" in a:
    print("L2COMM: SUCCESS" if os.environ["PHASE"] == "Succeeded" else "application failed")
""")
                kubectl.chmod(0o755)
                env = self.environment()
                env.update(DRY_RUN="0", PHASE=phase, CALLS=str(folder/"calls"),
                           PATH=str(folder)+os.pathsep+env["PATH"], POD_TIMEOUT_SECONDS="5")
                result = subprocess.run([str(WRAPPER), *ARGS], env=env, text=True,
                                        capture_output=True, timeout=10)
                calls = [json.loads(x) for x in (folder/"calls").read_text().splitlines()]
                deletes = [x for x in calls if "delete" in x and "pod" in x]
                if phase == "Succeeded":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(deletes)
                    self.assertIn("L2COMM: SUCCESS", result.stdout)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(deletes)
                    self.assertTrue(any("describe" in x for x in calls))

if __name__ == "__main__":
    unittest.main()
