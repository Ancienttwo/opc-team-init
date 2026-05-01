#!/usr/bin/env python3
"""Compatibility wrapper for the renamed opc-team-init script."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("init_opc_team.py")), run_name="__main__")
