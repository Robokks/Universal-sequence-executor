import os
import shutil
import xml.etree.ElementTree as ET

src_ref = r"D:\Karthikeyan\DEVELOPMENT\Data Analyser\Actor Framework Counter"
af_root = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF"

print("1. Copying pristine CounterActor...")
dst_actor = os.path.join(af_root, "CounterActor")
if os.path.exists(dst_actor):
    shutil.rmtree(dst_actor)
shutil.copytree(os.path.join(src_ref, "CounterActor"), dst_actor)

print("2. Copying pristine Messages...")
dst_messages = os.path.join(af_root, "Messages")
if os.path.exists(dst_messages):
    shutil.rmtree(dst_messages)
shutil.copytree(os.path.join(src_ref, "Messages"), dst_messages)

print("3. Copying pristine Launchers...")
for f in ["Launch Message Counter.vi", "Test Actor Messaging.vi"]:
    shutil.copy2(os.path.join(src_ref, f), os.path.join(af_root, f))

print("4. Cleaning up corrupted fake classes in src/01_Host...")
host_dir = os.path.join(af_root, "src", "01_Host")
for bogus in ["SequenceActor", "Sequence_Actor", "Host_Actor", "Messages"]:
    p = os.path.join(host_dir, bogus)
    if os.path.exists(p):
        shutil.rmtree(p)
        print("Removed corrupted:", p)

# Also remove any loose copies from 01_Host
for f in ["Add.vi", "Configure.vi", "Reset.vi", "Stop Core.vi", "Launch_Sequence_Actor.vi", "Test_Sequence_Actor_Messaging.vi"]:
    p = os.path.join(host_dir, f)
    if os.path.exists(p):
        os.remove(p)
        print("Removed loose:", p)

print("5. Rewriting Universal_Sequence_Executor_AF.lvproj to reference pristine AF components...")
proj_path = os.path.join(af_root, "Universal_Sequence_Executor_AF.lvproj")
proj_xml = '''<?xml version='1.0' encoding='utf-8'?>
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

		<!-- TOP-LEVEL LAUNCHERS -->
		<Item Name="Launch Message Counter.vi" Type="VI" URL="Launch Message Counter.vi"/>
		<Item Name="Test Actor Messaging.vi" Type="VI" URL="Test Actor Messaging.vi"/>

		<!-- ACTOR CLASSES -->
		<Item Name="Actors" Type="Folder">
			<Item Name="CounterActor.lvclass" Type="LVClass" URL="CounterActor/CounterActor.lvclass"/>
		</Item>

		<!-- ACTOR MESSAGES -->
		<Item Name="Messages" Type="Folder">
			<Item Name="Counter Add Msg.lvclass" Type="LVClass" URL="Messages/Add/Counter Add Msg.lvclass"/>
			<Item Name="Counter Reset Msg.lvclass" Type="LVClass" URL="Messages/Reset/Counter Reset Msg.lvclass"/>
		</Item>

		<!-- ENGINE & SIMULATION -->
		<Item Name="00_Typedefs" Type="Folder" URL="src/00_Typedefs">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
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
'''
with open(proj_path, "w", encoding="utf-8") as f:
    f.write(proj_xml)

print("Deploy pristine AF completed successfully!")
