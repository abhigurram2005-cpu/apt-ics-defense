import json, os
PATH = "data/threat_intel.json"
DEFAULT = {"verified": False, "summary": "", "attack_techniques": [], "apt_associations": [],
           "sources": [], "confidence": "none: no entry for this family"}

def lookup(family):
    kb = json.load(open(PATH)) if os.path.exists(PATH) else {}
    return kb.get(family, DEFAULT)
