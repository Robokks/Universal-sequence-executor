# 02 — Complete VI Catalog

> **Draft implementation design V0.3 (2026-11-05)**. Based on SRS/SDD/SDP V0.2. These are proposed names and connector patterns, **not existing native `.vi` binaries**. Ratings, timing budgets, approved pressure/motion limits and protective responses require the responsible controls/safety engineers' sign-off. This package contains no executable rig-control logic.


Every VI below is a **proposed source VI**. For every entry: **Inputs**, **Outputs**, **Block-diagram behavior**, **LabVIEW blocks/functions**, and **error/failure handling** are specified. All VIs share the type/connector rules in document 01. This is a design catalog, not a claim the VI binary exists.


## 01_Host/01_Application — 5 VIs

### `Host_Main.vi`
**Purpose:** Host process entry and service owner.

**Connector inputs:** Startup config, application path.

**Connector outputs:** Stop status, error cluster.

**Block-diagram logic:** Initialize transport, Host queues and HMI; launch MHL workers; on exit request coordinated stop and close queues..

**Functions / blocks to use:** While Loop, Event Structure, Obtain Queue, Enqueue Element, error cluster.

**Failure handling:** Never call device controls from UI; report transport initialization errors..

### `Host_Event_Loop.vi`
**Purpose:** Convert front panel actions into requests.

**Connector inputs:** UI references, event loop queue.

**Connector outputs:** Host messages.

**Block-diagram logic:** Handle Start/Stop/Manual/ACK button Value Change events; enqueue typed requests only; handle Panel Close..

**Functions / blocks to use:** Event Structure, Enqueue Element, Timeout case.

**Failure handling:** UI never blocks on network response..

### `Host_Message_Loop.vi`
**Purpose:** Handle Host application commands.

**Connector inputs:** HostMessage.ctl queue, app-state shift register.

**Connector outputs:** HMI updates, transport requests.

**Block-diagram logic:** Dequeue commands and dispatch by enum; update Host state and send commands to selected target..

**Functions / blocks to use:** Dequeue Element, Case Structure, shift registers.

**Failure handling:** Bad message produces rejection event, not silent default..

### `Host_State_Update.vi`
**Purpose:** Build consistent HMI view model.

**Connector inputs:** Incoming runtime event, existing Host state.

**Connector outputs:** New Host state.

**Block-diagram logic:** Match run ID and event sequence; update status, active step, progress and operator notices..

**Functions / blocks to use:** Case Structure, Bundle by Name, Comparison.

**Failure handling:** Ignore late events for older run identities..

### `Host_Close.vi`
**Purpose:** Stop Host services.

**Connector inputs:** Host refs, close policy.

**Connector outputs:** Error/status.

**Block-diagram logic:** Stop UI senders, close connections, drain mandatory audit events and release references..

**Functions / blocks to use:** Enqueue Element, Release Queue, Close Reference.

**Failure handling:** Host exit triggers RT watchdog on communication loss if active..


## 01_Host/02_Editor — 9 VIs

### `Rig_Editor.vi`
**Purpose:** Define rig resource and I/O capabilities.

**Connector inputs:** RigDefinition, resource metadata.

**Connector outputs:** Updated RigDefinition.

**Block-diagram logic:** Show editable rig fields and parameter mappings; validate identifiers and protected limit permissions..

**Functions / blocks to use:** Event Structure, Table, Array controls, Bundle by Name.

**Failure handling:** Do not permit operator edit of protective limits..

### `Test_Editor.vi`
**Purpose:** Define tests and attached procedures.

**Connector inputs:** TestDefinition, list of groups.

**Connector outputs:** Updated TestDefinition.

**Block-diagram logic:** Edit prerequisite tests, repeat count, selected fault and shutdown sequence IDs, result rules..

**Functions / blocks to use:** Event Structure, Listbox, Cluster controls.

**Failure handling:** Reject missing fault/shutdown definitions..

### `Group_Editor.vi`
**Purpose:** Define sequential and parallel groups.

**Connector inputs:** GroupDefinition, actions.

**Connector outputs:** Updated group tree.

**Block-diagram logic:** Create child list, cycles, join policy and resource declarations; show conflicts..

