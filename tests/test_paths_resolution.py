#!/usr/bin/env python3
"""Minimal, non-invasive tests for config/paths.py (Fase 2 portability layer).

Verifies: (1) defaults are byte-identical to the current hardcoded paths, and
(2) env overrides work. Dependency-free: run with `python tests/test_paths_resolution.py`
or under pytest. Touches nothing else.
"""
import os
import sys
import importlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _fresh_paths():
    """Import (or reload) config.paths so env changes take effect."""
    import config.paths as p
    return importlib.reload(p)


def test_defaults_are_byte_identical():
    for var in ("TRADING_SYSTEM_ROOT", "DATA_ROOT", "RAW_DATA_ROOT", "OUTPUT_ROOT",
                "PRIVATE_ROOT", "EXTERNAL_FACTOR_ROOT", "LOG_ROOT", "TEMP_ROOT"):
        os.environ.pop(var, None)
    p = _fresh_paths()
    assert p.TRADING_SYSTEM_ROOT == REPO, p.TRADING_SYSTEM_ROOT
    assert str(p.TEMP_ROOT) == "/tmp", p.TEMP_ROOT
    assert str(p.causal_segments()) == "/tmp/causal_segments_v10.json", p.causal_segments()
    assert str(p.RAW_DATA_ROOT) == "/Volumes/GUTS_ LACIE/TradingData", p.RAW_DATA_ROOT
    assert p.PRIVATE_ROOT == REPO / "my-strategy", p.PRIVATE_ROOT
    assert p.EXTERNAL_FACTOR_ROOT == REPO / "external_factors_v2", p.EXTERNAL_FACTOR_ROOT
    assert p.LOG_ROOT == REPO / "alert-bridge" / "logs", p.LOG_ROOT
    assert p.OUTPUT_ROOT == REPO / "reports", p.OUTPUT_ROOT
    # ruler helper matches the real revalidation results tree
    assert p.ruler("XAU_4H_L2_BPT_BOS_CHOCH", "v1", "results", "l2_bpt_regua_structural.csv") == \
        REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"


def test_env_override():
    os.environ["TRADING_SYSTEM_ROOT"] = "/tmp/clone_root"
    os.environ["TEMP_ROOT"] = "/tmp/scratch"
    try:
        p = _fresh_paths()
        assert str(p.TRADING_SYSTEM_ROOT) == "/tmp/clone_root", p.TRADING_SYSTEM_ROOT
        assert p.PRIVATE_ROOT == Path("/tmp/clone_root/my-strategy"), p.PRIVATE_ROOT
        assert str(p.causal_segments()) == "/tmp/scratch/causal_segments_v10.json", p.causal_segments()
    finally:
        os.environ.pop("TRADING_SYSTEM_ROOT", None)
        os.environ.pop("TEMP_ROOT", None)
        _fresh_paths()  # restore defaults for any later import


if __name__ == "__main__":
    test_defaults_are_byte_identical()
    test_env_override()
    print("OK: path resolution defaults byte-identical + env override works")
