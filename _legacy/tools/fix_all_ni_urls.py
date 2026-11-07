import os

# Update Universal_Sequence_Executor_AF.lvproj
af_proj = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor_AF.lvproj"
af_xml = '''<?xml version='1.0' encoding='utf-8'?>
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
		<Item Name="Launch Message Counter.vi" Type="VI" URL="../Launch Message Counter.vi"/>
		<Item Name="Test Actor Messaging.vi" Type="VI" URL="../Test Actor Messaging.vi"/>

		<!-- ACTOR CLASSES -->
		<Item Name="Actors" Type="Folder">
			<Item Name="CounterActor.lvclass" Type="LVClass" URL="../CounterActor/CounterActor.lvclass"/>
		</Item>

		<!-- ACTOR MESSAGES -->
		<Item Name="Messages" Type="Folder">
			<Item Name="Counter Add Msg.lvclass" Type="LVClass" URL="../Messages/Add/Counter Add Msg.lvclass"/>
			<Item Name="Counter Reset Msg.lvclass" Type="LVClass" URL="../Messages/Reset/Counter Reset Msg.lvclass"/>
		</Item>

		<!-- ENGINE & SIMULATION -->
		<Item Name="00_Typedefs" Type="Folder" URL="../src/00_Typedefs">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
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
'''
with open(af_proj, "w", encoding="utf-8") as f:
    f.write(af_xml)
print("Updated AF project with standard NI relative paths (../).")

# Update Universal_Sequence_Executor.lvproj (QMH)
qmh_proj = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor\Universal_Sequence_Executor.lvproj"
with open(qmh_proj, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure all disk folders start with ../
import re
fixed_qmh = re.sub(r'URL="src/', 'URL="../src/', content)
fixed_qmh = re.sub(r'URL="tests"', 'URL="../tests"', fixed_qmh)
# Avoid double ../
fixed_qmh = fixed_qmh.replace('../../../', '../').replace('../../', '../')
with open(qmh_proj, "w", encoding="utf-8") as f:
    f.write(fixed_qmh)
print("Updated QMH project with standard NI relative paths (../).")