**Functions / blocks to use:** Tree control, Array, Case Structure.

**Failure handling:** Reject unbounded loops and invalid joins..

### `Step_Editor.vi`
**Purpose:** Edit action parameters.

**Connector inputs:** ActionDefinition, parameter registry.

**Connector outputs:** Updated action.

**Block-diagram logic:** Select action type, commands, deadlines, feedback/timeout/retry/capture configuration; validate units..

**Functions / blocks to use:** Ring/Enum controls, clusters, Event Structure.

**Failure handling:** Prevent unsupported action/controller combination..

### `Profile_Editor.vi`
**Purpose:** Edit sweeps and operating points.

**Connector inputs:** ProfileDefinition, rig envelope.

**Connector outputs:** Updated profile.

**Block-diagram logic:** Edit pressure/flow-only/combined points, ramps, controller modes, dwell and capture per point..

**Functions / blocks to use:** Multicolumn Listbox/Table, clusters.

**Failure handling:** Flag incompatible or unsafe points before publication..

### `Condition_Editor.vi`
**Purpose:** Build AND/OR expression trees.

**Connector inputs:** ConditionNode tree, parameter definitions.

**Connector outputs:** Validated tree.

**Block-diagram logic:** Build nested operators and compare nodes; show units, quality behavior, reference source..

**Functions / blocks to use:** Tree control, Case Structure, recursion helper.

**Failure handling:** Reject type mismatches and missing references..

### `Plugin_Editor.vi`
**Purpose:** Register supported custom VIs.

**Connector inputs:** PluginManifest, target inventory.

**Connector outputs:** Selected plugin definitions.

**Block-diagram logic:** Show plugin ID/version, target support, arguments, outputs, resource requirements and cancellation policy..

**Functions / blocks to use:** Listbox, clusters, File Path controls.

**Failure handling:** Reject unregistered or target-incompatible plugins..

### `Host_Validate_Config.vi`
**Purpose:** Run initial editing checks.

**Connector inputs:** Editable config package.

**Connector outputs:** Diagnostics list.

**Block-diagram logic:** Call structural, semantic and plugin validation locally before publish; show precise path to failures..

**Functions / blocks to use:** For Loop, subVI calls, Build Array.

**Failure handling:** Host validation is not a substitute for target validation..

### `Host_Publish_Config.vi`
**Purpose:** Publish a fixed configuration revision.

**Connector inputs:** Validated config, version, target ID.

**Connector outputs:** Publish receipt.

**Block-diagram logic:** Serialize signed/hashed revision as approved by project policy; transfer, await target validation and acknowledgement..

**Functions / blocks to use:** Config encode subVI, transport send, timeout wait.

**Failure handling:** Never hot-swap active test snapshot..


## 01_Host/03_Operations — 4 VIs

### `Host_Runtime_Monitor.vi`
**Purpose:** Display current execution.

**Connector inputs:** Incoming status/events, run identity.

**Connector outputs:** HMI indicators.

**Block-diagram logic:** Update state, current group, active steps, cycle counts and fault details from event messages..

**Functions / blocks to use:** Event Structure, cluster indicators, charts.

**Failure handling:** Do not use polling of hardware via UI loop for safety logic..

### `Host_Popup_Manager.vi`
**Purpose:** Show operator instructions and ACK.

**Connector inputs:** PopupRequest, run and request IDs.

**Connector outputs:** PopupAck, cancellation.

**Block-diagram logic:** Display requested text, elapsed-time feedback and options; send ACK only for active request; close on stop/fault..

**Functions / blocks to use:** Dialog VI, Event Structure, Tick Count.

**Failure handling:** Stale ACK must be ignored by target..

### `Host_Manual_Control.vi`
**Purpose:** Request manual commands via Bridge.

**Connector inputs:** Mode status, desired setpoint.

**Connector outputs:** CommandRequest.

**Block-diagram logic:** Require confirmed idle/manual state; submit typed command and show ACK/result..

**Functions / blocks to use:** Numeric controls, Enqueue Element, Case Structure.

**Failure handling:** No direct VFD/PRV/servo writes from Host UI..

### `Host_Report_Viewer.vi`
**Purpose:** Browse completed report records.

**Connector inputs:** Run ID, report path/index.

