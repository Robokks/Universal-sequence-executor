# 08 — VI-Level Test Coverage Backlog

> **Draft implementation design V0.3 (2026-11-05)**. Based on SRS/SDD/SDP V0.2. These are proposed names and connector patterns, **not existing native `.vi` binaries**. Ratings, timing budgets, approved pressure/motion limits and protective responses require the responsible controls/safety engineers' sign-off. This package contains no executable rig-control logic.


The 82 designed test cases exercise the most critical behaviors, but they **do not individually cover every one** of the 123 proposed VIs. This list identifies VIs **not explicitly named** in an existing test case and for which a focused positive-path, invalid-input and error-path test should be designed before the corresponding implementation is merged. A VI referenced in a test can still need more direct test coverage.

| Area | VI | Minimum tests to author |
|---|---|---|
| 01_Host/01_Application | Host_Main.vi | Normal operation; Never call device controls from UI; report transport initialization errors. |
| 01_Host/01_Application | Host_Event_Loop.vi | Normal operation; UI never blocks on network response. |
| 01_Host/01_Application | Host_Message_Loop.vi | Normal operation; Bad message produces rejection event, not silent default. |
| 01_Host/01_Application | Host_State_Update.vi | Normal operation; Ignore late events for older run identities. |
| 01_Host/01_Application | Host_Close.vi | Normal operation; Host exit triggers RT watchdog on communication loss if active. |
| 01_Host/02_Editor | Rig_Editor.vi | Normal operation; Do not permit operator edit of protective limits. |
| 01_Host/02_Editor | Test_Editor.vi | Normal operation; Reject missing fault/shutdown definitions. |
| 01_Host/02_Editor | Group_Editor.vi | Normal operation; Reject unbounded loops and invalid joins. |
| 01_Host/02_Editor | Step_Editor.vi | Normal operation; Prevent unsupported action/controller combination. |
| 01_Host/02_Editor | Profile_Editor.vi | Normal operation; Flag incompatible or unsafe points before publication. |
| 01_Host/02_Editor | Condition_Editor.vi | Normal operation; Reject type mismatches and missing references. |
| 01_Host/02_Editor | Plugin_Editor.vi | Normal operation; Reject unregistered or target-incompatible plugins. |
| 01_Host/02_Editor | Host_Validate_Config.vi | Normal operation; Host validation is not a substitute for target validation. |
| 01_Host/02_Editor | Host_Publish_Config.vi | Normal operation; Never hot-swap active test snapshot. |
| 01_Host/03_Operations | Host_Runtime_Monitor.vi | Normal operation; Do not use polling of hardware via UI loop for safety logic. |
| 01_Host/03_Operations | Host_Manual_Control.vi | Normal operation; No direct VFD/PRV/servo writes from Host UI. |
| 01_Host/03_Operations | Host_Report_Viewer.vi | Normal operation; Missing data must display explicit capture failure. |
| 02_Transport | Transport_Init.vi | Normal operation; Validate protocol version and connection state. |
| 02_Transport | Transport_Send_Command.vi | Normal operation; Distinguish transport success from applied command. |
| 02_Transport | Transport_Receive_Command.vi | Normal operation; Never block the entire Host loop indefinitely. |
| 02_Transport | Transport_Send_Event.vi | Normal operation; Record local events if remote channel unavailable. |
| 02_Transport | Transport_Receive_Event.vi | Normal operation; Old run events not applied to new run. |
| 02_Transport | Transport_Close.vi | Normal operation; Loss of network cannot prevent RT protective behavior. |
| 03_Config | Config_Get_Active.vi | Normal operation; Return explicit not-found status. |
| 04_Runtime_Supervisor | Target_Main.vi | Normal operation; Fault supervisor must run independently of normal engine. |
| 04_Runtime_Supervisor | Runtime_Initialize.vi | Normal operation; On partial init failure unwind acquired resources. |
| 04_Runtime_Supervisor | Supervisor_Loop.vi | Normal operation; Avoid calling any blocking action/plugin directly. |
| 04_Runtime_Supervisor | Supervisor_Start_Test.vi | Normal operation; Fail closed if target not ready. |
| 04_Runtime_Supervisor | Supervisor_Stop_Test.vi | Normal operation; Cannot assume blocked plugin will finish. |
| 04_Runtime_Supervisor | Supervisor_Finalize_Run.vi | Normal operation; Log failures do not reopen normal control. |
| 04_Runtime_Supervisor | Runtime_Close.vi | Normal operation; Never turn off protection to make app exit faster. |
| 05_Engine | Executor_Loop.vi | Normal operation; Fault/stop events bypass ordinary backlogged work. |
| 05_Engine | Executor_Begin_Group.vi | Normal operation; Reject invalid nested depth. |
| 05_Engine | Scheduler_Claim_Resources.vi | Normal operation; A step cannot partially own incompatible resource set. |
| 05_Engine | Step_Begin.vi | Normal operation; Reject start if run already faulted. |
| 05_Engine | Step_Enter_Phase.vi | Normal operation; Prevent repeated command sends on every scheduler tick. |
| 05_Engine | Step_Cancel.vi | Normal operation; Cancellation must not wait for physical motion to finish. |
| 05_Engine | Profile_Get_Next_Point.vi | Normal operation; Do not use implicit default mode after relief point. |
| 05_Engine | Condition_Evaluate.vi | Normal operation; UNKNOWN never implies pass. |
| 05_Engine | Popup_Begin.vi | Normal operation; Host unavailable triggers configured shutdown policy. |
| 06_Bridge | Bridge_Read_Status.vi | Normal operation; Snapshots are advisory, not source of safety decisions. |
| 07_Parameter_Registry | Registry_Init.vi | Normal operation; Uninitialized measurements remain invalid. |
| 07_Parameter_Registry | Registry_Resolve.vi | Normal operation; No silent fallback to index 0. |
| 07_Parameter_Registry | Registry_Stale_Scan.vi | Normal operation; Stale values must never satisfy success condition. |
| 08_RT_Functions | RT_Main.vi | Normal operation; If control service fails do not mark ready. |
| 08_RT_Functions | RT_IO_Acquisition_Loop.vi | Normal operation; Reject broken wire/out-of-range/communication fault by sensor policy. |
| 08_RT_Functions | RT_VFD_Adapter.vi | Normal operation; Drive fault prevents new normal command. |
| 08_RT_Functions | RT_PRV_AO_Adapter.vi | Normal operation; AO fail safe depends on rig wiring and valve behavior. |
| 08_RT_Functions | RT_Servo_IO_Adapter.vi | Normal operation; Check actual direction and enable/interlock before motion. |
| 08_RT_Functions | RT_Actuator_Adapter.vi | Normal operation; Reject unsupported actuator modes. |
| 08_RT_Functions | RT_PROFINET_Adapter.vi | Normal operation; Hardware/firmware capability must be verified separately. |
| 08_RT_Functions | RT_Status_Publish.vi | Normal operation; Slow reporting must not stall PID loop. |
| 08_RT_Functions | RT_Close.vi | Normal operation; Independent hardware protection remains functional. |
| 09_Plugins | Plugin_Worker_Template.vi | Normal operation; Template must never write hardware directly. |
| 09_Plugins | VTU_Reference_Load_Calc.vi | Normal operation; Reject unavailable earlier measurement. |
| 10_Logging | Capture_Start.vi | Normal operation; Reject impossible buffer size or unavailable signal. |
| 11_Simulation | Sim_Main.vi | Normal operation; Physical adapters must be disabled in simulation. |
| 11_Simulation | Sim_IO_Adapter.vi | Normal operation; Clearly label every simulation record. |
| 11_Simulation | Sim_VTU_Plant.vi | Normal operation; Simulation is not equipment design evidence. |
| 11_Simulation | Sim_Fault_Injection.vi | Normal operation; Safety hardware tests require actual qualified test procedures. |
| 11_Simulation | Sim_Clock.vi | Normal operation; Never substitute virtual clock for deployed RT timing. |

For all controller and fault-related VIs, add separately reviewed HIL / timing tests; do not treat host-simulator unit tests as proof of safe physical operation.