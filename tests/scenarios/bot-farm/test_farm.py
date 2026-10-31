"""The bot farm's test run under pytest: the gates, the patch tests that still pass, the simulator's self-test and a smoke run of every brain class.

    python -m pytest ShardContent/tests/scenarios/bot-farm/test_farm.py -q            (the workspace Python; pytest is installed there)
    python -m pytest ... -k gates                                                      only the three gates
    python -m pytest ... -k smoke --smoke-hours 0.5                                    a longer smoke run

A patch test that fails under both folder conventions is reported as skipped ("stale"), never as a failure: the release pipeline lists them, the author
decides. farm_release.py --check runs the same things without pytest.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farm_release as fr  # noqa: E402

PATCH_TESTS = sorted(os.path.basename(p) for p in glob.glob(os.path.join(fr.PATCHES, "test_*.py")) if os.path.basename(p) not in fr.GATES)
TREE_TESTS = sorted(os.path.basename(p) for p in glob.glob(os.path.join(fr.TREE_TESTS, "test_*.py")))


def pytest_addoption(parser):
    parser.addoption("--smoke-hours", type=float, default=0.1)


@pytest.mark.parametrize("gate", fr.GATES)
def test_gate(gate):
    p = os.path.join(fr.PATCHES, gate)
    assert os.path.exists(p), f"gate missing: {p}"
    ok, tail, s, conv = fr.run_test(p)
    assert ok, f"{gate}: {tail}"


@pytest.mark.parametrize("name", PATCH_TESTS)
def test_patch(name):
    ok, tail, s, conv = fr.run_test(os.path.join(fr.PATCHES, name))
    if not ok:
        pytest.skip(f"stale: {tail}")


@pytest.mark.parametrize("name", TREE_TESTS)
def test_tree(name):
    """The brain tree's own tests (tests/): a failure is a failure, never stale."""
    ok, tail, s, conv = fr.run_test(os.path.join(fr.TREE_TESTS, name))
    assert ok, f"{name}: {tail}"


def test_simulator_selftest():
    r = subprocess.run([sys.executable, os.path.join(HERE, "sim", "selftest.py")], capture_output=True, text=True, timeout=600, errors="replace")
    assert r.returncode == 0, (r.stdout or "")[-2000:] + (r.stderr or "")[-1000:]


def test_smoke_every_brain_class(request):
    hours = request.config.getoption("--smoke-hours")
    smoke = fr.run_smoke(hours)
    assert smoke["ok"], f"smoke run failed: exceptions {smoke['exceptions']}, crashes {[c['error'] for c in smoke['crashes']]}, {smoke['tail']}"
    assert not smoke["crashes"], smoke["crashes"]
    assert not smoke["exceptions"], smoke["exceptions"]