**Connector outputs:** Rendered report summary.

**Block-diagram logic:** Filter run/step/cycle results and export copies; never modify source records..

**Functions / blocks to use:** File I/O, Table, waveform graph.

**Failure handling:** Missing data must display explicit capture failure..


## 02_Transport — 8 VIs

### `Transport_Init.vi`
**Purpose:** Construct Host/target communication channels.

**Connector inputs:** Connection configuration, target endpoint.

**Connector outputs:** Transport references and status.

**Block-diagram logic:** Open command-down, reply-up, event-up and heartbeat channels according to deployment profile..

**Functions / blocks to use:** Network Stream Create Reader/Writer endpoints or TCP VIs.

**Failure handling:** Validate protocol version and connection state..

### `Transport_Send_Command.vi`
**Purpose:** Send command/config/ACK requests.

**Connector inputs:** Typed RuntimeMessage, transport ref.

**Connector outputs:** Send result.

**Block-diagram logic:** Serialize envelope with message ID/run ID and finite send deadline; record send attempts..

**Functions / blocks to use:** Flatten To String/JSON adapter, Network Stream Write/TCP Write.

**Failure handling:** Distinguish transport success from applied command..

### `Transport_Receive_Command.vi`
**Purpose:** Consume incoming target requests.

**Connector inputs:** Transport ref, shutdown token.

**Connector outputs:** RuntimeMessage.

**Block-diagram logic:** Read with bounded timeout; decode and validate envelope; reject malformed messages..

**Functions / blocks to use:** Network Stream Read/TCP Read, Case Structure.

**Failure handling:** Never block the entire Host loop indefinitely..

### `Transport_Send_Event.vi`
**Purpose:** Publish event/status to Host.

**Connector inputs:** EventRecord, transport ref.

**Connector outputs:** Delivery status.

**Block-diagram logic:** Serialize event with monotonically increasing event sequence; send on event channel..

**Functions / blocks to use:** Network Stream Write, Error Cluster.

**Failure handling:** Record local events if remote channel unavailable..

### `Transport_Receive_Event.vi`
**Purpose:** Receive event/status streams.

**Connector inputs:** Transport ref, run version.

**Connector outputs:** EventRecord.

**Block-diagram logic:** Receive and validate event ordering, detect duplicates, forward to Host state updater..

**Functions / blocks to use:** Network Stream Read, Enqueue Element.

**Failure handling:** Old run events not applied to new run..

### `Transport_Heartbeat.vi`
**Purpose:** Maintain connectivity health.

**Connector inputs:** Link status, monotonic clock.

**Connector outputs:** Heartbeat events.

**Block-diagram logic:** Transmit and monitor heartbeat sequence independently of operator prompts..

**Functions / blocks to use:** Timed supervisory loop, elapsed time VIs.

**Failure handling:** Missing heartbeat triggers RT supervision, not UI-only error..

### `Transport_Reconnect.vi`
**Purpose:** Recover non-running communication session.

**Connector inputs:** Channel refs, reconnection policy.

**Connector outputs:** New connection or failure.

**Block-diagram logic:** Tear down broken refs, negotiate capabilities, reconcile run identity and report outstanding status..

**Functions / blocks to use:** Close Reference, transport init subVI, Case Structure.

**Failure handling:** Reconnect never silently resumes an interrupted test..

### `Transport_Close.vi`
**Purpose:** Release endpoints.

**Connector inputs:** Channel references.

**Connector outputs:** Final status.

**Block-diagram logic:** Signal close, release endpoints and flush bounded essential messages where possible..

**Functions / blocks to use:** Destroy/Close endpoint VIs, error merge.

**Failure handling:** Loss of network cannot prevent RT protective behavior..


## 03_Config — 7 VIs

### `Config_File_Read_Block.vi`
**Purpose:** Read locally stored package.

**Connector inputs:** Local package path.

**Connector outputs:** Raw bytes, read status.

**Block-diagram logic:** Check path, read complete content, check size limits before decoding..

**Functions / blocks to use:** Check if File Exists, Read from Binary File, Close File.

**Failure handling:** Reject truncated/inaccessible file..

### `Config_Decode.vi`
**Purpose:** Decode versioned configuration.

