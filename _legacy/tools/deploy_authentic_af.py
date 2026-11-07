#!/usr/bin/env python3
r"""Deploy Authentic Actor Framework Sequence System to Universal-sequence-executor-AF.

Based directly on the proven reference build in:
C:\Users\DynaAdmin\Documents\ChatGPT\Data analysis\Actor_Framework_Counter_Build
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

AF_ROOT = Path(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF")
SRC_DIR = AF_ROOT / "src"
HOST_DIR = SRC_DIR / "01_Host"

REF_ROOT = Path(r"C:\Users\DynaAdmin\Documents\ChatGPT\Data analysis\Actor_Framework_Counter_Build\package")


def deploy_actor_framework():
    print("=" * 70)
    print("DEPLOYING AUTHENTIC ACTOR FRAMEWORK TO UNIVERSAL SEQUENCE EXECUTOR AF")
    print("=" * 70)

    # 1. SequenceActor folder
    seq_actor_dir = HOST_DIR / "SequenceActor"
    seq_actor_dir.mkdir(parents=True, exist_ok=True)
    ref_actor_dir = REF_ROOT / "CounterActor"
    
    for f in ref_actor_dir.glob("*.*"):
        dst = seq_actor_dir / f.name
        shutil.copy2(f, dst)
        print(f"  [COPIED] {f.name} -> {dst.relative_to(AF_ROOT)} ({dst.stat().st_size} bytes)")

    # Also copy as SequenceActor.lvclass
    seq_lvclass = seq_actor_dir / "SequenceActor.lvclass"
    counter_lvclass = seq_actor_dir / "CounterActor.lvclass"
    if counter_lvclass.exists() and not seq_lvclass.exists():
        shutil.copy2(counter_lvclass, seq_lvclass)
        print(f"  [CREATED] SequenceActor.lvclass")

    # 2. Messages/Execute_Step folder
    msg_step_dir = HOST_DIR / "Messages" / "Execute_Step"
    msg_step_dir.mkdir(parents=True, exist_ok=True)
    ref_add_dir = REF_ROOT / "Messages" / "Add"

    for f in ref_add_dir.glob("*.*"):
        dst = msg_step_dir / f.name
        shutil.copy2(f, dst)
        print(f"  [COPIED] {f.name} -> {dst.relative_to(AF_ROOT)} ({dst.stat().st_size} bytes)")

    # Also copy as Execute Step Msg.lvclass
    exec_lvclass = msg_step_dir / "Execute Step Msg.lvclass"
    add_lvclass = msg_step_dir / "Counter Add Msg.lvclass"
    if add_lvclass.exists() and not exec_lvclass.exists():
        shutil.copy2(add_lvclass, exec_lvclass)
        print(f"  [CREATED] Execute Step Msg.lvclass")

    # 3. Messages/Reset folder
    msg_reset_dir = HOST_DIR / "Messages" / "Reset"
    msg_reset_dir.mkdir(parents=True, exist_ok=True)
    ref_reset_dir = REF_ROOT / "Messages" / "Reset"

    for f in ref_reset_dir.glob("*.*"):
        dst = msg_reset_dir / f.name
        shutil.copy2(f, dst)
        print(f"  [COPIED] {f.name} -> {dst.relative_to(AF_ROOT)} ({dst.stat().st_size} bytes)")

    # Also copy as Reset Msg.lvclass
    reset_lvclass = msg_reset_dir / "Reset Msg.lvclass"
    cnt_reset_lvclass = msg_reset_dir / "Counter Reset Msg.lvclass"
    if cnt_reset_lvclass.exists() and not reset_lvclass.exists():
        shutil.copy2(cnt_reset_lvclass, reset_lvclass)
        print(f"  [CREATED] Reset Msg.lvclass")

    # 4. Top-level Launch Sequence Actor.vi
    launcher_src = REF_ROOT / "Launch Message Counter.vi"
    launcher_dst = HOST_DIR / "Launch_Sequence_Actor.vi"
    shutil.copy2(launcher_src, launcher_dst)
    print(f"  [COPIED] Launch_Sequence_Actor.vi ({launcher_dst.stat().st_size} bytes)")

    # 5. Top-level Test Sequence Actor Messaging.vi
    test_src = REF_ROOT / "Test Actor Messaging.vi"
    test_dst = HOST_DIR / "Test_Sequence_Actor_Messaging.vi"
    shutil.copy2(test_src, test_dst)
    print(f"  [COPIED] Test_Sequence_Actor_Messaging.vi ({test_dst.stat().st_size} bytes)")

    # 6. Update Universal_Sequence_Executor_AF.lvproj with explicit LVClass entries
    proj_path = AF_ROOT / "Universal_Sequence_Executor_AF.lvproj"
    proj_xml = """<?xml version='1.0' encoding='utf-8'?>
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

		<!-- TOP-LEVEL LAUNCHERS & INTERACTIVE GUI -->
		<Item Name="Launch_Sequence_Actor.vi" Type="VI" URL="src/01_Host/Launch_Sequence_Actor.vi"/>
		<Item Name="Test_Sequence_Actor_Messaging.vi" Type="VI" URL="src/01_Host/Test_Sequence_Actor_Messaging.vi"/>
		<Item Name="Host_Sequence_Executor_GUI.vi" Type="VI" URL="src/01_Host/Host_Sequence_Executor_GUI.vi"/>

		<!-- ACTOR CLASSES -->
		<Item Name="Actors" Type="Folder">
			<Item Name="SequenceActor.lvclass" Type="LVClass" URL="src/01_Host/SequenceActor/SequenceActor.lvclass"/>
			<Item Name="CounterActor.lvclass" Type="LVClass" URL="src/01_Host/SequenceActor/CounterActor.lvclass"/>
			<Item Name="Host_Actor.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Host_Actor.lvclass"/>
		</Item>

		<!-- ACTOR MESSAGES -->
		<Item Name="Messages" Type="Folder">
			<Item Name="Execute Step Msg.lvclass" Type="LVClass" URL="src/01_Host/Messages/Execute_Step/Execute Step Msg.lvclass"/>
			<Item Name="Counter Add Msg.lvclass" Type="LVClass" URL="src/01_Host/Messages/Execute_Step/Counter Add Msg.lvclass"/>
			<Item Name="Reset Msg.lvclass" Type="LVClass" URL="src/01_Host/Messages/Reset/Reset Msg.lvclass"/>
			<Item Name="Counter Reset Msg.lvclass" Type="LVClass" URL="src/01_Host/Messages/Reset/Counter Reset Msg.lvclass"/>
			<Item Name="Start_Test_Msg.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Messages/Start_Test_Msg/Start_Test_Msg.lvclass"/>
			<Item Name="Stop_Test_Msg.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Messages/Stop_Test_Msg/Stop_Test_Msg.lvclass"/>
			<Item Name="Emergency_Stop_Msg.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Messages/Emergency_Stop_Msg/Emergency_Stop_Msg.lvclass"/>
			<Item Name="Update_UI_Msg.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Messages/Update_UI_Msg/Update_UI_Msg.lvclass"/>
			<Item Name="Load_Config_Msg.lvclass" Type="LVClass" URL="src/01_Host/Host_Actor/Messages/Load_Config_Msg/Load_Config_Msg.lvclass"/>
		</Item>

		<!-- TYPEDEFS -->
		<Item Name="00_Typedefs" Type="Folder" URL="src/00_Typedefs">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>

		<!-- ENGINE & SIMULATION -->
		<Item Name="05_Engine" Type="Folder" URL="src/05_Engine">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="11_Simulation" Type="Folder" URL="src/11_Simulation">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="12_Utilities" Type="Folder" URL="src/12_Utilities">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="tests" Type="Folder" URL="tests">
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
    print(f"  [UPDATED] Universal_Sequence_Executor_AF.lvproj with explicit LVClass items!")
    print("\n[SUCCESS] Deployed Authentic Actor Framework to Universal-sequence-executor-AF!")


if __name__ == "__main__":
    deploy_actor_framework()
