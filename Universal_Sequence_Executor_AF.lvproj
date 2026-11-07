<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="26008000">
	<Property Name="NI.LV.All.SaveVersion" Type="Str">26.0</Property>
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Property Name="NI.Project.Description" Type="Str"></Property>
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
		<Item Name="12_Utilities" Type="Folder" URL="../src/12_Utilities">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="Logic" Type="Folder" URL="../src/Logic">
			<Property Name="NI.DISK" Type="Bool">true</Property>
		</Item>
		<Item Name="Plugins" Type="Folder">
			<Item Name="VTU Sim Rig.lvclass" Type="LVClass" URL="../plugins/VTU Sim Rig/VTU Sim Rig.lvclass"/>
		</Item>
		<Item Name="Samples" Type="Folder">
			<Item Name="Counter Add Msg.lvclass" Type="LVClass" URL="../Messages/Add/Counter Add Msg.lvclass"/>
			<Item Name="Counter Reset Msg.lvclass" Type="LVClass" URL="../Messages/Reset/Counter Reset Msg.lvclass"/>
			<Item Name="CounterActor.lvclass" Type="LVClass" URL="../CounterActor/CounterActor.lvclass"/>
			<Item Name="Launch Message Counter.vi" Type="VI" URL="../Launch Message Counter.vi"/>
			<Item Name="Test Actor Messaging.vi" Type="VI" URL="../Test Actor Messaging.vi"/>
		</Item>
		<Item Name="Typedefs" Type="Folder">
			<Item Name="Channel Definition.ctl" Type="VI" URL="../src/Typedefs/Channel Definition.ctl"/>
			<Item Name="Channel Feedback.ctl" Type="VI" URL="../src/Typedefs/Channel Feedback.ctl"/>
			<Item Name="Channel Value.ctl" Type="VI" URL="../src/Typedefs/Channel Value.ctl"/>
			<Item Name="Condition.ctl" Type="VI" URL="../src/Typedefs/Condition.ctl"/>
			<Item Name="Rig Config.ctl" Type="VI" URL="../src/Typedefs/Rig Config.ctl"/>
			<Item Name="Sequence File.ctl" Type="VI" URL="../src/Typedefs/Sequence File.ctl"/>
			<Item Name="Step Config.ctl" Type="VI" URL="../src/Typedefs/Step Config.ctl"/>
			<Item Name="Step Phase.ctl" Type="VI" URL="../src/Typedefs/Step Phase.ctl"/>
			<Item Name="Step Result.ctl" Type="VI" URL="../src/Typedefs/Step Result.ctl"/>
		</Item>
		<Item Name="Rig.lvclass" Type="LVClass" URL="../src/Rig/Rig.lvclass"/>
		<Item Name="Sequence Executor.lvclass" Type="LVClass" URL="../src/Executor/Sequence Executor.lvclass"/>
		<Item Name="Test Select Monitored Signal A.vi" Type="VI" URL="../tests/caraya/Test Select Monitored Signal A.vi"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
