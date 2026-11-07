# 2. Detailed Python module and function design

Every entry states the role, key functions, algorithm, and integration or failure behavior. This describes the actual supplied implementation, with limitations identified.

## `domain/models.py` — message and result types

- `Quality`: `VALID`, `STALE`, `INVALID`.
- `Truth`: condition result `TRUE`, `FALSE`, or `UNKNOWN`.
- `RunState`: `IDLE`, `VALIDATING`, `READY`, `RUNNING`, `STOPPING`, `FAULTING`, `FINISHED`, `FAULTED` (not all transitions exercised in demo).
- `ParameterDefinition(id, unit, kind, max_age_s)`: schema for a feedback channel.
- `Measurement(value, sampled_at, quality)`: immutable timestamped observation.
- `Command(command_id, resource, target, unit, run_id, owner, epoch)`: command/ownership identity.
- `StepResult(step_id, status, samples)`: one step completion payload.
- `ConfigurationError`, `ExecutionFault`, `CommandRejected`: domain error categories.

**Reason:** all modules communicate through named, typed contracts rather than guessing meanings from raw strings.

## `config/validator.py` — config preflight

- `load_config(path)`: open UTF-8 JSON and parse it. Raises on invalid JSON or missing file.
- `_condition_refs(tree, registry, resources)`: recursively walks AND/OR expressions; rejects missing references, mismatched units, unsupported comparisons, negative tolerances.
- `validate(config)`: checks schema version, nonempty resource/test tables, unique parameter IDs, positive freshness limits, group depth/repetition, step kinds, timeouts/delays, registered plugin names, command-unit/range matching, relative motion feedback source, report channel references and whitelisted simulation fault/shutdown actions. Returns `ParameterDefinition` list.

**Limit:** this is not a full industrial preflight. A relative command may be within delta range yet exceed the physical final target; Bridge validates the resolved target at runtime.

## `registry/parameters.py` — feedback registry

- `ParameterRegistry(definitions)`: build mapping of permitted feedback IDs.
- `update(name, value, quality=VALID, timestamp=None)`: update a named measurement, defaulting to `time.monotonic()`.
- `get(name)`: return sample or `None`; if older than `max_age_s`, return same sample with `STALE` quality.

**Rule:** a stored command setpoint is not a measured actual. Time freshness is checked when the value is consumed.

## `conditions/evaluator.py` — tree evaluation

- `_lookup(operand, registry)`: resolve either live parameter or configured constant. Invalid/stale feedback yields unknown operand.
- `evaluate(tree, registry)`: recursively evaluate `and`, `or`, `eq`, `gt`, `lt`, `gte`, `lte`, `within`.
- Three-valued AND: FALSE dominates UNKNOWN; TRUE only if all TRUE.
- Three-valued OR: TRUE dominates UNKNOWN; FALSE only if all FALSE.
- Reject unit mismatches by returning `UNKNOWN` at evaluation (configuration validation should reject them first).

**Failure mode:** missing values do not spuriously satisfy a completion condition.

## `bridge/arbiter.py` — simulated resource authority

- `HardwareAdapter` protocol: requires `apply(resource, value)` and `safe_demo_state()`; only `SimulatedVTU` implements it here.
- `Bridge(adapter, resources)`: creates one `asyncio.Lock` per resource, tracks owner IDs, fault epoch, latched fault, and demo applied history.
- `lease(resources, owner, timeout)`: acquires **sorted unique resource locks**; records owner and yields epoch; releases on normal or exceptional exit. Sorted acquisition avoids circular lock ordering.
- `command(Command)`: checks fault latch, epoch, owner, unit, allowed range, then duplicate ID; forwards to dummy adapter and returns `APPLIED`, which does NOT mean physical feedback achieved.
- `fault_and_revoke()`: increments epoch, latches fault, drives demo setpoints to zero.
- `reset_demo_only()`: resets the demo latch between runs; not an industrial safety reset.

**Limit:** no protected physical IO, hard-RT guarantees or transactional multi-resource atomic commit.

## `simulator/plant.py` — dummy VTU

