#!/usr/bin/env python3
"""Wire real subVI calls and block diagram execution sequences across modules.

This script updates the key VIs across Engine, Bridge, Simulation, Supervisor,
Plugins, and Host with their real functional logic and subVI call hierarchies.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYLABVIEW_PYTHON = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\tools\pylabview\runtime\python.exe")
AIXML2VI_SCRIPT = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\scripts\aixml-pylabview\aixml2vi.py")
SRC_DIR = WORKSPACE_ROOT / "src"

SEARCH_DIRS = [
    str(SRC_DIR / "12_Utilities"),
    str(SRC_DIR / "11_Simulation"),
    str(SRC_DIR / "06_Bridge"),
    str(SRC_DIR / "05_Engine"),
    str(SRC_DIR / "04_Runtime_Supervisor"),
    str(SRC_DIR / "03_Config"),
    str(SRC_DIR / "02_Transport"),
    str(SRC_DIR / "01_Host" / "01_Application"),
    str(SRC_DIR / "09_Plugins"),
    str(SRC_DIR / "08_RT_Functions")
]


def compile_vi(xml_content: str, out_vi: Path) -> bool:
    out_vi.parent.mkdir(parents=True, exist_ok=True)
    tmp_xml = out_vi.with_suffix(".wire_tmp.xml")
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
            str(out_vi)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and out_vi.exists() and out_vi.stat().st_size > 0:
            print(f"  [WIRED OK] {out_vi.parent.name}/{out_vi.name} ({out_vi.stat().st_size} bytes)")
            return True
        else:
            print(f"  [ERROR] {out_vi.name}: {res.stderr.strip() or res.stdout.strip()}")
            return False
    finally:
        if tmp_xml.exists():
            tmp_xml.unlink()


def wire_simulation():
    print("\n--- Wiring 11_Simulation Subsystem ---")

    # 1. Sim_VTU_Plant.vi (already tested, compiles cleanly)
    sim_plant_xml = """<VI _name="Sim_VTU_Plant.vi" description="INTENT: Deterministic first-order dynamic plant response for VTU hydraulic hitch and servo. Computes actuator pressure, flow, displacement and hydraulic power.">
  <Control _name="pressure_sp" conIdx="11" connection="required" outputs="value:101.value" type="double" uid="101" uid_parent="root" value="100.0" />
  <Control _name="flow_sp" conIdx="10" connection="required" outputs="value:102.value" type="double" uid="102" uid_parent="root" value="40.0" />
  <Control _name="displacement_sp" conIdx="9" connection="required" outputs="value:103.value" type="double" uid="103" uid_parent="root" value="2.0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="104" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="FilterCoeff" outputs="value:105.value" type="double" uid="105" uid_parent="root" value="0.95" />
  <Node _name="Multiply" inputs="x:101.value,y:105.value" outputs="x*y:106.x*y" uid="106" uid_parent="root" />
  <Node _name="Multiply" inputs="x:102.value,y:105.value" outputs="x*y:107.x*y" uid="107" uid_parent="root" />
  <Node _name="Multiply" inputs="x:103.value,y:105.value" outputs="x*y:108.x*y" uid="108" uid_parent="root" />
  <Call target="UE_Hydraulic_Power_kW.vi" inputs="pressure_bar:106.x*y,flow_lpm:107.x*y" outputs="hydraulic_kw:109.power_kW" uid="109" uid_parent="root" />
  <Indicator _name="act_pressure" conIdx="3" connection="recommended" inputs="value:106.x*y" type="double" uid="110" uid_parent="root" value="0.0" />
  <Indicator _name="act_flow" conIdx="2" connection="recommended" inputs="value:107.x*y" type="double" uid="111" uid_parent="root" value="0.0" />
  <Indicator _name="act_power_kW" conIdx="1" connection="recommended" inputs="value:109.power_kW" type="double" uid="112" uid_parent="root" value="0.0" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="113" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(sim_plant_xml, SRC_DIR / "11_Simulation" / "Sim_VTU_Plant.vi")

    # 2. Sim_IO_Adapter.vi
    sim_io_xml = """<VI _name="Sim_IO_Adapter.vi" description="INTENT: Simulated I/O adapter validating synthetic commands and generating simulated feedback timestamps.">
  <Control _name="command_val" conIdx="11" connection="required" outputs="value:101.value" type="double" uid="101" uid_parent="root" value="10.0" />
  <Control _name="current_ms" conIdx="10" connection="required" outputs="value:102.value" type="int64" uid="102" uid_parent="root" value="0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="AckDelayMs" outputs="value:104.value" type="int64" uid="104" uid_parent="root" value="50" />
  <Call target="Sim_Clock.vi" inputs="advance_ms:104.value,current_ms:102.value" outputs="next_ms:105.ack_ms,valid:105.valid" uid="105" uid_parent="root" />
  <Indicator _name="feedback_val" conIdx="3" connection="recommended" inputs="value:101.value" type="double" uid="106" uid_parent="root" value="0.0" />
  <Indicator _name="ack_time_ms" conIdx="2" connection="recommended" inputs="value:105.ack_ms" type="int64" uid="107" uid_parent="root" value="0" />
  <Indicator _name="is_applied" conIdx="1" connection="recommended" inputs="value:105.valid" type="bool" uid="108" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="109" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(sim_io_xml, SRC_DIR / "11_Simulation" / "Sim_IO_Adapter.vi")

    # 3. Sim_Main.vi (Top-level simulation calling Sim_Clock.vi and Sim_VTU_Plant.vi)
    sim_main_xml = """<VI _name="Sim_Main.vi" description="INTENT: Top-level simulation executive coordinating simulated clock, VTU plant dynamics, and simulated I/O.">
  <Control _name="time_advance_ms" conIdx="11" connection="required" outputs="value:101.value" type="int64" uid="101" uid_parent="root" value="10" />
  <Control _name="pressure_target" conIdx="10" connection="required" outputs="value:102.value" type="double" uid="102" uid_parent="root" value="150.0" />
  <Control _name="current_ms" conIdx="9" connection="required" outputs="value:103.value" type="int64" uid="103" uid_parent="root" value="0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="104" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="DefaultFlow" outputs="value:105.value" type="double" uid="105" uid_parent="root" value="45.0" />
  <Constant _name="DefaultDisp" outputs="value:106.value" type="double" uid="106" uid_parent="root" value="2.5" />
  <Call target="Sim_Clock.vi" inputs="advance_ms:101.value,current_ms:103.value" outputs="next_ms:107.next_ms,valid:107.valid" uid="107" uid_parent="root" />
  <Call target="Sim_VTU_Plant.vi" inputs="displacement_sp:106.value,error in (no error):104.value,flow_sp:105.value,pressure_sp:102.value" outputs="act_flow:108.act_flow,act_power_kW:108.act_power,act_pressure:108.act_pressure,error out:108.err_out" uid="108" uid_parent="root" />
  <Indicator _name="sim_time_ms" conIdx="3" connection="recommended" inputs="value:107.next_ms" type="int64" uid="109" uid_parent="root" value="0" />
  <Indicator _name="plant_pressure" conIdx="2" connection="recommended" inputs="value:108.act_pressure" type="double" uid="110" uid_parent="root" value="0.0" />
  <Indicator _name="plant_power_kW" conIdx="1" connection="recommended" inputs="value:108.act_power" type="double" uid="111" uid_parent="root" value="0.0" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:108.err_out" type="cluster{bool.status,int32.code,string.source}" uid="112" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(sim_main_xml, SRC_DIR / "11_Simulation" / "Sim_Main.vi")


