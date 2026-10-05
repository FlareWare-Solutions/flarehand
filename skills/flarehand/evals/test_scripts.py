#!/usr/bin/env python3
"""test_scripts.py - tier 0 checks. No model, no network, a couple of seconds.

These cover the parts of the skill that are supposed to be deterministic. If any
of these fail, no amount of prompt tuning will make the skill consistent,
because the floor it stands on has moved.

Run:
    python3 evals/test_scripts.py
    python3 evals/test_scripts.py -v
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import classify  # noqa: E402
import kb  # noqa: E402
import recall  # noqa: E402
import redact  # noqa: E402
import check_output  # noqa: E402


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
