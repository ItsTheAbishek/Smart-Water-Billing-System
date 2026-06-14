# tariff_loader.py
# Module responsible for loading the tariff configuration from a JSON file.

import json
import os
from exceptions import MalformedConfigError

REQUIRED_KEYS = {"slabs", "fixed_charge"}
REQUIRED_SLAB_KEYS = {"min", "max", "rate"}


def load_tariff(config_path: str = "tariff_config.json") -> dict:
    """
    Read and validate the tariff JSON configuration file.

    Parameters
    ----------
    config_path : str
        Path to the JSON configuration file (default: 'tariff_config.json').

    Returns
    -------
    dict
        A structured dictionary mapping:
            category (str) -> {
                "slabs": [{"min": int, "max": int|None, "rate": float}, ...],
                "fixed_charge": float
            }

    Raises
    ------
    MalformedConfigError
        If the file is missing, unreadable, not valid JSON, or has structural issues.
    """

    # ── 1. File existence check ────────────────────────────────────────────────
    if not os.path.exists(config_path):
        raise MalformedConfigError(
            f"Configuration file '{config_path}' not found."
        )

    # ── 2. Parse JSON ──────────────────────────────────────────────────────────
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise MalformedConfigError(f"JSON parse error in '{config_path}': {e}")
    except OSError as e:
        raise MalformedConfigError(f"Cannot read '{config_path}': {e}")

    # ── 3. Top-level structure check ───────────────────────────────────────────
    if not isinstance(raw, dict) or len(raw) == 0:
        raise MalformedConfigError(
            "Configuration must be a non-empty JSON object mapping categories to slab rules."
        )

    # ── 4. Per-category validation ─────────────────────────────────────────────
    for category, config in raw.items():
        if not isinstance(config, dict):
            raise MalformedConfigError(
                f"Category '{category}': expected an object, got {type(config).__name__}."
            )

        missing = REQUIRED_KEYS - config.keys()
        if missing:
            raise MalformedConfigError(
                f"Category '{category}' is missing required keys: {missing}."
            )

        if not isinstance(config["slabs"], list) or len(config["slabs"]) == 0:
            raise MalformedConfigError(
                f"Category '{category}': 'slabs' must be a non-empty list."
            )

        for i, slab in enumerate(config["slabs"]):
            missing_slab_keys = REQUIRED_SLAB_KEYS - slab.keys()
            if missing_slab_keys:
                raise MalformedConfigError(
                    f"Category '{category}', slab {i}: missing keys {missing_slab_keys}."
                )
            if slab["rate"] < 0:
                raise MalformedConfigError(
                    f"Category '{category}', slab {i}: rate cannot be negative."
                )

        if config["fixed_charge"] < 0:
            raise MalformedConfigError(
                f"Category '{category}': fixed_charge cannot be negative."
            )

    return raw


def get_categories(tariff: dict) -> list:
    """Return a list of all category names present in the loaded tariff."""
    return list(tariff.keys())