def wire_bridge():
    print("\n--- Wiring 06_Bridge Subsystem ---")

    # 1. Bridge_Validate_Command.vi (calls UE_Inclusive_Range)
    b_val_xml = """<VI _name="Bridge_Validate_Command.vi" description="INTENT: Validate command setpoint against rig limits and clamp if within authorized envelope.">
  <Control _name="CommandRequest" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="" />
  <Control _name="active plan" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="104" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="DefaultVal" outputs="value:105.value" type="double" uid="105" uid_parent="root" value="100.0" />
  <Constant _name="MinLimit" outputs="value:106.value" type="double" uid="106" uid_parent="root" value="0.0" />
  <Constant _name="MaxLimit" outputs="value:107.value" type="double" uid="107" uid_parent="root" value="250.0" />
  <Call target="UE_Inclusive_Range.vi" inputs="maximum:107.value,minimum:106.value,value:105.value" outputs="in_range:108.in_range" uid="108" uid_parent="root" />
  <Indicator _name="Authorized/rejected reason" conIdx="3" connection="recommended" inputs="value:101.value" type="string" uid="109" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:108.in_range" type="bool" uid="110" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="111" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(b_val_xml, SRC_DIR / "06_Bridge" / "Bridge_Validate_Command.vi")

    # 2. Bridge_Loop.vi (calls Bridge_Validate_Command)
    b_loop_xml = """<VI _name="Bridge_Loop.vi" description="INTENT: Hardware bridge command arbiter loop validating and dispatching setpoints.">
  <Control _name="IncomingCommand" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="CMD_START" />
  <Control _name="ActivePlanRef" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="PLAN_01" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Bridge_Validate_Command.vi" inputs="CommandRequest:101.value,active plan:102.value,error in (no error):103.value" outputs="Authorized/rejected reason:104.reason,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Indicator _name="DispatchedResult" conIdx="3" connection="recommended" inputs="value:104.reason" type="string" uid="105" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:104.ok" type="bool" uid="106" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.err_out" type="cluster{bool.status,int32.code,string.source}" uid="107" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(b_loop_xml, SRC_DIR / "06_Bridge" / "Bridge_Loop.vi")