- `SimulatedVTU(registry)`: owns in-memory setpoints/actuals for `pressure`, `flow` and `pc_lever`.
- `apply`: updates only in-memory target values.
- `safe_demo_state`: sets all simulated targets to zero.
- `loop(period_s=0.02)`: uses a first-order exponential approach to target; publishes named feedback; models hitch position as a toy multiple of lever position.

**Limit:** these are illustrative dynamics and limits, not physical VTU parameters, hydraulic behavior or controller tuning values.

## `engine/steps.py` — one operating point or special action

- `StepRunner.acknowledge(step_id)`: sets an event to complete an operator-ACK demo step.
- `_resolved_condition(condition, targets)`: replaces runtime `commanded_target` operand with actual resolved command target; necessary for **relative servo steps**.
- `_wait_feedback(condition, timeout_s, stabilize_s)`: polls the condition every 10 ms until it remains TRUE for required stabilization interval or timeout expires. An UNKNOWN or FALSE resets stabilization.
- `_dwell_capture_post`: optional dwell, single-snapshot report capture, optional post-delay; emits report record.
- `execute(step, run_id, attempt)`: emits start; optional pre-delay; executes plugin or ACK or normal operating point. For normal steps it leases required resources, resolves relative targets from **fresh valid feedback**, sends commands via Bridge, waits for feedback, captures data, logs completion. Any exception records failure and propagates upward; cancellation records cancellation.

**Limits:** demo sends multi-resource commands one by one; no atomic group or hardware compensation sequence. `timeout_s` primarily bounds feedback, not all step stages; a production deadline needs explicit whole-step semantics.

## `engine/scheduler.py` — nested cycles and parallel groups

- `Scheduler.group(group, run_id, prefix='root')`: for each configured cycle, emit start; recurse into nested child groups; execute steps sequentially or concurrently by `asyncio.create_task`; if a branch fails, cancel pending branches, collect exceptions and propagate fault; emit cycle completed only when all required children finish.

**Resource contention:** Bridge serializes competing writers using sorted leases. Independent writers can run concurrently. Cancellation is cooperative for Python tasks.

## `plugins/base.py` — registered special operations

- `PluginManager`: static dictionary maps approved names to async demo functions.
- `sample_calculation`: return a selected feedback value as a result; read-only.
- `sample_full_test`: example complete-test plugin; produces a simple result, no hardware commands.
- `execute(name, arguments, timeout)`: check registration and apply `asyncio.timeout` to plugin invocation.

**Limit:** in-process plugins are not sandboxed. An uncooperative CPU-blocking plugin can prevent event-loop progress; a production design needs subprocess isolation or equivalent supervision where required.

## `supervisor/service.py` — run lifecycle

- `heartbeat()`: refresh Host monotonic timestamp.
- `_monitor(timeout)`: when enabled, detects missed heartbeat and requests global fault.
- `_demo_procedure`: executes only whitelisted `SIMULATED_SAFE_STATE` actions; not equipment shutdown.
- `request_fault(reason)`: latch fault, revoke Bridge command epoch, zero dummy setpoints and cancel active task.
- `request_stop()`: cancel active task and command demo zero targets.
- `run_test(test, heartbeat_timeout_s=None)`: create run ID, activate scheduler or complete-test plugin, optionally monitor heartbeat, execute normal demo shutdown, or on fault call demonstration fault and shutdown procedures. Returns run ID; state holds final outcome.

**Rule:** independent hardware protection is OUTSIDE this supervisor; see the earlier SRS/SDD for required protection layers.

## `reporting/logger.py` — event and measurement records

- `EventLogger.emit(event, **fields)`: append JSONL with Unix wall-clock timestamp and event fields.
- `capture(registry, names)`: return `{'channel':{'last':value,'n':1}}` from current valid fresh numeric samples; raise on missing/stale samples.

**Limit:** no averaging, report templates, transactional persistence, real high-rate buffering, file rotation, or synchronization with external data acquisition.

## `cli.py` / `__main__.py` — executable assembly

- `simulate(config_path, output)`: load/validate configuration, create registry, simulated plant, Bridge, logger, StepRunner, Scheduler and Supervisor; start plant task, run example test, print final state, and cancel plant task.
- `main()`: argparse entry point supporting `--config`, `--events`.
- `__main__.py`: allows `python -m universal_executor`.

**Integration principle:** each service receives its dependencies in the constructor; no module reaches into unrelated global state.