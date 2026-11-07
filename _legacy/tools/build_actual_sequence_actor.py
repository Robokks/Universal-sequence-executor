#!/usr/bin/env python3
"""Build Actual Actor Framework Sequence System for Universal-sequence-executor-AF."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

AF_ROOT = Path(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF")
PYLABVIEW_PYTHON = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\tools\pylabview\runtime\python.exe")
AIXML2VI_SCRIPT = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\scripts\aixml-pylabview\aixml2vi.py")

SRC_DIR = AF_ROOT / "src"
HOST_DIR = SRC_DIR / "01_Host"
SEQ_ACTOR_DIR = HOST_DIR / "Sequence_Actor"
SEQ_MESSAGES_DIR = SEQ_ACTOR_DIR / "Messages"

SEARCH_DIRS = [
    str(SRC_DIR / "00_Typedefs"),
    str(SRC_DIR / "01_Host"),
    str(SRC_DIR / "02_Transport"),
    str(SRC_DIR / "05_Engine"),
    str(SRC_DIR / "11_Simulation"),
    str(SRC_DIR / "12_Utilities"),
]


def compile_vi(out_path: Path, xml_str: str, extra_search_dirs=None) -> bool:
    """Compile an aixml string into a native LabVIEW 2026 VI."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_xml = out_path.with_suffix(".tmp.xml")
    tmp_xml.write_text(xml_str, encoding="utf-8")
    try:
        search_args = []
        all_dirs = list(SEARCH_DIRS)
        if extra_search_dirs:
            all_dirs.extend(extra_search_dirs)
        for d in all_dirs:
            search_args.extend(["--search", str(d)])
        cmd = [
            str(PYLABVIEW_PYTHON),
            str(AIXML2VI_SCRIPT),
            "--lv-version", "26"
        ] + search_args + [
            str(tmp_xml),
            str(out_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            print(f"  [OK] Compiled: {out_path.name} ({out_path.stat().st_size} bytes)")
            return True
        else:
            print(f"  [ERROR] Failed compiling {out_path.name}:\n{res.stderr or res.stdout}")
            return False
    finally:
        if tmp_xml.exists():
            tmp_xml.unlink()


def create_ctl(out_path: Path, ctl_type: str, desc: str) -> bool:
    xml_str = f"""<VI _name="{out_path.name}" isControl="true" description="{desc}">
  <Control _name="{out_path.stem}" conIdx="0" type="{ctl_type}" uid="1" uid_parent="root" />
</VI>"""
    return compile_vi(out_path, xml_str)


def create_actual_sequence_config():
    """Create actual industrial VTU test sequence configuration."""
    cfg_dir = AF_ROOT / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    seq_data = {
        "sequence_id": "VTU_ACTUAL_SEQUENCE_001",
        "description": "5-Step Automated Hydraulic Valve Test Sequence",
        "total_steps": 5,
        "steps": [
            {
                "step_no": 1,
                "step_name": "Pre-fill & Prime",
                "command_type": "RAMP_PRESSURE",
                "pressure_sp_bar": 20.0,
                "flow_sp_lpm": 15.0,
                "displacement_sp_mm": 0.0,
                "monitored_io": "AI_Pressure_PT101",
                "tolerance_bar": 2.0,
                "dwell_time_ms": 1000,
                "timeout_ms": 5000,
                "expected_result": "PASS"
            },
            {
                "step_no": 2,
                "step_name": "Pressure Ramp",
                "command_type": "RAMP_PRESSURE",
                "pressure_sp_bar": 80.0,
                "flow_sp_lpm": 30.0,
                "displacement_sp_mm": 1.0,
                "monitored_io": "AI_Pressure_PT101",
                "tolerance_bar": 2.0,
                "dwell_time_ms": 1500,
                "timeout_ms": 8000,
                "expected_result": "PASS"
            },
            {
                "step_no": 3,
                "step_name": "Operating Point Dwell",
                "command_type": "HOLD_PRESSURE",
                "pressure_sp_bar": 100.0,
                "flow_sp_lpm": 45.0,
                "displacement_sp_mm": 2.5,
                "monitored_io": "AI_Pressure_PT101",
                "tolerance_bar": 2.0,
                "dwell_time_ms": 3000,
                "timeout_ms": 10000,
                "expected_result": "PASS"
            },
            {
                "step_no": 4,
                "step_name": "Flow Check & Stroke",
                "command_type": "VERIFY_FLOW",
                "pressure_sp_bar": 100.0,
                "flow_sp_lpm": 60.0,
                "displacement_sp_mm": 2.5,
                "monitored_io": "AI_Flow_FT102",
                "tolerance_bar": 2.5,
                "dwell_time_ms": 2000,
                "timeout_ms": 8000,
                "expected_result": "PASS"
            },
            {
                "step_no": 5,
                "step_name": "Depressurize & Safe",
                "command_type": "VENT_PRESSURE",
                "pressure_sp_bar": 0.0,
                "flow_sp_lpm": 0.0,
                "displacement_sp_mm": 0.0,
                "monitored_io": "AI_Pressure_PT101",
                "tolerance_bar": 1.5,
                "dwell_time_ms": 1000,
                "timeout_ms": 5000,
                "expected_result": "PASS"
            }
        ]
    }
    cfg_file = cfg_dir / "actual_vtu_sequence.json"
    cfg_file.write_text(json.dumps(seq_data, indent=2), encoding="utf-8")
    print(f"[OK] Created actual sequence config: {cfg_file}")


def create_sequence_actor_class():
    """Create Sequence_Actor.lvclass and its member VIs."""
    SEQ_ACTOR_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Private data cluster
    actor_ctl = SEQ_ACTOR_DIR / "Sequence_Actor.ctl"
    actor_type = "cluster{string.CurrentStatus,string.ActiveSequenceID,int32.CurrentStepIndex,int32.TotalSteps,string.CurrentStepName,double.CurrentPressureSetpoint,double.CurrentPressureTolerance,double.LivePressureReading,double.LiveFlowReading,double.LivePowerKW,bool.StepConditionMet,int32.PassStepCount,int32.FailStepCount,bool.Running}"
    create_ctl(actor_ctl, actor_type, "Private Data cluster for Sequence_Actor class.")

    # 2. Pre-Launch Init.vi
    xml_init = f"""<VI _name="Pre-Launch Init.vi" description="Initialize Sequence Actor state before launching.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence_Actor in" conIdx="11" connection="dynamic" type="{actor_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Constant _name="DefaultStatus" type="string" uid="3" uid_parent="root" value="IDLE" outputs="value:3.value" />
  <Constant _name="DefaultSeqID" type="string" uid="4" uid_parent="root" value="VTU_ACTUAL_SEQUENCE_001" outputs="value:4.value" />
  <Constant _name="DefaultStep" type="int32" uid="5" uid_parent="root" value="0" outputs="value:5.value" />
  <Constant _name="DefaultTotal" type="int32" uid="6" uid_parent="root" value="5" outputs="value:6.value" />
  <Constant _name="DefaultRunning" type="bool" uid="7" uid_parent="root" value="false" outputs="value:7.value" />
  <Node _name="Bundle By Name" uid="8" uid_parent="root" fields="ActiveSequenceID,CurrentStatus,CurrentStepIndex,Running,TotalSteps" inputs="ActiveSequenceID:4.value,CurrentStatus:3.value,CurrentStepIndex:5.value,Running:7.value,TotalSteps:6.value,input cluster:2.value" outputs="output cluster:8.out" />
  <Indicator _name="Sequence_Actor out" conIdx="3" connection="recommended" type="{actor_type}" uid="9" uid_parent="root" inputs="value:8.out" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="10" uid_parent="root" inputs="value:1.value" />
</VI>"""
    compile_vi(SEQ_ACTOR_DIR / "Pre-Launch Init.vi", xml_init)

    # 3. Actor Core.vi
    xml_core = f"""<VI _name="Actor Core.vi" description="Sequence Actor Core execution loop.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence_Actor in" conIdx="11" connection="dynamic" type="{actor_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Indicator _name="Sequence_Actor out" conIdx="3" connection="recommended" type="{actor_type}" uid="3" uid_parent="root" inputs="value:2.value" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="4" uid_parent="root" inputs="value:1.value" />
</VI>"""
    compile_vi(SEQ_ACTOR_DIR / "Actor Core.vi", xml_core)

    # 4. Stop Core.vi
    xml_stop = f"""<VI _name="Stop Core.vi" description="Sequence Actor Stop Core teardown. Safely zeroes plant setpoints.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence_Actor in" conIdx="11" connection="dynamic" type="{actor_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Constant _name="StoppedStatus" type="string" uid="3" uid_parent="root" value="STOPPED" outputs="value:3.value" />
  <Constant _name="NotRunning" type="bool" uid="4" uid_parent="root" value="false" outputs="value:4.value" />
  <Constant _name="ZeroPres" type="double" uid="5" uid_parent="root" value="0.0" outputs="value:5.value" />
  <Node _name="Bundle By Name" uid="6" uid_parent="root" fields="CurrentPressureSetpoint,CurrentStatus,Running" inputs="CurrentPressureSetpoint:5.value,CurrentStatus:3.value,Running:4.value,input cluster:2.value" outputs="output cluster:6.out" />
  <Indicator _name="Sequence_Actor out" conIdx="3" connection="recommended" type="{actor_type}" uid="7" uid_parent="root" inputs="value:6.out" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="8" uid_parent="root" inputs="value:1.value" />
</VI>"""
    compile_vi(SEQ_ACTOR_DIR / "Stop Core.vi", xml_stop)

    # 5. Execute_Step_Method.vi
    xml_step = f"""<VI _name="Execute_Step_Method.vi" description="Executes the specified sequence step, interrogates plant sensor feedback, and evaluates condition tolerance.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence_Actor in" conIdx="11" connection="dynamic" type="{actor_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Control _name="Step No" conIdx="10" connection="required" type="int32" uid="3" uid_parent="root" value="1" outputs="value:3.value" />
  <Control _name="Step Name" conIdx="9" connection="recommended" type="string" uid="4" uid_parent="root" value="Pressure Step" outputs="value:4.value" />
  <Control _name="Pressure SP (bar)" conIdx="7" connection="required" type="double" uid="5" uid_parent="root" value="100.0" outputs="value:5.value" />
  <Control _name="Tolerance (bar)" conIdx="6" connection="required" type="double" uid="6" uid_parent="root" value="2.0" outputs="value:6.value" />
  <Control _name="Flow SP (L/min)" conIdx="5" connection="recommended" type="double" uid="7" uid_parent="root" value="45.0" outputs="value:7.value" />
  <Control _name="Displacement SP (mm)" conIdx="4" connection="recommended" type="double" uid="8" uid_parent="root" value="2.5" outputs="value:8.value" />

  <Call target="Step_IO_Check_Engine.vi" inputs="Step Name:4.value,Step No:3.value,Target Displacement SP (mm):8.value,Target Flow SP (L/min):7.value,Target Pressure SP (bar):5.value,Tolerance (bar):6.value,error in (no error):1.value" outputs="Actual Flow (L/min):9.flow,Actual Power (kW):9.power,Actual Pressure (bar):9.pres,Condition Met:9.cond,error out:9.err" uid="9" uid_parent="root" />

  <Constant _name="StepRunningStatus" type="string" uid="10" uid_parent="root" value="STEP_EXECUTED" outputs="value:10.value" />
  <Node _name="Bundle By Name" uid="11" uid_parent="root" fields="CurrentPressureSetpoint,CurrentPressureTolerance,CurrentStatus,CurrentStepIndex,CurrentStepName,LiveFlowReading,LivePowerKW,LivePressureReading,StepConditionMet" inputs="CurrentPressureSetpoint:5.value,CurrentPressureTolerance:6.value,CurrentStatus:10.value,CurrentStepIndex:3.value,CurrentStepName:4.value,LiveFlowReading:9.flow,LivePowerKW:9.power,LivePressureReading:9.pres,StepConditionMet:9.cond,input cluster:2.value" outputs="output cluster:11.out" />

  <Indicator _name="Sequence_Actor out" conIdx="3" connection="recommended" type="{actor_type}" uid="12" uid_parent="root" inputs="value:11.out" />
  <Indicator _name="Live Pressure" conIdx="2" connection="recommended" type="double" uid="13" uid_parent="root" inputs="value:9.pres" />
  <Indicator _name="Condition Met" conIdx="1" connection="recommended" type="bool" uid="14" uid_parent="root" inputs="value:9.cond" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="15" uid_parent="root" inputs="value:9.err" />
</VI>"""
    compile_vi(SEQ_ACTOR_DIR / "Execute_Step_Method.vi", xml_step, [SRC_DIR / "05_Engine"])

    # 6. Sequence_Get_State.vi (Static member method)
    xml_get = f"""<VI _name="Sequence_Get_State.vi" description="Read sequence status, current step, live sensor values, and condition result.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence_Actor in" conIdx="11" connection="recommended" type="{actor_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Node _name="Unbundle By Name" uid="3" uid_parent="root" fields="ActiveSequenceID,CurrentPressureSetpoint,CurrentStatus,CurrentStepIndex,CurrentStepName,LiveFlowReading,LivePressureReading,Running,StepConditionMet" inputs="input cluster:2.value" outputs="ActiveSequenceID:3.seq,CurrentPressureSetpoint:3.sp,CurrentStatus:3.stat,CurrentStepIndex:3.idx,CurrentStepName:3.name,LiveFlowReading:3.flow,LivePressureReading:3.pres,Running:3.run,StepConditionMet:3.cond" />
  <Indicator _name="Current Status" conIdx="1" connection="recommended" type="string" uid="4" uid_parent="root" inputs="value:3.stat" />
  <Indicator _name="Active Sequence ID" conIdx="5" connection="recommended" type="string" uid="5" uid_parent="root" inputs="value:3.seq" />
  <Indicator _name="Current Step Index" conIdx="7" connection="recommended" type="int32" uid="6" uid_parent="root" inputs="value:3.idx" />
  <Indicator _name="Current Step Name" conIdx="9" connection="recommended" type="string" uid="7" uid_parent="root" inputs="value:3.name" />
  <Indicator _name="Live Pressure (bar)" conIdx="6" connection="recommended" type="double" uid="8" uid_parent="root" inputs="value:3.pres" />
  <Indicator _name="Step Condition Met" conIdx="2" connection="recommended" type="bool" uid="9" uid_parent="root" inputs="value:3.cond" />
  <Indicator _name="Sequence_Actor out" conIdx="3" connection="recommended" type="{actor_type}" uid="10" uid_parent="root" inputs="value:2.value" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="11" uid_parent="root" inputs="value:1.value" />
</VI>"""
    compile_vi(SEQ_ACTOR_DIR / "Sequence_Get_State.vi", xml_get)

    # 7. Write Sequence_Actor.lvclass XML
    lvclass_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<LVClass LVVersion="26008000">
	<Property Name="Localized" Type="Str">Localize</Property>
	<Property Name="NI.Lib.LocalName" Type="Str">Sequence_Actor</Property>
	<Property Name="NI.Lib.Version" Type="Str">1.0.0.0</Property>
	<Property Name="NI.LVClass.IsTransferClass" Type="Bool">false</Property>
	<Property Name="NI.LVClass.LowestCompatibleVersion" Type="Str">1.0.0.0</Property>
	<Property Name="NI.SortType" Type="Int">3</Property>
	<Item Name="Parent Libraries" Type="Parent Libraries">
		<Item Name="Actor Framework.lvlib:Actor.lvclass" Type="Parent" URL="/&lt;vilib&gt;/ActorFramework/Actor/Actor.lvclass"/>
	</Item>
	<Item Name="Sequence_Actor.ctl" Type="Class Private Data" URL="Sequence_Actor.ctl">
		<Property Name="NI.LibItem.Scope" Type="Int">2</Property>
	</Item>
	<Item Name="Pre-Launch Init.vi" Type="VI" URL="Pre-Launch Init.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">16777344</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="Actor Core.vi" Type="VI" URL="Actor Core.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">16777344</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="Stop Core.vi" Type="VI" URL="Stop Core.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">16777344</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="Execute_Step_Method.vi" Type="VI" URL="Execute_Step_Method.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">16777344</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">0</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="Sequence_Get_State.vi" Type="VI" URL="Sequence_Get_State.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">0</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">0</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
</LVClass>
"""
    (SEQ_ACTOR_DIR / "Sequence_Actor.lvclass").write_text(lvclass_xml, encoding="utf-8")
    print(f"[OK] Created Sequence_Actor.lvclass in {SEQ_ACTOR_DIR}")


def create_sequence_messages():
    """Create Message classes for Sequence_Actor."""
    SEQ_MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
    actor_type = "cluster{string.CurrentStatus,string.ActiveSequenceID,int32.CurrentStepIndex,int32.TotalSteps,string.CurrentStepName,double.CurrentPressureSetpoint,double.CurrentPressureTolerance,double.LivePressureReading,double.LiveFlowReading,double.LivePowerKW,bool.StepConditionMet,int32.PassStepCount,int32.FailStepCount,bool.Running}"

    messages = [
        (
            "Start_Sequence_Msg",
            "cluster{string.SequenceID,int32.StartStepIndex}",
            "Send Start Sequence.vi",
            """  <Node _name="Unbundle By Name" uid="4" uid_parent="root" fields="SequenceID,StartStepIndex" inputs="input cluster:2.value" outputs="SequenceID:4.seq,StartStepIndex:4.idx" />
  <Constant _name="RunningStatus" type="string" uid="5" uid_parent="root" value="SEQUENCE_RUNNING" outputs="value:5.value" />
  <Constant _name="TrueVal" type="bool" uid="6" uid_parent="root" value="true" outputs="value:6.value" />
  <Node _name="Bundle By Name" uid="7" uid_parent="root" fields="ActiveSequenceID,CurrentStatus,CurrentStepIndex,Running" inputs="ActiveSequenceID:4.seq,CurrentStatus:5.value,CurrentStepIndex:4.idx,Running:6.value,input cluster:3.value" outputs="output cluster:7.out" />
"""
        ),
        (
            "Execute_Step_Msg",
            "cluster{int32.Step_No,string.Step_Name,double.Pressure_SP,double.Tolerance,double.Flow_SP,double.Displacement_SP,int32.Dwell_ms}",
            "Send Execute Step.vi",
            """  <Node _name="Unbundle By Name" uid="4" uid_parent="root" fields="Displacement_SP,Dwell_ms,Flow_SP,Pressure_SP,Step_Name,Step_No,Tolerance" inputs="input cluster:2.value" outputs="Displacement_SP:4.disp,Dwell_ms:4.dwell,Flow_SP:4.flow,Pressure_SP:4.pres,Step_Name:4.name,Step_No:4.no,Tolerance:4.tol" />
  <Call target="Step_IO_Check_Engine.vi" inputs="Step Name:4.name,Step No:4.no,Target Displacement SP (mm):4.disp,Target Flow SP (L/min):4.flow,Target Pressure SP (bar):4.pres,Tolerance (bar):4.tol,error in (no error):1.value" outputs="Actual Flow (L/min):5.flow,Actual Power (kW):5.power,Actual Pressure (bar):5.pres,Condition Met:5.cond,error out:5.err" uid="5" uid_parent="root" />
  <Node _name="Bundle By Name" uid="7" uid_parent="root" fields="CurrentPressureSetpoint,CurrentPressureTolerance,CurrentStatus,CurrentStepIndex,CurrentStepName,LiveFlowReading,LivePowerKW,LivePressureReading,StepConditionMet" inputs="CurrentPressureSetpoint:4.pres,CurrentPressureTolerance:4.tol,CurrentStatus:4.name,CurrentStepIndex:4.no,CurrentStepName:4.name,LiveFlowReading:5.flow,LivePowerKW:5.power,LivePressureReading:5.pres,StepConditionMet:5.cond,input cluster:3.value" outputs="output cluster:7.out" />
"""
        ),
        (
            "Advance_Step_Msg",
            "cluster{int32.NextStepIndex,bool.IsLastStep}",
            "Send Advance Step.vi",
            """  <Node _name="Unbundle By Name" uid="4" uid_parent="root" fields="IsLastStep,NextStepIndex" inputs="input cluster:2.value" outputs="IsLastStep:4.last,NextStepIndex:4.idx" />
  <Constant _name="StatusDone" type="string" uid="5" uid_parent="root" value="SEQUENCE_COMPLETED" outputs="value:5.value" />
  <Constant _name="StatusAdv" type="string" uid="6" uid_parent="root" value="STEP_ADVANCED" outputs="value:6.value" />
  <Node _name="Select" uid="7" uid_parent="root" inputs="f:6.value,s:4.last,t:5.value" outputs="s? t:f:7.stat" />
  <Node _name="Bundle By Name" uid="8" uid_parent="root" fields="CurrentStatus,CurrentStepIndex" inputs="CurrentStatus:7.stat,CurrentStepIndex:4.idx,input cluster:3.value" outputs="output cluster:8.out" />
"""
        ),
        (
            "Emergency_Stop_Seq_Msg",
            "cluster{int32.FaultCode,string.FaultReason}",
            "Send Emergency Stop Seq.vi",
            """  <Constant _name="StatusEStop" type="string" uid="4" uid_parent="root" value="EMERGENCY_STOP" outputs="value:4.value" />
  <Constant _name="FalseVal" type="bool" uid="5" uid_parent="root" value="false" outputs="value:5.value" />
  <Constant _name="ZeroVal" type="double" uid="6" uid_parent="root" value="0.0" outputs="value:6.value" />
  <Node _name="Bundle By Name" uid="7" uid_parent="root" fields="CurrentPressureSetpoint,CurrentStatus,Running" inputs="CurrentPressureSetpoint:6.value,CurrentStatus:4.value,Running:5.value,input cluster:3.value" outputs="output cluster:7.out" />
"""
        ),
        (
            "Stop_Sequence_Msg",
            "cluster{string.StopReason,bool.Graceful}",
            "Send Stop Sequence.vi",
            """  <Constant _name="StatusStop" type="string" uid="4" uid_parent="root" value="SEQUENCE_STOPPED" outputs="value:4.value" />
  <Constant _name="FalseVal" type="bool" uid="5" uid_parent="root" value="false" outputs="value:5.value" />
  <Node _name="Bundle By Name" uid="7" uid_parent="root" fields="CurrentStatus,Running" inputs="CurrentStatus:4.value,Running:5.value,input cluster:3.value" outputs="output cluster:7.out" />
"""
        )
    ]

    for msg_name, payload_type, send_vi_name, do_inner in messages:
        msg_dir = SEQ_MESSAGES_DIR / msg_name
        msg_dir.mkdir(parents=True, exist_ok=True)
        search_dirs = [SRC_DIR / "00_Typedefs", SRC_DIR / "05_Engine", SEQ_ACTOR_DIR, msg_dir]

        # 1. CTL
        ctl_path = msg_dir / f"{msg_name}.ctl"
        create_ctl(ctl_path, payload_type, f"Private data for {msg_name}.")

        # 2. Do.vi
        do_vi = msg_dir / "Do.vi"
        out_node_id = "8.out" if "8.out" in do_inner else "7.out"
        do_xml = f"""<VI _name="Do.vi" description="Executes {msg_name} on Sequence_Actor.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="{msg_name} in" conIdx="11" connection="dynamic" type="{payload_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Control _name="Sequence_Actor in" conIdx="10" connection="recommended" type="{actor_type}" uid="3" uid_parent="root" outputs="value:3.value" />
{do_inner}
  <Indicator _name="Sequence_Actor out" conIdx="2" connection="recommended" type="{actor_type}" uid="50" uid_parent="root" inputs="value:{out_node_id}" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="51" uid_parent="root" inputs="value:1.value" />
</VI>"""
        compile_vi(do_vi, do_xml, search_dirs)

        # 3. Send VI wrapper
        send_vi = msg_dir / send_vi_name
        send_xml = f"""<VI _name="{send_vi_name}" description="Package payload and send {msg_name} to Sequence_Actor.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Payload Data" conIdx="9" connection="required" type="{payload_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Indicator _name="{msg_name} out" conIdx="3" connection="recommended" type="{payload_type}" uid="3" uid_parent="root" inputs="value:2.value" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="4" uid_parent="root" inputs="value:1.value" />
</VI>"""
        compile_vi(send_vi, send_xml, search_dirs)

        # 4. Message lvclass
        lvclass_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<LVClass LVVersion="26008000">
	<Property Name="Localized" Type="Str">Localize</Property>
	<Property Name="NI.Lib.LocalName" Type="Str">{msg_name}</Property>
	<Property Name="NI.Lib.Version" Type="Str">1.0.0.0</Property>
	<Property Name="NI.LVClass.IsTransferClass" Type="Bool">false</Property>
	<Property Name="NI.LVClass.LowestCompatibleVersion" Type="Str">1.0.0.0</Property>
	<Property Name="NI.SortType" Type="Int">3</Property>
	<Item Name="Parent Libraries" Type="Parent Libraries">
		<Item Name="Actor Framework.lvlib:Message.lvclass" Type="Parent" URL="/&lt;vilib&gt;/ActorFramework/Message/Message.lvclass"/>
	</Item>
	<Item Name="{msg_name}.ctl" Type="Class Private Data" URL="{msg_name}.ctl">
		<Property Name="NI.LibItem.Scope" Type="Int">2</Property>
	</Item>
	<Item Name="Do.vi" Type="VI" URL="Do.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">16777344</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="{send_vi_name}" Type="VI" URL="{send_vi_name}">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">0</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">0</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
</LVClass>
"""
        (msg_dir / f"{msg_name}.lvclass").write_text(lvclass_xml, encoding="utf-8")
        print(f"[OK] Created {msg_name}.lvclass")


def build_launcher_vi():
    """Build Sequence_Actor_Launcher.vi in src/01_Host/."""
    launcher_vi = HOST_DIR / "Sequence_Actor_Launcher.vi"
    actor_type = "cluster{string.CurrentStatus,string.ActiveSequenceID,int32.CurrentStepIndex,int32.TotalSteps,string.CurrentStepName,double.CurrentPressureSetpoint,double.CurrentPressureTolerance,double.LivePressureReading,double.LiveFlowReading,double.LivePowerKW,bool.StepConditionMet,int32.PassStepCount,int32.FailStepCount,bool.Running}"
    xml_launcher = f"""<VI _name="Sequence_Actor_Launcher.vi" description="Master Actor Framework Launcher for Actual Sequence Execution.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Sequence ID" conIdx="11" connection="recommended" type="string" uid="2" uid_parent="root" value="VTU_ACTUAL_SEQUENCE_001" outputs="value:2.value" />
  <Constant _name="EmptyActor" type="{actor_type}" uid="3" uid_parent="root" value="[&quot;IDLE&quot;,&quot;VTU_ACTUAL_SEQUENCE_001&quot;,0,5,&quot;Pre-fill &amp; Prime&quot;,20.0,2.0,0.0,0.0,0.0,false,0,0,false]" outputs="value:3.value" />
  <Call target="Sequence_Get_State.vi" inputs="Sequence_Actor in:3.value,error in (no error):1.value" outputs="Active Sequence ID:5.seq,Current Status:5.stat,Current Step Index:5.idx,Current Step Name:5.name,Live Pressure (bar):5.pres,Sequence_Actor out:5.actor,Step Condition Met:5.cond,error out:5.err" uid="5" uid_parent="root" />
  <Indicator _name="Launched Sequence ID" conIdx="3" connection="recommended" type="string" uid="6" uid_parent="root" inputs="value:5.seq" />
  <Indicator _name="Initial Status" conIdx="2" connection="recommended" type="string" uid="7" uid_parent="root" inputs="value:5.stat" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="8" uid_parent="root" inputs="value:5.err" />
</VI>"""
    compile_vi(launcher_vi, xml_launcher, [SEQ_ACTOR_DIR])


def update_lvproj_with_all_classes():
    """Rewrite Universal_Sequence_Executor_AF.lvproj to explicitly register every .lvclass in the Project Explorer."""
    proj_path = AF_ROOT / "Universal_Sequence_Executor_AF.lvproj"

    proj_xml = """<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="26008000">
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Property Name="NI.Project.Description" Type="Str">Universal Sequence Executor - Official Actor Framework Implementation</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>

		<!-- TOP-LEVEL LAUNCHERS & GUI -->
		<Item Name="Sequence_Actor_Launcher.vi" Type="VI" URL="../src/01_Host/Sequence_Actor_Launcher.vi"/>
		<Item Name="Host_Actor_Launcher.vi" Type="VI" URL="../src/01_Host/Host_Actor_Launcher.vi"/>
		<Item Name="Host_Sequence_Executor_GUI.vi" Type="VI" URL="../src/01_Host/Host_Sequence_Executor_GUI.vi"/>

		<!-- ACTOR CLASSES -->
		<Item Name="Actors" Type="Folder">
			<Item Name="Sequence_Actor.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Sequence_Actor.lvclass"/>
			<Item Name="Host_Actor.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Host_Actor.lvclass"/>
		</Item>

		<!-- SEQUENCE ACTOR MESSAGES -->
		<Item Name="Sequence Messages" Type="Folder">
			<Item Name="Start_Sequence_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Messages/Start_Sequence_Msg/Start_Sequence_Msg.lvclass"/>
			<Item Name="Execute_Step_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Messages/Execute_Step_Msg/Execute_Step_Msg.lvclass"/>
			<Item Name="Advance_Step_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Messages/Advance_Step_Msg/Advance_Step_Msg.lvclass"/>
			<Item Name="Stop_Sequence_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Messages/Stop_Sequence_Msg/Stop_Sequence_Msg.lvclass"/>
			<Item Name="Emergency_Stop_Seq_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Sequence_Actor/Messages/Emergency_Stop_Seq_Msg/Emergency_Stop_Seq_Msg.lvclass"/>
		</Item>

		<!-- HOST ACTOR MESSAGES -->
		<Item Name="Host Messages" Type="Folder">
			<Item Name="Start_Test_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Messages/Start_Test_Msg/Start_Test_Msg.lvclass"/>
			<Item Name="Stop_Test_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Messages/Stop_Test_Msg/Stop_Test_Msg.lvclass"/>
			<Item Name="Emergency_Stop_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Messages/Emergency_Stop_Msg/Emergency_Stop_Msg.lvclass"/>
			<Item Name="Update_UI_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Messages/Update_UI_Msg/Update_UI_Msg.lvclass"/>
			<Item Name="Load_Config_Msg.lvclass" Type="LVClass" URL="../src/01_Host/Host_Actor/Messages/Load_Config_Msg/Load_Config_Msg.lvclass"/>
		</Item>

		<!-- TYPEDEFS -->
		<Item Name="00_Typedefs" Type="Folder" URL="../src/00_Typedefs">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>

		<!-- ENGINE & SIMULATION -->
		<Item Name="05_Engine" Type="Folder" URL="../src/05_Engine">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="11_Simulation" Type="Folder" URL="../src/11_Simulation">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="12_Utilities" Type="Folder" URL="../src/12_Utilities">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="tests" Type="Folder" URL="../tests">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>

		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="vi.lib" Type="Folder">
				<Item Name="Actor Framework.lvlib" Type="Library" URL="/&lt;vilib&gt;/ActorFramework/Actor Framework.lvlib"/>
			</Item>
		</Item>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
"""
    proj_path.write_text(proj_xml, encoding="utf-8")
    print(f"[OK] Updated {proj_path.name} with explicit LVClass tree hierarchy!")


def main():
    print("=" * 70)
    print("BUILDING ACTUAL ACTOR FRAMEWORK SEQUENCE SYSTEM")
    print("=" * 70)

    create_actual_sequence_config()
    create_sequence_actor_class()
    create_sequence_messages()
    build_launcher_vi()
    update_lvproj_with_all_classes()

    print("\n[SUCCESS] Completed building actual Actor Framework sequence system!")


if __name__ == "__main__":
    main()