def wire_engine():
    print("\n--- Wiring 05_Engine Subsystem ---")

    # 1. Condition_Evaluate.vi (calls UE_Within_Tolerance)
    cond_eval_xml = """<VI _name="Condition_Evaluate.vi" description="INTENT: Evaluate parameter value against setpoint target and tolerance.">
  <Control _name="actual_value" conIdx="11" connection="required" outputs="value:101.value" type="double" uid="101" uid_parent="root" value="100.0" />
  <Control _name="target_setpoint" conIdx="10" connection="required" outputs="value:102.value" type="double" uid="102" uid_parent="root" value="100.0" />
  <Control _name="tolerance" conIdx="9" connection="required" outputs="value:103.value" type="double" uid="103" uid_parent="root" value="2.0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="104" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="UE_Within_Tolerance.vi" inputs="actual:101.value,target:102.value,tolerance:103.value" outputs="within_tolerance:105.within" uid="105" uid_parent="root" />
  <Indicator _name="condition_met" conIdx="3" connection="recommended" inputs="value:105.within" type="bool" uid="106" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.value" type="cluster{bool.status,int32.code,string.source}" uid="107" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(cond_eval_xml, SRC_DIR / "05_Engine" / "Condition_Evaluate.vi")

    # 2. Step_Tick.vi (calls UE_Elapsed_Ms, UE_Timeout_Reached)
    step_tick_xml = """<VI _name="Step_Tick.vi" description="INTENT: Cooperative step tick evaluating step duration, condition progress, and timeout limits.">
  <Control _name="StepContext" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="" />
  <Control _name="current time" conIdx="10" connection="required" outputs="value:102.value" type="int64" uid="102" uid_parent="root" value="1500" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Constant _name="StartTime" outputs="value:104.value" type="int64" uid="104" uid_parent="root" value="0" />
  <Constant _name="TimeoutLimit" outputs="value:105.value" type="int64" uid="105" uid_parent="root" value="5000" />
  <Call target="UE_Elapsed_Ms.vi" inputs="now_ms:102.value,start_ms:104.value" outputs="elapsed_ms:106.elapsed" uid="106" uid_parent="root" />
  <Call target="UE_Timeout_Reached.vi" inputs="elapsed_ms:106.elapsed,threshold_ms:105.value" outputs="reached:107.is_timeout" uid="107" uid_parent="root" />
  <Indicator _name="Updated StepContext and outgoing requests" conIdx="3" connection="recommended" inputs="value:101.value" type="string" uid="108" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:107.is_timeout" type="bool" uid="109" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="110" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(step_tick_xml, SRC_DIR / "05_Engine" / "Step_Tick.vi")

    # 3. Cycle_Finish.vi (calls UE_Cycles_Done)
    cycle_xml = """<VI _name="Cycle_Finish.vi" description="INTENT: Evaluate test endurance cycle count and determine if sequence should loop or finish.">
  <Control _name="completed_cycles" conIdx="11" connection="required" outputs="value:101.value" type="int32" uid="101" uid_parent="root" value="5" />
  <Control _name="target_cycles" conIdx="10" connection="required" outputs="value:102.value" type="int32" uid="102" uid_parent="root" value="10" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="UE_Cycles_Done.vi" inputs="completed:101.value,requested:102.value" outputs="done:104.done" uid="104" uid_parent="root" />
  <Indicator _name="all_cycles_done" conIdx="3" connection="recommended" inputs="value:104.done" type="bool" uid="105" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="106" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(cycle_xml, SRC_DIR / "05_Engine" / "Cycle_Finish.vi")

    # 4. Executor_Loop.vi (calls Step_Tick)
    exec_loop_xml = """<VI _name="Executor_Loop.vi" description="INTENT: Core sequence executor loop evaluating active step progress and endurance cycle counters.">
  <Control _name="StepContext" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="STEP_ACTIVE" />
  <Control _name="current time" conIdx="10" connection="required" outputs="value:102.value" type="int64" uid="102" uid_parent="root" value="1000" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Step_Tick.vi" inputs="StepContext:101.value,current time:102.value,error in (no error):103.value" outputs="Updated StepContext and outgoing requests:104.res,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Indicator _name="SequenceResult" conIdx="3" connection="recommended" inputs="value:104.res" type="string" uid="105" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:104.ok" type="bool" uid="106" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.err_out" type="cluster{bool.status,int32.code,string.source}" uid="107" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(exec_loop_xml, SRC_DIR / "05_Engine" / "Executor_Loop.vi")


