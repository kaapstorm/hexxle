"""The source checkout the tool runs from.

The tool is run with ``uv run`` from a checkout: the site is built from
its ``web/`` and ``node_modules/`` directories, and ``hexxle.toml`` is
read from its root.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