**Connector inputs:** Raw package bytes.

**Connector outputs:** RigDefinition, TestDefinition and manifest.

**Block-diagram logic:** Parse schema version, materialize typed arrays/clusters, reject unknown required fields..

**Functions / blocks to use:** Unflatten From String/JSON parser adapter, Type Cast only if format supports.

**Failure handling:** Never execute partially decoded config..

### `Config_Validate_Target.vi`
**Purpose:** Enforce target-specific validation.

**Connector inputs:** Decoded config, deployed capabilities.

**Connector outputs:** Diagnostics and validity flag.

**Block-diagram logic:** Check IDs, units, bounds, cyclic depth, resources, plugin manifests, device capabilities and controller modes..

**Functions / blocks to use:** For Loop, Search 1D Array, Comparison, subVIs.

**Failure handling:** Reject nonterminating and invalid definitions..

### `Config_Compile_Plan.vi`
**Purpose:** Preprocess definitions for executor.

**Connector inputs:** Validated test/group/action tree.

**Connector outputs:** Immutable ExecutionPlan.

**Block-diagram logic:** Resolve references and plugins, precompute resource requirements, stable action indexes and branch joins..

**Functions / blocks to use:** For Loop, Build Array, Lookup helpers.

**Failure handling:** Abort compile on dangling references or resource conflict..

### `Config_Activate_Snapshot.vi`
**Purpose:** Fix active configuration for run.

**Connector inputs:** Approved ExecutionPlan, current mode.

**Connector outputs:** Active snapshot ID/handle.

**Block-diagram logic:** Atomically switch only while idle/ready; record content hash and revision in run record..

**Functions / blocks to use:** Case Structure, shift registers, file rename strategy.

**Failure handling:** Never modify running snapshot..

### `Config_Get_Active.vi`
**Purpose:** Return read-only run configuration.

**Connector inputs:** Snapshot handle, requested ID.

**Connector outputs:** Typed definition/result.

**Block-diagram logic:** Retrieve by identifier without exposing writeable storage..

**Functions / blocks to use:** Index Array, search helper.

**Failure handling:** Return explicit not-found status..

### `Config_Resolve_Plugins.vi`
**Purpose:** Check plugin package availability.

**Connector inputs:** Manifest list, deployment index.

**Connector outputs:** Resolved plugin registry.

**Block-diagram logic:** Match plugin ID/version, target, connector signature and resource permissions..

**Functions / blocks to use:** For Loop, Search 1D Array, Compare.

**Failure handling:** Reject missing plugin before test start..


## 04_Runtime_Supervisor — 12 VIs

### `Target_Main.vi`
**Purpose:** Start execution-target services.

**Connector inputs:** Local paths, hardware/transport profile.

**Connector outputs:** Shutdown/status.

**Block-diagram logic:** Boot in disabled/safe state; initialize local services in dependency order; launch supervisor and service loops; run until coordinated close..

**Functions / blocks to use:** Error handling, While Loop, queue initiation.

**Failure handling:** Fault supervisor must run independently of normal engine..

### `Runtime_Initialize.vi`
**Purpose:** Prepare registries/queues/loggers.

**Connector inputs:** Target capability, configuration locations.

**Connector outputs:** Service references.

**Block-diagram logic:** Create bounded message queues, event log, registry, Bridge, RT gateway and simulator selection..

**Functions / blocks to use:** Obtain Queue, Initialize Array, subVIs.

**Failure handling:** On partial init failure unwind acquired resources..

### `Supervisor_Loop.vi`
**Purpose:** Single owner of run lifecycle.

**Connector inputs:** Supervisor message queue, RunContext.

**Connector outputs:** State transitions/events.

**Block-diagram logic:** Dequeue messages, prioritize fault and stop signals, call state handler, tick watchdog checks..

**Functions / blocks to use:** While Loop, Dequeue Element with timeout, Case Structure, shift register.

**Failure handling:** Avoid calling any blocking action/plugin directly..

### `Supervisor_Handle_Event.vi`
**Purpose:** Apply legal state transitions.

**Connector inputs:** Current run state, RuntimeMessage.

**Connector outputs:** Updated state and effects.

