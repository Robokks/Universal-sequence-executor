"""Verified compact connector-pane policy for generated utility VIs.

All positions are from Zuehlke/labview-mcp's measured
docs/connector-pane-patterns.tsv. A pane pattern and its conIdx assignments
must be chosen TOGETHER: conIdx 11 is left on 4815 but not on 4833.
This module never edits an existing binary VI or its callers.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# (number of controls, number of indicators): (pattern, input slots, output slots)
# Slots within each edge run top to bottom. Avoid patterns with unmeasured geometry.
COMPACT_PANES = {
    (1, 1): (4801, (1,), (0,)),
    (2, 1): (4802, (2, 1), (0,)),
    (2, 2): (4805, (3, 2), (1, 0)),
    (3, 1): (4810, (5, 4, 3), (2,)),
    (3, 2): (4810, (5, 4, 3), (2, 1)),
    (4, 1): (4815, (11, 10, 9, 8), (3,)),
    (4, 2): (4815, (11, 10, 9, 8), (3, 2)),
}

# Larger-but-consistent fallback; no silent guess beyond four inputs or outputs.
STANDARD_4815 = ((11, 10, 9, 8), (3, 2, 1, 0))


def assign_connector(root: ET.Element, entry: dict, mode: str, source_pane: str) -> tuple[int, dict]:
    """Return the actual native pattern and the expected, named connector assignments.

    'compact' chooses a measured NI pattern and rewrites staged AIXML terminals.
    'fixed' keeps the baseline indices but explicitly pins the native pane pattern.
    In either case the composer MUST receive the corresponding pane directive.
    """
    if mode not in ("compact", "fixed"):
        raise ValueError("Connector layout must be 'compact' or 'fixed'")
    inputs, outputs = entry["inputs"], entry["outputs"]
    if mode == "fixed":
        pattern = int(source_pane)
        mapping = {el.get("_name"): int(el.get("conIdx")) for el in root
                   if el.tag in ("Control", "Indicator") and el.get("conIdx") is not None}
    else:
        key = (len(inputs), len(outputs))
        if key in COMPACT_PANES:
            pattern, input_slots, output_slots = COMPACT_PANES[key]
        elif len(inputs) <= 4 and len(outputs) <= 4:
            pattern = 4815
            input_slots, output_slots = STANDARD_4815
        else:
            raise ValueError(f"Do not guess a connector layout for {key}: design a pane first")
        mapping = {}
        for terminals, slots, kind in ((inputs, input_slots, "Control"),
                                       (outputs, output_slots, "Indicator")):
            for term, slot in zip(terminals, slots):
                named = [el for el in root if el.tag == kind and el.get("_name") == term["name"]]
                if len(named) != 1:
                    raise ValueError(f"Expected exactly one {kind} named {term['name']}")
                named[0].set("conIdx", str(slot))
                mapping[term["name"]] = slot

    expected = [term["name"] for term in inputs + outputs]
    if len(mapping) != len(expected) or set(mapping) != set(expected):
        raise ValueError("Connector does not bind exactly the declared input/output controls")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Duplicate connector terminal index")
    if any(x < 0 for x in mapping.values()):
        raise ValueError("Invalid connector terminal index")
    return pattern, mapping


def native_subdir(value: str) -> str:
    """Allow only one safe folder name directly below outputs/<batch>."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,60}", value):
        raise ValueError("native-dir must be a simple directory name, e.g. native_refined")
    return value


def composer_pane_directive(pattern: int) -> str:
    """pylabview reads this after </VI>; NI's AIXML reader ignores it."""
    return f'\n<?lvmcp pane="{pattern}"?>\n'