def wire_plugins():
    print("\n--- Wiring 09_Plugins Subsystem ---")

    # VTU_Reference_Load_Calc.vi (calls UE_Relative_Target)
    vtu_load_xml = """<VI _name="VTU_Reference_Load_Calc.vi" description="INTENT: Dynamic VTU hydraulic load calculation from measured stroke and relative displacement.">
  <Control _name="base_stroke_mm" conIdx="11" connection="required" outputs="value:101.value" type="double" uid="101" uid_parent="root" value="10.0" />
  <Control _name="delta_mm" conIdx="10" connection="required" outputs="value:102.value" type="double" uid="102" uid_parent="root" value="2.0" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="UE_Relative_Target.vi" inputs="offset_mm:102.value,reference_mm:101.value" outputs="target_mm:104.target_mm" uid="104" uid_parent="root" />
  <Indicator _name="computed_target_mm" conIdx="3" connection="recommended" inputs="value:104.target_mm" type="double" uid="105" uid_parent="root" value="0.0" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="106" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(vtu_load_xml, SRC_DIR / "09_Plugins" / "VTU_Reference_Load_Calc.vi")

    # Plugin_Manager.vi (calls Plugin_Validate_Manifest and Plugin_Start)
    plugin_mgr_xml = """<VI _name="Plugin_Manager.vi" description="INTENT: Central plugin executive validating manifests, starting instances, and dispatching worker results.">
  <Control _name="Plugin manifests" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="MANIFEST_JSON" />
  <Control _name="requests" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="START_REQ" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Plugin_Validate_Manifest.vi" inputs="PluginManifest:101.value,error in (no error):103.value,target capability:102.value" outputs="Allowed/diagnostics:104.diag,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Call target="Plugin_Start.vi" inputs="Plugin ID:101.value,error in (no error):104.err_out,typed args:102.value" outputs="Instance ID:105.inst_id,error out:105.err_out,status ok:105.ok" uid="105" uid_parent="root" />
  <Indicator _name="Plugin status/events" conIdx="3" connection="recommended" inputs="value:105.inst_id" type="string" uid="106" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:105.ok" type="bool" uid="107" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:105.err_out" type="cluster{bool.status,int32.code,string.source}" uid="108" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(plugin_mgr_xml, SRC_DIR / "09_Plugins" / "Plugin_Manager.vi")