**Block-diagram logic:** Enforce Idle→Validating→Ready→Running and stop/fault/shutdown path; reject illegal transitions..

**Functions / blocks to use:** Case Structure, Bundle by Name.

**Failure handling:** Emit traceable rejection for invalid transition..

### `Supervisor_Set_Mode.vi`
**Purpose:** Enforce Manual/Auto separation.

**Connector inputs:** Requested mode, current state, Bridge lease state.

**Connector outputs:** Accepted mode or rejection.

**Block-diagram logic:** Change only from stopped/idle safe state with no outstanding leases..

**Functions / blocks to use:** Case Structure, Comparison, Bridge query.

**Failure handling:** No live manual takeover of auto commands..

### `Supervisor_Start_Test.vi`
**Purpose:** Establish a new test run.

**Connector inputs:** Approved plan, readiness, user authority.

**Connector outputs:** RunContext/run ID.

**Block-diagram logic:** Check interlocks, acquire test ownership token, initialize counters/logging; authorize scheduler..

**Functions / blocks to use:** Get Date/Time, Generate ID helper, Bundle cluster.

**Failure handling:** Fail closed if target not ready..

### `Supervisor_Stop_Test.vi`
**Purpose:** Execute operator stop policy.

**Connector inputs:** Active RunContext, Stop reason.

**Connector outputs:** Stopping state.

**Block-diagram logic:** Prevent new normal steps, request cooperative cancellation, revoke leases, run safe shutdown when permitted..

**Functions / blocks to use:** Enqueue high-priority stop, state handler.

**Failure handling:** Cannot assume blocked plugin will finish..

### `Supervisor_Enter_Fault.vi`
**Purpose:** Latch global fault and preempt.

**Connector inputs:** FaultRecord, RunContext.

**Connector outputs:** Faulting event and preemption request.

**Block-diagram logic:** Latch fault; invalidate all normal owners; cancel all parallel branches; activate protective path first..

**Functions / blocks to use:** Case Structure, dedicated fault signal, Bridge preempt subVI.

**Failure handling:** Fault cannot depend on normal queue being empty..

### `Supervisor_Fault_Procedure.vi`
**Purpose:** Execute exactly one test-specific fault sequence.

**Connector inputs:** TestDefinition, fault cause, protective readiness.

**Connector outputs:** Procedure outcome.

**Block-diagram logic:** Validate permissive safe state, run bounded designated fault sequence, monitor separately; otherwise fallback..

**Functions / blocks to use:** Sequence interpreter with restricted actions, timeout, Case Structure.

**Failure handling:** Fault sequence cannot override latched safety permissions..

### `Supervisor_Shutdown_Procedure.vi`
**Purpose:** Execute exactly one test-specific shutdown sequence.

**Connector inputs:** TestDefinition, shutdown reason.

**Connector outputs:** Completion/timeout.

**Block-diagram logic:** Run bounded approved shutdown actions if safe; when unavailable rely on protective fallback and record outcome..

**Functions / blocks to use:** Restricted sequence runner, Event Logger.

**Failure handling:** Do not use failed sensor for closed-loop shutdown..

### `Supervisor_Finalize_Run.vi`
**Purpose:** Finalize run after control secured.

**Connector inputs:** RunContext, results and events.

**Connector outputs:** Final run status.

**Block-diagram logic:** Mark incomplete operations, commit run outcome, close capture sessions and release resources..

**Functions / blocks to use:** Bundle, File I/O/Logger requests.

**Failure handling:** Log failures do not reopen normal control..

### `Runtime_Close.vi`
**Purpose:** Orderly release of application services.

**Connector inputs:** Run state, service references.

**Connector outputs:** Close results.

**Block-diagram logic:** After safe state stop executor, bridge worker, logging and transport; report residual faults..

**Functions / blocks to use:** Enqueue close, Release Queue, Merge Errors.

**Failure handling:** Never turn off protection to make app exit faster..


## 05_Engine — 26 VIs

### `Executor_Loop.vi`
**Purpose:** Run scheduled actions without blocking.

**Connector inputs:** ExecutionPlan, RunContext, queues.

**Connector outputs:** Sequence events/results.

**Block-diagram logic:** Consume step events, service timers, dispatch ready work; yield each iteration; report progress to Supervisor..

