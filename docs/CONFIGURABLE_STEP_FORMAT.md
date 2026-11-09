# Configurable Step Format (draft v3)

This is the contract between the **configuration GUI** (built by the user) and the
**executor logic** (built in this repository). The GUI writes these JSON files and
the executor reads them. Neither side needs the other's code.

Samples: `configs/rigs/configurable_sim.json`, `configs/sequences/configurable_sample.json`.

## Rules

1. **Not configured means skipped.** An empty list, a delay of 0 or `enabled: false`
   means no check and no action.
2. **Names, not indexes.** Every IO is stored by its `name` from the rig file, so
   reordering a rig's IO list cannot change what a sequence does.
3. **Every name must exist in the rig file**, with the right `type`. Otherwise Load
   rejects the sequence.
4. **Every key must be present.** LabVIEW's JSON reader rejects a missing key (error -375006). Not configured is written as an empty list, 0, or `false`. `Flatten To JSON` on a cluster with these field names writes every key automatically.

## Rig file

```json
{
  "rig_id": "...",
  "description": "...",
  "plugin_class": "relative/path/to/Rig Plugin.lvclass",
  "channels": [
    { "name": "Pressure", "type": "AI", "unit": "bar", "min": 0, "max": 250 }
  ]
}
```

`type` is one of `AI`, `AO`, `DI`, `DO`, `MISC_BOOL`, `MISC_NUM`.
For digital types `unit`, `min` and `max` are not used.

## Sequence file

```json
{ "sequence_id": "...", "description": "...", "rig_config": "../rigs/x.json", "steps": [] }
```

## Step

| JSON key | Screen field | Type | Notes |
|---|---|---|---|
| `step_no` | S.No | int | |
| `step_name` | Sequence_Name | string | |
| `interlock_status` | Interlock Status text | string | Shown while checks run |
| `pre_delay_ms` | Pre-Delay | number | 0 = skip |
| `post_delay_ms` | Post-Delay | number | 0 = skip |
| `timeout_ms` | (new) | number | Limit for feedback checks; 0 = wait forever is **not** allowed when any check exists |
| `popup` | Sequence Popup | object | `enabled`, `message`, `type`, `timeout_ms` |
| `retest` | Retest Sequence | object | `enabled`, `popup`, `popup_message`, `condition`, `goto_step_no` |
| `log` | Datalog Type | object | `peak`, `average`, `event` (bool) |
| `actions.do` | DO_Action | list | `{ "name", "on": bool, "mode" }` |
| `actions.ao` | AO_Action | list | `{ "name", "value": number, "mode" }` |
| `actions.misc_write` | Misc Write | list | `{ "name", "on": bool }` |
| `actions.call` | MISC_FB_VI / Call Sub VI | list | Named actions, run by the rig plug-in |
| `checks.di_high` | DI_High Feedback | group | `{ "and": [names], "or": [names] }` |
| `checks.di_low` | DI_Low Feedback | group | same |
| `checks.misc_high` | Misc High Bool | group | same |
| `checks.misc_low` | Misc Low Bool | group | same |
| `checks.t0_high` | T0_High Feedback | range group | `{ "and": [{ "name", "min", "max" }], "or": [same] }` |
| `checks.t0_low` | T0_Low Feedback | range group | same |
| `checks.misc_compare` | Misc Compare | list | `{ "name", "compare_with", "comparison", "tolerance" }` |

`mode` is `FROM_IO` or `ACK`. `comparison` is `EQ`, `NE`, `GT`, `GE`, `LT` or `LE`.
`EQ` and `NE` use `tolerance` as a band. `GT`, `GE`, `LT` and `LE` ignore it.

## How a group passes

Every `and` item must be true, and at least one `or` item must be true.
An empty list counts as passed, so an empty group always passes.

## Execution order

1. Pre-delay
2. Popup
3. DO, AO and Misc Write actions, then Call actions
4. Feedback checks, until all pass or `timeout_ms` runs out
5. Post-delay, then logging
6. On failure: retest if enabled, otherwise fail the step and apply safe setpoints

## Open questions (behaviour not yet confirmed)

The reference Dashboard shows these fields but not how they are executed.

1. **Popup `type`:** which types exist, and what happens on timeout?
2. **Retest `condition`:** what are the options, and how many retries are allowed?
3. **T0 High versus T0 Low:** both have Min and Max. What is the difference?
4. **`ACK` mode:** who acknowledges, the operator or a device signal?
5. **Interlocks:** must checks be met before actions, after actions, or both?
6. **Monitoring:** are feedback checks only awaited, or also watched for the rest of the step?
