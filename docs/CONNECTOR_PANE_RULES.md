# Connector pane rules (mandatory for every VI in this project)

Source of truth: the user's hand-built Counter sample (`Messages/Add/Do.vi`, `CounterActor/*.vi`).
Pattern **4815** (4-2-2-4) for every VI. Use **4835** only if a VI has more than 6 inputs or more than 6 outputs, and say so in the report.

## Slot map for 4815 (conIdx)

(Measured with `lvai_connector_pane` by DeepSeek, 2026-11-07 — corrected from an earlier wrong top/bottom numbering.)
```
            top:    7     5
 left  11  ┌───────────────┐  3   right
 inputs 10 │               │  2   outputs
        9  │               │  1
        8  └───────────────┘  0
         bottom:   6     4
```

| Slot | Use |
|---|---|
| 11 (left top) | main input: class/actor in, or the main data input of a plain VI |
| 10 | 2nd input |
| 9 | 3rd input |
| 8 (left bottom) | **error in** — always here when the VI has error terminals |
| 3 (right top) | main output: class/actor out, or the main data output |
| 2 | 2nd output |
| 1 | 3rd output |
| 0 (right bottom) | **error out** — always here when the VI has error terminals |
| 7 then 5 (top) | extra inputs only if the left column is full |
| 6 then 4 (bottom) | extra outputs only if the right column is full |

Mandatory:
1. Inputs on the left/top, outputs on the right/bottom. Never mix.
2. Class methods: `<Class> in` = 11, `<Class> out` = 3 (same row). Messages' Do.vi stays as the AF message maker creates it.
3. error in = 8, error out = 0. Pure math VIs without error terminals leave 8 and 0 empty.
4. Connection type: main input and error in = **Required**; other inputs = Recommended; outputs = Recommended. Never "Optional" for a main input.
5. Every front-panel control/indicator that is part of the contract MUST be on the pane. No unconnected contract terminals; no internal helper controls on the pane.
6. Terminal labels must be exactly the names in `docs/DESIGN_AF_EXECUTOR.md` §4 (they are what callers wire by name).
7. After creating each VI, read it back with `lvai_connector_pane` / `lvai_vi_terminals` and paste the slot list into the report. A VI whose pane does not match this table is not done.

## Assignment for the v2 Logic VIs

| VI | 11 | 10 | 9 | 8 | 3 | 2 | 1 | 0 | top/bottom |
|---|---|---|---|---|---|---|---|---|---|
| Parse Sequence JSON | JSON string | | | error in | Sequence File | | | error out | |
| Read Sequence File | path | | | error in | Sequence File | rig config path | | error out | |
| Read Rig Config | path | | | error in | Rig Config | plugin class path | | error out | |
| Validate Sequence | Sequence File | Rig Config | | error in | valid | problems | | error out | |
| Lookup Channel | Channel Feedback | channel | | | value | found | | | |
| Evaluate Conditions | conditions | Channel Feedback | | | all within | all found | measured | | 6 target, 4 missing channel |
| Evaluate Step (4835) | see note | | | | | | | | |
| Build Step Table | Sequence File | Step Results | | | Step Table | | | | |
| Write Results CSV | results folder | sequence_id | rig_id | error in | file path | | | error out | 7 Step Results, 5 overall verdict |
| Safe Setpoints | Rig Config | | | | setpoints | | | | |
| Sim First Order Step (plugin) | State | Setpoints | dt s | | new State | | | | |

Evaluate Step has 5 inputs / 7 outputs → use **4835**. Inputs on the left in this order top→bottom: Step Config, Channel Feedback, Step Phase in, step start ms, dwell start ms. Outputs on the right top→bottom: Step Phase out, dwell start ms out, done, passed, reason, measured, target. Report the conIdx numbers you used.