**Functions / blocks to use:** While Loop, Dequeue Element with timeout, shift register, Case Structure.

**Failure handling:** Fault/stop events bypass ordinary backlogged work..

### `Executor_Begin_Group.vi`
**Purpose:** Initialize group-level execution.

**Connector inputs:** GroupDefinition, RunContext.

**Connector outputs:** GroupContext.

**Block-diagram logic:** Create branch contexts and cycle counters; register declared resource sets..

**Functions / blocks to use:** Initialize Array, Bundle by Name.

**Failure handling:** Reject invalid nested depth..

### `Scheduler_Find_Ready.vi`
**Purpose:** Select executable actions.

**Connector inputs:** ExecutionPlan, active state, completed dependencies.

**Connector outputs:** Ready step IDs.

**Block-diagram logic:** Resolve ordered dependencies, joins and completed predecessors; do not start blocked branches..

**Functions / blocks to use:** For Loop, Boolean logic, Search 1D Array.

**Failure handling:** Avoid circular waiting by prevalidated plan..

### `Scheduler_Claim_Resources.vi`
**Purpose:** Reserve command resources for action.

**Connector inputs:** Ready step resource declarations, lease table.

**Connector outputs:** Ownership tokens or busy state.

**Block-diagram logic:** Request all required leases in stable sorted order; reject/serialize conflicts before commanding..

**Functions / blocks to use:** Sort 1D Array, Bridge lease subVI.

**Failure handling:** A step cannot partially own incompatible resource set..

### `Scheduler_Join_Branches.vi`
**Purpose:** Apply parallel join policy.

**Connector inputs:** Branch statuses, group policy.

**Connector outputs:** Join outcome.

**Block-diagram logic:** Wait All/Selected/First Complete semantics; on declared fault preempt all; cancel unused branches safely..

**Functions / blocks to use:** Case Structure, AND Array Elements.

**Failure handling:** No orphan branch after early completion..

### `Scheduler_Advance.vi`
**Purpose:** Update graph execution and results.

**Connector inputs:** Step completion event, execution graph.

**Connector outputs:** New ready nodes/group status.

**Block-diagram logic:** Commit action terminal status, update dependency counters, queue next actions or cycle boundary..

**Functions / blocks to use:** Case Structure, Bundle by Name, Enqueue Element.

**Failure handling:** Duplicate completion event must not advance twice..

### `Step_Begin.vi`
**Purpose:** Create action instance.

**Connector inputs:** ActionDefinition, active run/cycle refs.

**Connector outputs:** StepContext.

**Block-diagram logic:** Set status active, phase precheck, assign action instance ID, deadlines and capture policy..

**Functions / blocks to use:** Bundle by Name, monotonic clock subVI.

**Failure handling:** Reject start if run already faulted..

### `Step_Tick.vi`
**Purpose:** Advance action phase with nonblocking checks.

**Connector inputs:** StepContext, current time, snapshots.

**Connector outputs:** Updated StepContext and outgoing requests.

**Block-diagram logic:** Inspect phase, send command once, wait for ACK/feedback, stabilize, dwell/capture, evaluate and finish..

**Functions / blocks to use:** Case Structure, shift registers, subVI calls.

**Failure handling:** No Wait(ms) inside a step state; deadline checked each tick..

### `Step_Enter_Phase.vi`
**Purpose:** Centralize phase entry side effects.

**Connector inputs:** Target phase, StepContext, monotonic time.

**Connector outputs:** New StepContext.

**Block-diagram logic:** Record phase start, reset relevant timers and issue required service request once..

**Functions / blocks to use:** Bundle by Name, Case Structure.

**Failure handling:** Prevent repeated command sends on every scheduler tick..

### `Step_On_Timeout.vi`
**Purpose:** Apply explicit timeout policy.

**Connector inputs:** StepContext, timer result, retry rules.

**Connector outputs:** Retry/Fail/Fault/Stop event.

**Block-diagram logic:** Count bounded retries and branch to correct action; record reason and escalation..

**Functions / blocks to use:** Select, Comparison, Case Structure.

**Failure handling:** Unbounded retries are configuration errors..

### `Step_Cancel.vi`
**Purpose:** Cancel action and cleanup.

