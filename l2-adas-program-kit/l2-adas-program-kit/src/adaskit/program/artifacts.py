"""Loaders for the program data files, plus ISO 26262 ASIL derivation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# ISO 26262-3 ASIL determination table, indexed [severity][exposure][controllability].
_ASIL_TABLE = {
    ("S1", "E1"): ["QM", "QM", "QM"], ("S1", "E2"): ["QM", "QM", "QM"],
    ("S1", "E3"): ["QM", "QM", "ASIL-A"], ("S1", "E4"): ["QM", "ASIL-A", "ASIL-B"],
    ("S2", "E1"): ["QM", "QM", "QM"], ("S2", "E2"): ["QM", "QM", "ASIL-A"],
    ("S2", "E3"): ["QM", "ASIL-A", "ASIL-B"], ("S2", "E4"): ["ASIL-A", "ASIL-B", "ASIL-C"],
    ("S3", "E1"): ["QM", "QM", "ASIL-A"], ("S3", "E2"): ["QM", "ASIL-A", "ASIL-B"],
    ("S3", "E3"): ["ASIL-A", "ASIL-B", "ASIL-C"], ("S3", "E4"): ["ASIL-B", "ASIL-C", "ASIL-D"],
}


def _load(name: str, data_dir: Path | None = None) -> dict[str, Any]:
    path = (data_dir or DATA_DIR) / name
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_requirements(data_dir: Path | None = None) -> list[dict[str, Any]]:
    return _load("requirements.yaml", data_dir)["requirements"]


def load_interfaces(data_dir: Path | None = None) -> list[dict[str, Any]]:
    return _load("interfaces.yaml", data_dir)["interfaces"]


def derive_asil(severity: str, exposure: str, controllability: str) -> str:
    """Derive the ASIL from S/E/C rather than trusting a hand-written value."""
    row = _ASIL_TABLE.get((severity, exposure))
    if row is None:
        raise ValueError(f"invalid S/E combination: {severity}/{exposure}")
    index = {"C1": 0, "C2": 1, "C3": 2}[controllability]
    return row[index]


def load_hazards(data_dir: Path | None = None) -> list[dict[str, Any]]:
    hazards = _load("hazards.yaml", data_dir)["hazards"]
    for hazard in hazards:
        hazard["derived_asil"] = derive_asil(
            hazard["severity"], hazard["exposure"], hazard["controllability"]
        )
    return hazards
