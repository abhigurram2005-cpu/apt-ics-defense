import json
import os

PATH = "data/threat_intel.json"
DEFAULT = {
    "verified": False,
    "summary": "",
    "attack_techniques": [],
    "apt_associations": [],
    "sources": [],
    "confidence": "none: no entry for this family",
}


def load_all() -> dict:
    """Return all family threat-intel entries (excluding metadata keys)."""
    if not os.path.exists(PATH):
        return {}
    with open(PATH, encoding="utf-8") as f:
        kb = json.load(f)
    return {k: v for k, v in kb.items() if not k.startswith("_") and isinstance(v, dict)}


def lookup(family: str) -> dict:
    """Look up threat intelligence for a single malware family."""
    return load_all().get(family, DEFAULT)