**Connector inputs:** StepContext, stop/fault reason.

**Connector outputs:** Cancelled status.

**Block-diagram logic:** Cancel capture, plugin request and outstanding commands; release leases; mark partial results..

**Functions / blocks to use:** Enqueue control messages, Bridge release.

**Failure handling:** Cancellation must not wait for physical motion to finish..

### `Profile_Expand_Points.vi`
**Purpose:** Expand generic operating-point sweep.

**Connector inputs:** ProfileDefinition, configured axes.

**Connector outputs:** Ordered operating-point list.

**Block-diagram logic:** Generate pressure-only, flow-only, combined or explicit table points respecting configured order..

**Functions / blocks to use:** For Loop, Build Array, Array functions.

**Failure handling:** Enforce maximum point count/authorized envelope..

### `Profile_Get_Next_Point.vi`
**Purpose:** Advance through operating points.

**Connector inputs:** ProfileContext and last result.

**Connector outputs:** Next point or completed.

**Block-diagram logic:** Set per-point controller modes, target values, stabilization/dwell definitions..

**Functions / blocks to use:** Index Array, comparison.

**Failure handling:** Do not use implicit default mode after relief point..

### `Condition_Evaluate.vi`
**Purpose:** Return true/false/unknown.

**Connector inputs:** ConditionNode, ParameterSnapshot.

**Connector outputs:** ConditionResult.

**Block-diagram logic:** Evaluate expression tree and propagate bad quality; enforce typed operands and configured tolerance..

**Functions / blocks to use:** Case Structure, subVI recursion, In Range and Coerce.

**Failure handling:** UNKNOWN never implies pass..

### `Condition_Eval_Logic.vi`
**Purpose:** Combine AND/OR/NOT expressions.

**Connector inputs:** Child ConditionResults.

**Connector outputs:** ConditionResult.

**Block-diagram logic:** Apply three-valued logic preserving definitive false for AND and true for OR where valid; otherwise unknown..

**Functions / blocks to use:** Boolean logic, Case Structure.

**Failure handling:** Never coerce unknown to TRUE..

### `Condition_Compare.vi`
**Purpose:** Evaluate typed comparison leaf.

**Connector inputs:** Typed operands, operator, unit policy.

**Connector outputs:** ConditionResult.

**Block-diagram logic:** Resolve both operands, convert compatible units, compare in-range/greater/equal/relative tolerance..

**Functions / blocks to use:** Greater?, Less?, Equal?, In Range and Coerce.

**Failure handling:** Reject incompatible dimensions or divide-by-zero..

### `Condition_Check_Quality.vi`
**Purpose:** Verify signal freshness.

**Connector inputs:** ParameterValue, max age, clock.

**Connector outputs:** Valid/stale/invalid state.

**Block-diagram logic:** Reject impossible timestamps, age beyond limit and sensor invalid flags..

**Functions / blocks to use:** Tick Count/monotonic clock, comparison.

**Failure handling:** No reuse of last-good value without explicit policy..

### `Condition_Stabilize.vi`
**Purpose:** Require continuous valid completion.

**Connector inputs:** Previous stable-since, current condition, time, stable duration.

**Connector outputs:** Stable flag and updated timestamp.

**Block-diagram logic:** Start when TRUE, reset on FALSE/UNKNOWN, report stable only when uninterrupted interval passes..

**Functions / blocks to use:** Case Structure, subtraction, comparison.

**Failure handling:** Signal flicker restarts stability timer..

### `Cycle_Begin.vi`
**Purpose:** Begin group/test repetition.

**Connector inputs:** Counter set and cycle policy.

**Connector outputs:** New cycle identity.

**Block-diagram logic:** Assign monotonic attempt ID, advance started count and open result scope..

**Functions / blocks to use:** Bundle by Name, Add, ID helper.

**Failure handling:** Keep attempt ID distinct from completed cycle number..

### `Cycle_Finish.vi`
**Purpose:** Commit cycle outcome.

**Connector inputs:** Cycle context, branch outcomes.

**Connector outputs:** Updated counts / continue decision.

**Block-diagram logic:** Increment completed only on qualified success; record failure/retry separately..

**Functions / blocks to use:** Case Structure, counters, checkpoint request.

