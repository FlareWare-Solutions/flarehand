#!/usr/bin/env python3
"""test_scripts.py - tier 0 checks. No model, no network, a couple of seconds.

These cover the parts of the skill that are supposed to be deterministic. If any
of these fail, no amount of prompt tuning will make the skill consistent,
because the floor it stands on has moved.

Run:
    python3 tests/test_scripts.py
    python3 tests/test_scripts.py -v
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
sys.path.insert(0, str(SKILL / "scripts"))



def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


# ---------------------------------------------------------------- normalising


# Tests that live beside this file as tests_*.py run with this suite too, so each area can keep its own.
def _load_extra_tests():
    import importlib.util
    for path in sorted(Path(__file__).resolve().parent.glob("tests_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, value in vars(module).items():
            if isinstance(value, type) and issubclass(value, unittest.TestCase) and value is not unittest.TestCase:
                globals()[f"{path.stem}_{name}"] = value


_load_extra_tests()


if __name__ == "__main__":
    unittest.main(verbosity=2)
