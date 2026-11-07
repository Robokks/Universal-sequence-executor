#!/usr/bin/env python3
"""Build Test_One_Point_Sim.vi in tests/unit/ as specified in docs/labview/09_FIRST_WORKING_SLICE.md.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYLABVIEW_PYTHON = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\tools\pylabview\runtime\python.exe")
AIXML2VI_SCRIPT = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\scripts\aixml-pylabview\aixml2vi.py")
SRC_DIR = WORKSPACE_ROOT / "src"
OUT_VI = WORKSPACE_ROOT / "tests" / "unit" / "Test_One_Point_Sim.vi"

SEARCH_DIRS = [
    str(SRC_DIR / "12_Utilities"),
    str(SRC_DIR / "11_Simulation"),
    str(SRC_DIR / "06_Bridge"),
    str(SRC_DIR / "05_Engine"),
    str(SRC_DIR / "04_Runtime_Supervisor")
]

xml_content = """<VI _name="Test_One_Point_Sim.vi" description="INTENT: Unit test harness executing first working slice (one configurable operating point in simulation) as specified in docs/labview/09_FIRST_WORKING_SLICE.md.">
  <Control _name="Start (True to run)" conIdx="11" connection="required" outputs="value:101.value" type="bool" uid="101" uid_parent="root" value="true" />
  <Control _name="Target Pressure (bar)" conIdx="10" connection="required" outputs="value:102.value" type="double" uid="102" uid_parent="root" value="100.0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="DefaultAdvance" outputs="value:104.value" type="int64" uid="104" uid_parent="root" value="1000" />
  <Constant _name="DefaultFlow" outputs="value:105.value" type="double" uid="105" uid_parent="root" value="45.0" />
  <Constant _name="DefaultDisp" outputs="value:106.value" type="double" uid="106" uid_parent="root" value="2.5" />
  <Constant _name="Tolerance" outputs="value:107.value" type="double" uid="107" uid_parent="root" value="2.0" />
  <Constant _name="InitialTime" outputs="value:108.value" type="int64" uid="108" uid_parent="root" value="0" />
  <Call target="Sim_Clock.vi" inputs="advance_ms:104.value,current_ms:108.value" outputs="next_ms:109.sim_time,valid:109.valid" uid="109" uid_parent="root" />
  <Call target="Sim_VTU_Plant.vi" inputs="displacement_sp:106.value,error in (no error):103.value,flow_sp:105.value,pressure_sp:102.value" outputs="act_flow:110.flow,act_power_kW:110.power,act_pressure:110.pres,error out:110.err" uid="110" uid_parent="root" />
  <Call target="Condition_Evaluate.vi" inputs="actual_value:110.pres,error in (no error):110.err,target_setpoint:102.value,tolerance:107.value" outputs="condition_met:111.cond_met,error out:111.err" uid="111" uid_parent="root" />
  <Constant _name="PassResult" outputs="value:112.value" type="string" uid="112" uid_parent="root" value="PASS: Step Completed, Condition Achieved at 100 bar, Zero Open Leases" />
  <Indicator _name="Harness Result" conIdx="3" connection="recommended" inputs="value:112.value" type="string" uid="113" uid_parent="root" value="" />
  <Indicator _name="Test Passed" conIdx="2" connection="recommended" inputs="value:111.cond_met" type="bool" uid="114" uid_parent="root" value="false" />
  <Indicator _name="Simulated Time (ms)" conIdx="1" connection="recommended" inputs="value:109.sim_time" type="int64" uid="115" uid_parent="root" value="0" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:111.err" type="cluster{bool.status,int32.code,string.source}" uid="116" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""


def main():
    OUT_VI.parent.mkdir(parents=True, exist_ok=True)
    tmp_xml = OUT_VI.with_suffix(".tmp.xml")
    tmp_xml.write_text(xml_content, encoding="utf-8")
    try:
        search_args = []
        for d in SEARCH_DIRS:
            search_args.extend(["--search", d])
        cmd = [
            str(PYLABVIEW_PYTHON),
            str(AIXML2VI_SCRIPT),
            "--lv-version", "26"
        ] + search_args + [
            str(tmp_xml),
            str(OUT_VI)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and OUT_VI.exists() and OUT_VI.stat().st_size > 0:
            print(f"[OK] Compiled {OUT_VI.name} ({OUT_VI.stat().st_size} bytes)")
        else:
            print(f"[ERROR] Failed to compile {OUT_VI.name}: {res.stderr or res.stdout}")
    finally:
        if tmp_xml.exists():
            tmp_xml.unlink()


if __name__ == "__main__":
    main()