**Failure handling:** Power loss must not duplicate committed cycle..

### `Timer_Create.vi`
**Purpose:** Register a nonblocking deadline.

**Connector inputs:** Timer purpose, duration, monotonic clock.

**Connector outputs:** TimerTicket.

**Block-diagram logic:** Compute monotonic deadline and scope (ACK/feedback/stabilize/dwell/capture)..

**Functions / blocks to use:** Add, Bundle by Name.

**Failure handling:** Reject negative/overflow durations..

### `Timer_Check.vi`
**Purpose:** Evaluate timer status.

**Connector inputs:** TimerTicket, monotonic now.

**Connector outputs:** Pending/elapsed/expired.

**Block-diagram logic:** Compare deadlines; return event without sleeping..

**Functions / blocks to use:** Comparison, Select.

**Failure handling:** Wraparound handled by clock abstraction..

### `Popup_Begin.vi`
**Purpose:** Request an operator or feedback acknowledgement.

**Connector inputs:** Popup definition, request ID, timeout.

**Connector outputs:** Popup session state.

**Block-diagram logic:** Post prompt event to Host; register independent feedback and elapsed requirements..

**Functions / blocks to use:** Enqueue message, timer subVI.

**Failure handling:** Host unavailable triggers configured shutdown policy..

### `Popup_Check_ACK.vi`
**Purpose:** Evaluate ACK combinations.

**Connector inputs:** Popup state, Host ACK, digital feedback, clock.

**Connector outputs:** Pending/acknowledged/timeout.

**Block-diagram logic:** Match request ID/run ID; combine operator/time/feedback conditions per configured AND/OR rule..

**Functions / blocks to use:** Case Structure, Boolean logic.

**Failure handling:** Late ACK ignored after fault/stop..

### `Result_Calculate.vi`
**Purpose:** Calculate acceptance values.

**Connector inputs:** Formula definition, resolved measurements.

**Connector outputs:** Typed calculated result.

**Block-diagram logic:** Run supported arithmetic/comparison with units and missing-data policy; produce pass/fail/incomplete..

**Functions / blocks to use:** Add/Subtract/Multiply/Divide, comparison, Case Structure.

**Failure handling:** No implicit pass on unavailable reference..

### `Result_Resolve_Reference.vi`
**Purpose:** Fetch earlier stored measurement.

**Connector inputs:** Current run/step/cycle IDs, reference key.

**Connector outputs:** Typed stored result.

**Block-diagram logic:** Resolve named historical result with permitted scope and immutable identity..

**Functions / blocks to use:** Search 1D Array, index, lookup helper.

**Failure handling:** Reject ambiguous prior measurement..


## 06_Bridge — 8 VIs

### `Bridge_Loop.vi`
**Purpose:** Own hardware command gateway.

**Connector inputs:** Command queue, ownership table.

**Connector outputs:** Command ACKs and events.

**Block-diagram logic:** Prioritize protective preemption, validate normal requests, lease resources and route to registered adapters..

**Functions / blocks to use:** While Loop, Case Structure, bounded Queue, shift registers.

**Failure handling:** Do not embed PID or test-specific criteria..

### `Bridge_Validate_Command.vi`
**Purpose:** Check command envelope.

**Connector inputs:** CommandRequest, active plan, authorization state.

**Connector outputs:** Authorized/rejected reason.

**Block-diagram logic:** Verify run ID, owner token, resource, limits, unit, sequence number, deadlines and controller mode..

**Functions / blocks to use:** In Range and Coerce, Compare, Case Structure.

**Failure handling:** Reject stale/replayed commands..

### `Bridge_Acquire_Lease.vi`
**Purpose:** Grant exclusive write control.

**Connector inputs:** Resource IDs, run/step owner, lease table.

**Connector outputs:** Lease token / busy status.

**Block-diagram logic:** Atomically verify requested set then allocate bounded leases and expiry policy..

**Functions / blocks to use:** Case Structure, array lookup, Bundle by Name.

**Failure handling:** No two normal writers for same physical resource..

### `Bridge_Release_Lease.vi`
**Purpose:** Return resource ownership.

**Connector inputs:** Lease token, release reason.

**Connector outputs:** Release ACK.
