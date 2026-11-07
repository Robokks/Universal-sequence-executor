"""Small, consistent 32x32 LabVIEW VI icon labels.

LabVIEW MCP v2.4.1 draws these icons from line1/2/3, <=5 characters each.
Apply only after native generation: regenerating from AIXML resets the icon.
"""
from __future__ import annotations

ICON_LABELS = {
    "Sim_Clock": ("CLOCK", "MS"),
    "UE_Relative_Target": ("REL", "TGT"),
    "UE_Measured_Displacement": ("MEAS", "DISP"),
    "UE_Elapsed_Ms": ("ELAP", "MS"),
    "UE_Ms_To_Seconds": ("MS", "SEC"),
    "UE_Target_Error": ("TGT", "ERR"),
    "UE_Cycle_Event_Duration": ("CYCLE", "DUR"),
    "UE_Inclusive_Range": ("INCL", "RANGE"),
    "UE_Clamp_To_Limits": ("CLAMP", "LIMIT"),
    "UE_Within_Tolerance": ("TOL", "CHECK"),
    "UE_Timeout_Reached": ("TIME", "OUT"),
    "UE_Stabilization_Reached": ("STAB", "READY"),
    "UE_Dwell_Reached": ("DWELL", "DONE"),
    "UE_Retry_Allowed": ("RETRY", "OK"),
    "UE_Cycles_Done": ("CYCLE", "DONE"),
}
BANNER_COLORS = {"U01": "006699", "U02": "339966", "U03": "663399", "U04": "CC6633", "A01": "336699"}


def icon_spec(vi_stem: str) -> dict:
    pieces = vi_stem.removeprefix("UE_").split("_")
    line2, line3 = ICON_LABELS.get(
        vi_stem, (pieces[0].upper()[:5], pieces[1].upper()[:5] if len(pieces) > 1 else "VI")
    )
    if not all(1 <= len(line) <= 5 for line in (line2, line3)):
        raise ValueError(f"Invalid icon lines for {vi_stem}")
    return {"line1": "SIM" if vi_stem.startswith("Sim_") else "UE",
            "line2": line2, "line3": line3}
