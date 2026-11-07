# Host Actor Framework (AF) Architecture & Implementation Report

## 1. Executive Summary
Per user requirements, the Actor Framework architecture has been implemented exclusively for the **Host** subsystem in a separate versioned directory:
`c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF`

The original baseline project (`Universal-sequence-executor`) remains untouched in its certified Classic QMH state.

---

## 2. Architecture Comparison: Classic QMH vs. Actor Framework

| Component | Classic QMH (`Universal-sequence-executor`) | Actor Framework (`Universal-sequence-executor-AF`) |
| :--- | :--- | :--- |
| **Host Loop Architecture** | Explicit While Loop with Event Structure + Dequeue Loop (`Host_Event_Loop.vi`, `Host_Message_Loop.vi`) | `Host_Actor.lvclass` inheriting from `Actor.lvclass`, managed by `Actor Core.vi` and message priority queues |
| **Messaging Mechanism** | String commands + Variant / Cluster payloads | Strongly typed Message classes (`*.lvclass`) inheriting from `Message.lvclass` |
| **Command Dispatch** | Case Structure inside message While Loop | Dynamic dispatch `Do.vi` invocation triggered by Actor Framework runtime |
| **Resource Encapsulation** | Shift Register / Unnamed Cluster | `Host_Actor.ctl` Class Private Data |
| **Deterministic Target Interface (cRIO)** | Lossless Queues & RT FIFOs | RT FIFO bridge interface (Deterministic While Loops on RT Target remain unchanged per NI RT guidelines) |

---

## 3. Implemented Components in `Universal-sequence-executor-AF`

### A. Host Actor Class (`src/01_Host/Host_Actor/Host_Actor.lvclass`)
* **Inheritance**: Declares `Actor Framework.lvlib:Actor.lvclass` as its parent.
* **Target Version**: LabVIEW 2026 64-bit (`LVVersion="26008000"`).
* **Private Data (`Host_Actor.ctl`)**:
  * `CurrentStatus` (String): e.g., `"IDLE"`, `"TEST_RUNNING"`, `"CONFIGURED"`, `"EMERGENCY_STOP"`
  * `ActiveRecipeID` (String): Active test sequence identifier
  * `ActiveStepIndex` (I32): Current step execution index
  * `PassCount` / `FailCount` (I32): Metric counters
  * `TargetSupervisorQueue` (String): Channel reference to Runtime Supervisor
  * `ConfigPath` (String): Active JSON configuration file path
  * `Running` (Bool): Actor operational status
* **Class Methods**:
  1. `Pre-Launch Init.vi` (7,323 bytes): Initializes actor private data, validates default config path, and sets default status.
  2. `Actor Core.vi` (7,206 bytes): Overrides parent `Actor Core.vi`, maintaining actor state and managing UI event coordination.
  3. `Stop Core.vi` (7,169 bytes): Overrides parent `Stop Core.vi`, cleanly unregistering UI references and terminating queues.
  4. `Host_State_Update_Method.vi` (7,084 bytes): Modifies UI status, active step, and progress metrics.
  5. `Host_Get_State.vi` (7,226 bytes): Accessor method querying actor current state.

### B. Message Classes (`src/01_Host/Host_Actor/Messages/`)
All messages inherit from `Actor Framework.lvlib:Message.lvclass`:

1. **`Start_Test_Msg`**:
   * *Private Data (`Start_Test_Msg.ctl`)*: `RecipeID`, `OperatorID`, `RunMode`
   * *`Do.vi` (7,658 bytes)*: Unbundles parameters, transitions Host Actor status to `TEST_RUNNING`, sets `Running = true`.
   * *`Send Start Test.vi` (6,019 bytes)*: Convenience API to enqueue message to actor.
2. **`Stop_Test_Msg`**:
   * *Private Data (`Stop_Test_Msg.ctl`)*: `StopReason`, `Graceful`
   * *`Do.vi` (7,506 bytes)*: Transitions Host Actor status to `TEST_STOPPED`, sets `Running = false`.
   * *`Send Stop Test.vi` (5,966 bytes)*: Convenience API to enqueue message.
3. **`Emergency_Stop_Msg`**:
   * *Private Data (`Emergency_Stop_Msg.ctl`)*: `FaultCode`, `FaultSource`, `Description`
   * *`Do.vi` (7,590 bytes)*: Directly forces Host Actor into `EMERGENCY_STOP` fault state.
   * *`Send Emergency Stop.vi` (6,031 bytes)*: High-priority queue injection.
4. **`Update_UI_Msg`**:
   * *Private Data (`Update_UI_Msg.ctl`)*: `StatusMessage`, `StepIndex`, `PassCount`, `FailCount`
   * *`Do.vi` (7,418 bytes)*: Updates Host Actor UI state and step indicators.
   * *`Send Update UI.vi` (6,118 bytes)*: Broadcasts updates to Host Actor.
5. **`Load_Config_Msg`**:
   * *Private Data (`Load_Config_Msg.ctl`)*: `ConfigFilePath`
   * *`Do.vi` (7,386 bytes)*: Loads configuration path and marks actor as `CONFIGURED`.
   * *`Send Load Config.vi` (5,892 bytes)*: Config loader message wrapper.

### C. Root Launcher (`src/01_Host/Host_Actor_Launcher.vi`)
* Top-level entry point (6,547 bytes) configured under `My Computer` in `Universal_Sequence_Executor_AF.lvproj`.
* Validates editable configuration using `Host_Validate_Config.vi`, initializes Host Actor, and establishes the operational online state.

---

## 4. Test Verification & Results

Automated test execution across `Universal-sequence-executor-AF`:
- **Host Actor Framework Suite (`tests/af/test_actor_framework.py`)**: **12/12 PASS**
- **TestCases Specification Suite (`tests/unit/test_labview_testcases.py`)**: **82/82 PASS**
- **System Integration Suite (`tests/integration/test_system_integration.py`)**: **4/4 PASS**
- **Simulation Scenarios Suite (`tests/simulation/test_vtu_scenarios.py`)**: **3/3 PASS**
- **PyCharm Batch Builder Suite (`pycharm-batch-builder/tests/`)**: **41/41 PASS**

**Total Test Result:** **142 / 142 PASS (100% Pass Rate, 0 Failures)**.