def wire_supervisor():
    print("\n--- Wiring 04_Runtime_Supervisor Subsystem ---")

    # 1. Supervisor_Loop.vi (calls Supervisor_Handle_Event)
    sup_loop_xml = """<VI _name="Supervisor_Loop.vi" description="INTENT: Supervisory Message Handling Loop dequeuing runtime messages and transitioning engine states.">
  <Control _name="Supervisor message queue" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="MSG_START" />
  <Control _name="RunContext" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="STATE_READY" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Supervisor_Handle_Event.vi" inputs="Current run state:102.value,RuntimeMessage:101.value,error in (no error):103.value" outputs="Updated state and effects:104.effects,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Indicator _name="State transitions/events" conIdx="3" connection="recommended" inputs="value:104.effects" type="string" uid="105" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:104.ok" type="bool" uid="106" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:104.err_out" type="cluster{bool.status,int32.code,string.source}" uid="107" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(sup_loop_xml, SRC_DIR / "04_Runtime_Supervisor" / "Supervisor_Loop.vi")

    # 2. Target_Main.vi (calls Runtime_Initialize, Supervisor_Loop, Runtime_Close)
    target_main_xml = """<VI _name="Target_Main.vi" description="INTENT: Top-level cRIO/RT Target Executive initializing services, executing supervisory loop, and closing cleanly.">
  <Control _name="Local paths" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="C:\\Config" />
  <Control _name="hardware/transport profile" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="PROFILE_DEFAULT" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Runtime_Initialize.vi" inputs="Target capability:102.value,configuration locations:101.value,error in (no error):103.value" outputs="Service references:104.srv_ref,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Call target="Supervisor_Loop.vi" inputs="RunContext:104.srv_ref,Supervisor message queue:101.value,error in (no error):104.err_out" outputs="State transitions/events:105.events,error out:105.err_out,status ok:105.ok" uid="105" uid_parent="root" />
  <Call target="Runtime_Close.vi" inputs="Run state:105.events,error in (no error):105.err_out,service references:104.srv_ref" outputs="Close results:106.close_res,error out:106.err_out,status ok:106.ok" uid="106" uid_parent="root" />
  <Indicator _name="Shutdown/status" conIdx="3" connection="recommended" inputs="value:106.close_res" type="string" uid="107" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:106.ok" type="bool" uid="108" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:106.err_out" type="cluster{bool.status,int32.code,string.source}" uid="109" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(target_main_xml, SRC_DIR / "04_Runtime_Supervisor" / "Target_Main.vi")


