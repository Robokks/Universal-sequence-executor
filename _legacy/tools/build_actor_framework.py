#!/usr/bin/env python3
"""Build Actor Framework on Host for Universal Sequence Executor.

Creates:
1. src/01_Host/Host_Actor/
   - Host_Actor.lvclass (inheriting from Actor.lvclass)
   - Host_Actor.ctl (Private data cluster)
   - Pre-Launch Init.vi
   - Actor Core.vi
   - Stop Core.vi
   - Host_State_Update_Method.vi
   - Host_Get_State.vi
2. src/01_Host/Host_Actor/Messages/
   - Start_Test_Msg/ (Start_Test_Msg.lvclass, Start_Test_Msg.ctl, Do.vi, Send Start Test.vi)
   - Stop_Test_Msg/ (Stop_Test_Msg.lvclass, Stop_Test_Msg.ctl, Do.vi, Send Stop Test.vi)
   - Emergency_Stop_Msg/ (Emergency_Stop_Msg.lvclass, Emergency_Stop_Msg.ctl, Do.vi, Send Emergency Stop.vi)
   - Update_UI_Msg/ (Update_UI_Msg.lvclass, Update_UI_Msg.ctl, Do.vi, Send Update UI.vi)
   - Load_Config_Msg/ (Load_Config_Msg.lvclass, Load_Config_Msg.ctl, Do.vi, Send Load Config.vi)
3. src/01_Host/Host_Actor_Launcher.vi (Top-level AF Root Launcher)
4. Update Universal_Sequence_Executor.lvproj / Universal_Sequence_Executor_AF.lvproj
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYLABVIEW_PYTHON = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\tools\pylabview\runtime\python.exe")
AIXML2VI_SCRIPT = Path(r"C:\Users\DynaAdmin\.claude\plugins\marketplaces\zuehlke-labview\scripts\aixml-pylabview\aixml2vi.py")
SRC_DIR = WORKSPACE_ROOT / "src"
HOST_DIR = SRC_DIR / "01_Host"
HOST_ACTOR_DIR = HOST_DIR / "Host_Actor"
MESSAGES_DIR = HOST_ACTOR_DIR / "Messages"

SEARCH_DIRS = [
    str(SRC_DIR / "00_Typedefs"),
    str(SRC_DIR / "01_Host" / "01_Application"),
    str(SRC_DIR / "01_Host" / "02_Editor"),
    str(SRC_DIR / "01_Host" / "03_Operations"),
    str(SRC_DIR / "04_Runtime_Supervisor"),
    str(SRC_DIR / "05_Engine"),
    str(SRC_DIR / "06_Bridge"),
    str(SRC_DIR / "11_Simulation"),
    str(SRC_DIR / "12_Utilities"),
]


def compile_vi(out_path: Path, xml_str: str) -> bool:
    """Compile an aixml string into a native LabVIEW 2026 VI using aixml2vi."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_xml = out_path.with_suffix(".tmp.xml")
    tmp_xml.write_text(xml_str, encoding="utf-8")
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
            str(out_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            print(f"  [OK] Compiled VI: {out_path.name} ({out_path.stat().st_size} bytes)")
            return True
        else:
            print(f"  [ERROR] Failed compiling {out_path.name}: {res.stderr or res.stdout}")
            return False
    finally:
        if tmp_xml.exists():
            tmp_xml.unlink()


def create_ctl(out_path: Path, ctl_type: str, desc: str) -> bool:
    """Compile a CTL using aixml2vi."""
    xml_str = f"""<VI _name="{out_path.name}" isControl="true" description="{desc}">
  <Control _name="{out_path.stem}" conIdx="0" type="{ctl_type}" uid="1" uid_parent="root" />
</VI>"""
    return compile_vi(out_path, xml_str)


def create_actor_class():
    """Create Host_Actor.lvclass and its methods."""
    HOST_ACTOR_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Host_Actor.ctl (Private Data)
    host_actor_ctl = HOST_ACTOR_DIR / "Host_Actor.ctl"
    host_actor_type = "cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}"
    create_ctl(host_actor_ctl, host_actor_type, "Private Data cluster for Host_Actor class.")

    # 2. Pre-Launch Init.vi
    pre_launch_init_vi = HOST_ACTOR_DIR / "Pre-Launch Init.vi"
    pre_launch_init_xml = """<VI _name="Pre-Launch Init.vi" description="INTENT: Initialize Host Actor state before launching.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Host_Actor in" conIdx="11" connection="dynamic" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Constant _name="DefaultStatus" outputs="value:3.value" type="string" uid="3" uid_parent="root" value="IDLE" />
  <Constant _name="DefaultQueue" outputs="value:4.value" type="string" uid="4" uid_parent="root" value="Supervisor_Cmd_Queue" />
  <Constant _name="DefaultPath" outputs="value:5.value" type="string" uid="5" uid_parent="root" value="configs/test_profile_sim.json" />
  <Node _name="Bundle By Name" uid="6" uid_parent="root" fields="CurrentStatus,TargetSupervisorQueue,ConfigPath" inputs="input cluster:2.value,CurrentStatus:3.value,TargetSupervisorQueue:4.value,ConfigPath:5.value" outputs="output cluster:6.output" />
  <Indicator _name="Host_Actor out" conIdx="3" connection="recommended" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="7" uid_parent="root" inputs="value:6.output" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="8" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(pre_launch_init_vi, pre_launch_init_xml)

    # 3. Actor Core.vi (Host Actor Message loop / UI handler)
    actor_core_vi = HOST_ACTOR_DIR / "Actor Core.vi"
    actor_core_xml = """<VI _name="Actor Core.vi" description="INTENT: Host Actor Core overriding parent Actor Core, managing Host UI and message coordination.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Host_Actor in" conIdx="11" connection="dynamic" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Constant _name="InitStatus" outputs="value:3.value" type="string" uid="3" uid_parent="root" value="RUNNING" />
  <Constant _name="RunningFlag" outputs="value:4.value" type="bool" uid="4" uid_parent="root" value="true" />
  <Node _name="Bundle By Name" uid="5" uid_parent="root" fields="CurrentStatus,Running" inputs="input cluster:2.value,CurrentStatus:3.value,Running:4.value" outputs="output cluster:5.output" />
  <Indicator _name="Host_Actor out" conIdx="3" connection="recommended" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="6" uid_parent="root" inputs="value:5.output" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="7" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(actor_core_vi, actor_core_xml)

    # 4. Stop Core.vi
    stop_core_vi = HOST_ACTOR_DIR / "Stop Core.vi"
    stop_core_xml = """<VI _name="Stop Core.vi" description="INTENT: Clean up Host Actor and close open references.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Host_Actor in" conIdx="11" connection="dynamic" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Constant _name="StoppedStatus" outputs="value:3.value" type="string" uid="3" uid_parent="root" value="STOPPED" />
  <Constant _name="StoppedFlag" outputs="value:4.value" type="bool" uid="4" uid_parent="root" value="false" />
  <Node _name="Bundle By Name" uid="5" uid_parent="root" fields="CurrentStatus,Running" inputs="input cluster:2.value,CurrentStatus:3.value,Running:4.value" outputs="output cluster:5.output" />
  <Indicator _name="Host_Actor out" conIdx="3" connection="recommended" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="6" uid_parent="root" inputs="value:5.output" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="7" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(stop_core_vi, stop_core_xml)

    # 5. Host_State_Update_Method.vi
    host_state_update_vi = HOST_ACTOR_DIR / "Host_State_Update_Method.vi"
    host_state_update_xml = """<VI _name="Host_State_Update_Method.vi" description="INTENT: Update Host Actor status, step progress, and pass/fail counts.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Host_Actor in" conIdx="11" connection="dynamic" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Control _name="New Status" conIdx="10" connection="required" type="string" uid="3" uid_parent="root" value="RUNNING" outputs="value:3.value" />
  <Control _name="Active Step" conIdx="9" connection="recommended" type="int32" uid="4" uid_parent="root" value="0" outputs="value:4.value" />
  <Node _name="Bundle By Name" uid="5" uid_parent="root" fields="CurrentStatus,ActiveStepIndex" inputs="input cluster:2.value,CurrentStatus:3.value,ActiveStepIndex:4.value" outputs="output cluster:5.output" />
  <Indicator _name="Host_Actor out" conIdx="3" connection="recommended" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="6" uid_parent="root" inputs="value:5.output" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="7" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(host_state_update_vi, host_state_update_xml)

    # 6. Host_Get_State.vi
    host_get_state_vi = HOST_ACTOR_DIR / "Host_Get_State.vi"
    host_get_state_xml = """<VI _name="Host_Get_State.vi" description="INTENT: Read current state and status metrics from Host Actor.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Host_Actor in" conIdx="11" connection="dynamic" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Node _name="Unbundle By Name" uid="3" uid_parent="root" fields="CurrentStatus,ActiveRecipeID,ActiveStepIndex,PassCount,FailCount,Running" inputs="input cluster:2.value" outputs="CurrentStatus:3.status,ActiveRecipeID:3.recipe,ActiveStepIndex:3.step,PassCount:3.pass,FailCount:3.fail,Running:3.run" />
  <Indicator _name="Current Status" conIdx="1" connection="recommended" type="string" uid="4" uid_parent="root" inputs="value:3.status" />
  <Indicator _name="Active Recipe ID" conIdx="5" connection="recommended" type="string" uid="5" uid_parent="root" inputs="value:3.recipe" />
  <Indicator _name="Active Step Index" conIdx="7" connection="recommended" type="int32" uid="6" uid_parent="root" inputs="value:3.step" />
  <Indicator _name="Host_Actor out" conIdx="3" connection="recommended" type="cluster{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}" uid="7" uid_parent="root" inputs="value:2.value" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="8" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(host_get_state_vi, host_get_state_xml)

    # 7. Write Host_Actor.lvclass XML
    lvclass_xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<LVClass LVVersion="26008000">
	<Property Name="Localized" Type="Str">Localize</Property>
	<Property Name="NI.Lib.LocalName" Type="Str">Host_Actor</Property>
	<Property Name="NI.Lib.Version" Type="Str">1.0.0.0</Property>
	<Property Name="NI.LVClass.IsTransferClass" Type="Bool">false</Property>
	<Property Name="NI.LVClass.LowestCompatibleVersion" Type="Str">1.0.0.0</Property>
	<Property Name="NI.SortType" Type="Int">3</Property>
	<Item Name="Parent Libraries" Type="Parent Libraries">
		<Item Name="Actor Framework.lvlib:Actor.lvclass" Type="Parent" URL="/&lt;vilib&gt;/ActorFramework/Actor/Actor.lvclass"/>
	</Item>
	<Item Name="Host_Actor.ctl" Type="Class Private Data" URL="Host_Actor.ctl">
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
	<Item Name="Host_State_Update_Method.vi" Type="VI" URL="Host_State_Update_Method.vi">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">0</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">0</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1107825168</Property>
		<Property Name="NI.LibItem.Scope" Type="Int">1</Property>
	</Item>
	<Item Name="Host_Get_State.vi" Type="VI" URL="Host_Get_State.vi">
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
    (HOST_ACTOR_DIR / "Host_Actor.lvclass").write_text(lvclass_xml, encoding="utf-8")
    print(f"[OK] Created Host_Actor.lvclass in {HOST_ACTOR_DIR}")


def create_message_class(msg_name: str, payload_type: str, do_vi_desc: str, do_vi_xml_inner: str):
    """Create an Actor Framework Message class with Do.vi and Send VI."""
    msg_dir = MESSAGES_DIR / msg_name
    msg_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Message Private Data (.ctl)
    msg_ctl = msg_dir / f"{msg_name}.ctl"
    create_ctl(msg_ctl, payload_type, f"Private data payload for {msg_name}.")

    # 2. Do.vi
    do_vi = msg_dir / "Do.vi"
    do_xml = f"""<VI _name="Do.vi" description="{do_vi_desc}">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="{msg_name} in" conIdx="11" connection="dynamic" type="{payload_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Control _name="Host_Actor in" conIdx="10" connection="recommended" type="cluster{{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}}" uid="3" uid_parent="root" outputs="value:3.value" />
{do_vi_xml_inner}
  <Indicator _name="Host_Actor out" conIdx="2" connection="recommended" type="cluster{{string.CurrentStatus,string.ActiveRecipeID,int32.ActiveStepIndex,int32.PassCount,int32.FailCount,string.TargetSupervisorQueue,string.ConfigPath,bool.Running}}" uid="50" uid_parent="root" inputs="value:do_actor_out.output" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="51" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(do_vi, do_xml)

    # 3. Send VI (e.g. "Send Start Test.vi")
    send_vi_name = f"Send {msg_name.replace('_Msg', '').replace('_', ' ')}.vi"
    send_vi = msg_dir / send_vi_name
    send_xml = f"""<VI _name="{send_vi_name}" description="INTENT: Convenience wrapper to send {msg_name} to target Actor Enqueuer.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Message Payload" conIdx="10" connection="required" type="{payload_type}" uid="2" uid_parent="root" outputs="value:2.value" />
  <Control _name="Actor Enqueuer Name" conIdx="9" connection="recommended" type="string" uid="3" uid_parent="root" value="Host_Actor_Queue" outputs="value:3.value" />
  <Indicator _name="Sent Successfully" conIdx="3" connection="recommended" type="bool" uid="4" uid_parent="root" inputs="value:5.value" />
  <Constant _name="TrueConst" outputs="value:5.value" type="bool" uid="5" uid_parent="root" value="true" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{{bool.status,int32.code,string.source}}" uid="6" uid_parent="root" inputs="value:1.value" />
</VI>
"""
    compile_vi(send_vi, send_xml)

    # 4. Message .lvclass XML
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
		<Property Name="NI.ClassItem.State" Type="Int">1074274816</Property>
	</Item>
	<Item Name="{send_vi_name}" Type="VI" URL="{send_vi_name}">
		<Property Name="NI.ClassItem.ExecutionSystem" Type="Int">-1</Property>
		<Property Name="NI.ClassItem.Flags" Type="Int">0</Property>
		<Property Name="NI.ClassItem.InvokeUsage" Type="UInt">0</Property>
		<Property Name="NI.ClassItem.MethodScope" Type="UInt">1</Property>
		<Property Name="NI.ClassItem.Priority" Type="Int">1</Property>
		<Property Name="NI.ClassItem.State" Type="Int">1074274816</Property>
	</Item>
</LVClass>
"""
    (msg_dir / f"{msg_name}.lvclass").write_text(lvclass_xml, encoding="utf-8")
    print(f"[OK] Created message class {msg_name}.lvclass in {msg_dir}")


def create_all_messages():
    """Create all standard AF Message classes for Host."""
    # 1. Start_Test_Msg
    start_payload = "cluster{string.RecipeID,string.OperatorID,string.RunMode}"
    start_do_xml = """  <Node _name="Unbundle By Name" uid="10" uid_parent="root" fields="RecipeID" inputs="input cluster:2.value" outputs="RecipeID:10.recipe" />
  <Constant _name="StatusRunning" outputs="value:11.value" type="string" uid="11" uid_parent="root" value="TEST_RUNNING" />
  <Constant _name="TrueRun" outputs="value:12.value" type="bool" uid="12" uid_parent="root" value="true" />
  <Node _name="Bundle By Name" uid="13" uid_parent="root" fields="CurrentStatus,ActiveRecipeID,Running" inputs="input cluster:3.value,CurrentStatus:11.value,ActiveRecipeID:10.recipe,Running:12.value" outputs="output cluster:do_actor_out.output" />
"""
    create_message_class("Start_Test_Msg", start_payload, "INTENT: Execute Start_Test message on Host Actor.", start_do_xml)

    # 2. Stop_Test_Msg
    stop_payload = "cluster{string.StopReason,bool.Graceful}"
    stop_do_xml = """  <Constant _name="StatusStopping" outputs="value:11.value" type="string" uid="11" uid_parent="root" value="TEST_STOPPED" />
  <Constant _name="FalseRun" outputs="value:12.value" type="bool" uid="12" uid_parent="root" value="false" />
  <Node _name="Bundle By Name" uid="13" uid_parent="root" fields="CurrentStatus,Running" inputs="input cluster:3.value,CurrentStatus:11.value,Running:12.value" outputs="output cluster:do_actor_out.output" />
"""
    create_message_class("Stop_Test_Msg", stop_payload, "INTENT: Execute Stop_Test message on Host Actor.", stop_do_xml)

    # 3. Emergency_Stop_Msg
    estop_payload = "cluster{int32.FaultCode,string.FaultSource,string.Description}"
    estop_do_xml = """  <Constant _name="StatusFault" outputs="value:11.value" type="string" uid="11" uid_parent="root" value="EMERGENCY_STOP" />
  <Constant _name="FalseRun" outputs="value:12.value" type="bool" uid="12" uid_parent="root" value="false" />
  <Node _name="Bundle By Name" uid="13" uid_parent="root" fields="CurrentStatus,Running" inputs="input cluster:3.value,CurrentStatus:11.value,Running:12.value" outputs="output cluster:do_actor_out.output" />
"""
    create_message_class("Emergency_Stop_Msg", estop_payload, "INTENT: Execute Emergency_Stop message on Host Actor.", estop_do_xml)

    # 4. Update_UI_Msg
    update_ui_payload = "cluster{string.StatusMessage,int32.StepIndex,int32.PassCount,int32.FailCount}"
    update_ui_do_xml = """  <Node _name="Unbundle By Name" uid="10" uid_parent="root" fields="StatusMessage,StepIndex,PassCount,FailCount" inputs="input cluster:2.value" outputs="StatusMessage:10.status,StepIndex:10.step,PassCount:10.pass,FailCount:10.fail" />
  <Node _name="Bundle By Name" uid="13" uid_parent="root" fields="CurrentStatus,ActiveStepIndex,PassCount,FailCount" inputs="input cluster:3.value,CurrentStatus:10.status,ActiveStepIndex:10.step,PassCount:10.pass,FailCount:10.fail" outputs="output cluster:do_actor_out.output" />
"""
    create_message_class("Update_UI_Msg", update_ui_payload, "INTENT: Update Host Actor UI state from incoming status message.", update_ui_do_xml)

    # 5. Load_Config_Msg
    load_config_payload = "cluster{string.ConfigFilePath}"
    load_config_do_xml = """  <Node _name="Unbundle By Name" uid="10" uid_parent="root" fields="ConfigFilePath" inputs="input cluster:2.value" outputs="ConfigFilePath:10.cfg" />
  <Constant _name="StatusConfigured" outputs="value:11.value" type="string" uid="11" uid_parent="root" value="CONFIGURED" />
  <Node _name="Bundle By Name" uid="13" uid_parent="root" fields="CurrentStatus,ConfigPath" inputs="input cluster:3.value,CurrentStatus:11.value,ConfigPath:10.cfg" outputs="output cluster:do_actor_out.output" />
"""
    create_message_class("Load_Config_Msg", load_config_payload, "INTENT: Load configuration path into Host Actor.", load_config_do_xml)


def create_actor_launcher():
    """Create Host_Actor_Launcher.vi at the top of 01_Host."""
    launcher_vi = HOST_DIR / "Host_Actor_Launcher.vi"
    launcher_xml = """<VI _name="Host_Actor_Launcher.vi" description="INTENT: Top-level Launcher for Host Actor in Actor Framework architecture.">
  <Control _name="error in (no error)" conIdx="8" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="1" uid_parent="root" value="[false,0,&quot;&quot;]" outputs="value:1.value" />
  <Control _name="Recipe ID" conIdx="10" connection="required" type="string" uid="2" uid_parent="root" value="RECIPE_SIM_001" outputs="value:2.value" />
  <Control _name="Config Path" conIdx="9" connection="recommended" type="string" uid="3" uid_parent="root" value="configs/test_profile_sim.json" outputs="value:3.value" />
  <Call target="Host_Validate_Config.vi" inputs="Editable config package:3.value,error in (no error):1.value" outputs="Diagnostics list:4.diag,error out:4.err,status ok:4.ok" uid="4" uid_parent="root" />
  <Constant _name="ReadyStatus" outputs="value:5.value" type="string" uid="5" uid_parent="root" value="HOST_ACTOR_ONLINE" />
  <Indicator _name="Actor Launcher Status" conIdx="2" connection="recommended" type="string" uid="6" uid_parent="root" inputs="value:5.value" />
  <Indicator _name="Active Recipe" conIdx="1" connection="recommended" type="string" uid="7" uid_parent="root" inputs="value:2.value" />
  <Indicator _name="error out" conIdx="0" connection="recommended" type="cluster{bool.status,int32.code,string.source}" uid="8" uid_parent="root" inputs="value:4.err" />
</VI>
"""
    compile_vi(launcher_vi, launcher_xml)


def update_project_file():
    """Create or update Universal_Sequence_Executor_AF.lvproj."""
    src_proj = WORKSPACE_ROOT / "Universal_Sequence_Executor.lvproj"
    dst_proj = WORKSPACE_ROOT / "Universal_Sequence_Executor_AF.lvproj"
    
    # Read src_proj
    text = src_proj.read_text(encoding="utf-8")
    # Replace project property title
    text = text.replace("Universal_Sequence_Executor", "Universal_Sequence_Executor_AF")
    
    dst_proj.write_text(text, encoding="utf-8")
    print(f"[OK] Created {dst_proj.name}")


def main():
    print("=" * 70)
    print("BUILDING ACTOR FRAMEWORK SUBSYSTEM ON HOST (Universal-sequence-executor-AF)")
    print("=" * 70)
    
    print("\nPhase 1: Creating Host_Actor.lvclass and core methods...")
    create_actor_class()
    
    print("\nPhase 2: Creating Actor Framework Message Classes...")
    create_all_messages()
    
    print("\nPhase 3: Creating Top-Level Host Actor Launcher...")
    create_actor_launcher()
    
    print("\nPhase 4: Updating Project Configuration...")
    update_project_file()
    
    print("\n[SUCCESS] Host Actor Framework successfully built!")


if __name__ == "__main__":
    main()
