from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or (Path(__file__).resolve().parent / "config.yaml")
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