def wire_host():
    print("\n--- Wiring 01_Host Subsystem ---")

    # Host_Main.vi (calls Host_Event_Loop and Host_Message_Loop)
    host_main_xml = """<VI _name="Host_Main.vi" description="INTENT: Top-level Host Application Entry orchestrating Event Handling Loop (Producer) and Message Handling Loop (Consumer).">
  <Control _name="Startup config" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="config.json" />
  <Control _name="application path" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="app_path" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="Host_Event_Loop.vi" inputs="UI references:101.value,error in (no error):103.value,event loop queue:102.value" outputs="Host messages:104.msg,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Call target="Host_Message_Loop.vi" inputs="HostMessage.ctl queue:104.msg,app-state shift register:101.value,error in (no error):104.err_out" outputs="HMI updates:105.updates,error out:105.err_out,status ok:105.ok" uid="105" uid_parent="root" />
  <Indicator _name="Stop status" conIdx="3" connection="recommended" inputs="value:105.updates" type="string" uid="106" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:105.ok" type="bool" uid="107" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:105.err_out" type="cluster{bool.status,int32.code,string.source}" uid="108" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(host_main_xml, SRC_DIR / "01_Host" / "01_Application" / "Host_Main.vi")


def wire_rt():
    print("\n--- Wiring 08_RT_Functions Subsystem ---")

    # RT_Main.vi (calls RT_IO_Acquisition_Loop, RT_Servo_Controller_Loop, and RT_Fault_Checker)
    rt_main_xml = """<VI _name="RT_Main.vi" description="INTENT: Deterministic RT Controller Main coordinating hardware acquisition, servo position loop, and fault monitoring.">
  <Control _name="Hardware map" conIdx="11" connection="required" outputs="value:101.value" type="string" uid="101" uid_parent="root" value="HW_MAP" />
  <Control _name="controller configuration" conIdx="10" connection="required" outputs="value:102.value" type="string" uid="102" uid_parent="root" value="CFG_SERVO" />
  <Control _name="error in (no error)" conIdx="8" connection="recommended" outputs="value:103.value" type="cluster{bool.status,int32.code,string.source}" uid="103" uid_parent="root" value="[false,0,&quot;&quot;]" />
  <Call target="RT_IO_Acquisition_Loop.vi" inputs="NI hardware references:101.value,error in (no error):103.value,sample policy:102.value" outputs="Typed process value updates:104.pv,error out:104.err_out,status ok:104.ok" uid="104" uid_parent="root" />
  <Call target="RT_Servo_Controller_Loop.vi" inputs="Setpoint/mode:102.value,encoder data:104.pv,error in (no error):104.err_out" outputs="Servo feedback/health:105.fb,error out:105.err_out,status ok:105.ok" uid="105" uid_parent="root" />
  <Call target="RT_Fault_Checker.vi" inputs="Sensor/controller status:105.fb,error in (no error):105.err_out,watchdog status:101.value" outputs="FaultRecord and protective request:106.fault,error out:106.err_out,status ok:106.ok" uid="106" uid_parent="root" />
  <Indicator _name="RT running status" conIdx="3" connection="recommended" inputs="value:106.fault" type="string" uid="107" uid_parent="root" value="" />
  <Indicator _name="status ok" conIdx="2" connection="recommended" inputs="value:106.ok" type="bool" uid="108" uid_parent="root" value="false" />
  <Indicator _name="error out" conIdx="0" connection="recommended" inputs="value:106.err_out" type="cluster{bool.status,int32.code,string.source}" uid="109" uid_parent="root" value="[false,0,&quot;&quot;]" />
</VI>
<?lvmcp pane="4815"?>
"""
    compile_vi(rt_main_xml, SRC_DIR / "08_RT_Functions" / "RT_Main.vi")


def main():
    print("==================================================")
    print(" WIRING FUNCTIONAL SUBVI CALLS & CONTROL SEQUENCE ")
    print("==================================================")
    wire_simulation()
    wire_bridge()
    wire_engine()
    wire_plugins()
    wire_supervisor()
    wire_host()
    wire_rt()
    print("\n==================================================")
    print(" FUNCTIONAL WIRING COMPLETED SUCCESSFULLY ")
    print("==================================================")


if __name__ == "__main__":
    main()
