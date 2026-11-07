# Message classes to create (AF message maker)

Source: spec §5 and §6 (`docs/DESIGN_AF_EXECUTOR.md`). Tool: `lvai_create_message_class` (NI's message maker; the plugin says do NOT author `Do.vi` by hand, see `labview-actor-framework.md` §4/§7).

## What the maker produces (from the plugin doc, measured)

- Class `<method> Msg.lvclass` in a folder next to the actor, with `Do.vi` and `Send <method>.vi`.
- The payload is lifted from the method's input terminals. Field order is **descending conIdx** (§13a). Every payload method in `build/staging/` has exactly one payload, at conIdx 10.
- `Send <method>.vi` pane: `Message Enqueuer` (11, required), payload (10, required), `Message Priority (Normal)` (7), `error in (no error)` (8), then `error out` (0) and `Message Enqueuer out` (3).
- The tool does **not** add the class to the `.lvproj`. Add it by hand with the project closed (§7).
- One message class per folder (§15d). Create the library before the messages if the actors go into a library (§16a).
- Order (plugin `af-override-tools.md` §1): class, then typedef field binding, accessors, methods, pane-typedef binding, library, **messages**, overrides, hooks. So all methods below must exist and be class members before the messages are made.

## Sequence Executor messages (spec folder `src/Executor Messages/`)

| # | actor method (must exist first) | message class the maker creates | Send VI | payload (label : type) | priority when sent | sent by |
|---|---|---|---|---|---|---|
| 1 | `Load Sequence.vi` | `Load Sequence Msg` | `Send Load Sequence.vi` | `Sequence Path` : path | Normal | launcher, Load event |
| 2 | `Start Sequence.vi` | `Start Sequence Msg` | `Send Start Sequence.vi` | none | Normal | launcher, Start event |
| 3 | `Stop Sequence.vi` (wrapper: Abort "STOPPED BY OPERATOR") | `Stop Sequence Msg` | `Send Stop Sequence.vi` | none | Normal | launcher, Stop Sequence event |
| 4 | `Emergency Stop.vi` (wrapper: Abort "E-STOP") | `Emergency Stop Msg` | `Send Emergency Stop.vi` | none | **High** (spec says *critical*, see below) | launcher, E-Stop event |
| 5 | `Process Feedback.vi` | `Process Feedback Msg` (spec name: `Feedback Msg`) | `Send Process Feedback.vi` | `Plant Feedback` : Plant Feedback.ctl | Normal | Sim Plant `Tick.vi`, to its caller |

## Sim Plant messages (spec folder `src/Sim Plant Messages/`)

| # | actor method | message class | Send VI | payload | priority | sent by |
|---|---|---|---|---|---|---|
| 6 | `Set Setpoints.vi` | `Set Setpoints Msg` | `Send Set Setpoints.vi` | `Plant Setpoints` : Plant Setpoints.ctl | Normal | executor `Begin Step`, `Finish Sequence`, `Abort Sequence` |
| 7 | `Tick.vi` | `Tick Msg` (spec name: `Plant Tick Msg`) | `Send Tick.vi` (not used) | none | Normal | `Time-Delayed Send Message.vi` from the Sim Plant Actor Core hook, every 100 ms, `# Copies` 0 |

## Notes and deviations

- **Critical priority is not available.** Measured offline from `vi.lib\ActorFramework`: `Message Priority (Normal)` on `Enqueue.vi` and on `Time-Delayed Send Message.vi` is `uint16{Low,Normal,High}`. `Enqueue Critical.vi` is community scope (`NI.ClassItem.MethodScope` 4), which only friends can call (`Stop Msg`, `Last Ack`, the AF library). So a user message can be sent at **High** at most. The launcher draft sends Emergency Stop with `Message Priority (Normal)` = 2 (High). The alternative, AF's own `Stop Msg.lvclass:Send Emergency Stop.vi`, stops the whole actor with error 1608. That is not what spec §1.5 means, because the plant must be driven to safe setpoints first.
- **Name clash, harmless:** `Emergency Stop Msg.lvclass:Send Emergency Stop.vi` and AF's `Stop Msg.lvclass:Send Emergency Stop.vi` share a file name. The qualified names differ, so it works, but the Call target in the launcher must be the qualified one (`Emergency Stop Msg.lvclass\3ASend Emergency Stop.vi`).
- **#5 and #7 names:** the maker's default name is `<method> Msg`. To get the spec's `Feedback Msg` / `Plant Tick Msg` exactly, either name the methods `Feedback.vi` / `Plant Tick.vi`, or rename the classes after creation. The drafts use the maker defaults (`Process Feedback Msg`, `Tick Msg`). README Q3.
- **#3 and #4** need the two thin wrapper methods (`Stop Sequence.vi`, `Emergency Stop.vi`, drafted in `executor/`). A message made from `Abort Sequence.vi` directly would carry a `Reason` payload, which the spec does not want.
- **Not messages:** `Configure.vi`, `Configure Plant Displays.vi` (called before launch), and the private `Begin Step.vi`, `Finish Sequence.vi`, `Update Displays.vi`, `Reset Results.vi`, plus the hook VIs.
- Every method behind a message returns **no error** for operator mistakes (bad path, start before load, start while running). Status reports them instead (spec §2).
