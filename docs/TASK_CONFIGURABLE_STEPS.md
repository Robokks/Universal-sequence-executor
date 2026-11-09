# Task: configurable step logic

Owner: DeepSeek builds in LabVIEW. Claude reviews over the bridge. The user builds the
configuration GUI, so **do not build any configuration screen.**

Contract: `docs/CONFIGURABLE_STEP_FORMAT.md`. Samples: `configs/rigs/configurable_sim.json`,
`configs/sequences/configurable_sample.json`.

## Rules

- Follow `docs/AGENT_PROTOCOL.md` and the recipe in `docs/HANDOVER.md` section 9.
- Only one agent uses LabVIEW at a time. While building, you own it.
- Reference VIs under `D:\Karthikeyan\DEVELOPMENT\L3570_VTU HYDRAULIC TEST RIG` are read-only.
- Work on `af-host`. Do not commit or push unless the user asks. Never touch `main`.
- The existing 5-step VTU sequence must keep passing, or be migrated with the user's approval.
- Report only what was run. A pass needs a Caraya JUnit count or a real CSV.

## Caraya rule (a defect was found here)

Every assert must be chained on the error wire after `Define Test`, and no placeholder stub
may remain. The old `Test_Logic_Caraya.vi` failed both, and reported a false pass. Prove a
pass with the assert count in `tests/caraya/Run_All_Caraya-TestReport.xml`, and include
one deliberately wrong expectation as a negative control per new test VI, then restore it.

## Behaviour defaults (the user has not specified these)

- Popup: `OK` only. If it times out unanswered the step fails, so actions never run unconfirmed. `timeout_ms` 0 waits for the operator.
- Retest: on failure, 1 retry, then the step fails.
- T0 High and T0 Low: both are Min-Max range checks.
- `ACK`: operator acknowledgement.
- Checks run after actions and are awaited once, not monitored afterwards.
- Anything not configured is skipped.

## Build order

1. `src/Logic` (no Actor Framework): condition group AND/OR, range group, compare group,
   and one aggregate that evaluates all checks and names the first failing item. An empty
   list passes. An unknown name fails.
2. Caraya tests for step 1, added to `tests/caraya/Run_All_Caraya.vi`. Stop and report.
3. Typedefs and parser for the v3 format, with missing sections as not configured.
   Validate every name and `type` against the rig file at Load.
4. Executor step phases in the documented order: pre-delay, popup, actions, checks,
   post-delay, log, retest.
5. Sim rig: DI, DO, Misc and AO channels, driven by config, so `configurable_sample.json` runs.
6. Popup handling and logging (peak, average, event).
7. Acceptance: sample run with CSV, a failing check, a timeout, retest, Stop, E-Stop, Exit.

Report to Claude after each numbered step and wait for review.
