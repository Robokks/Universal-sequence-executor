# 3. Integration, initialization, step timing and fault flow

## Start-up call graph

```mermaid
sequenceDiagram
    participant CLI as CLI
    participant V as Validator
    participant P as Simulated Plant
    participant S as Supervisor
    participant G as Scheduler
    participant E as StepRunner
    participant B as Bridge
    participant R as Registry
    CLI->>V: Load + validate JSON
    CLI->>P: Start dummy feedback task
    CLI->>S: Construct and run selected test
    S->>G: Execute group tree
    G->>E: Execute operating point
    E->>B: Lease resources + command
    B->>P: Apply dummy targets
    P-->>R: Publish timestamped feedback
    E->>R: Poll feedback for condition
    R-->>E: Measurement + quality
    E-->>G: StepResult
    G-->>S: Group complete
    S->>P: Demo safe-state request
```

## Step decision flow

```mermaid
flowchart TD
   A[Step start] --> B[Optional pre-delay]
   B --> C{Action kind?}
   C -->|Plugin| P[Look up registered async plugin]
   C -->|ACK| K[Wait for operator event]
   C -->|Operating point| D[Acquire ordered resource leases]
   D --> E[Resolve relative target from live servo feedback]
   E --> F[Bridge checks owner, limits and fault epoch]
   F --> G[Apply simulated command]
   G --> H{Condition TRUE continuously?}
   H -->|No / UNKNOWN| I{Deadline exceeded?}
   I -->|No| H
   I -->|Yes| Z[Raise ExecutionFault]
   H -->|Yes| J[Dwell]
   P --> J
   K --> J
   J --> L[Capture fresh measurements]
   L --> M[Post-delay and completion]
   Z --> N[Supervisor fault path]
```

## Global fault/preemption flow

```mermaid
flowchart TD
  F[Equipment-like simulated failure / feedback timeout / Host heartbeat loss] --> S[Supervisor requests global fault]
  S --> R[Bridge increments ownership epoch and latches]
  R --> T[Demo setpoints set to zero]
  T --> C[Cancel active scheduler + parallel tasks]
  C --> P[Whitelisted demo fault and shutdown record]
  P --> X[Final state FAULTED; manual review required]
  H[Independent hardware protection] -. required in real machine; NOT in this simulator .-> T
```

## Integration order

1. Run condition tests (`registry` and `evaluator`) with no simulator.
2. Run Bridge authority tests with a fake adapter.
3. Start SimulatedVTU and confirm parameter IDs update with quality and timestamps.
4. Connect StepRunner + Bridge and execute one normal operating point.
5. Add nested Scheduler groups, exclusive lease checks and parallel-failure cancellation.
6. Start Supervisor, test stop/fault/heartbeat, verify no normal command after fault latch.
7. Connect registered plugins and ACK test steps.
8. Add audit JSONL output and capture validation.
9. Run the complete sample and compare logged events to expected flow.
10. Introduce a separate real Host/RT design only after rig-specific safety assessment; never treat the simulator as deployable control code.

## Example JSON sequence

`examples/vtu_demo.json` commands a simulated pressure/flow point, performs **relative** +2 mm PC lever motion with its own servo feedback and separate hitch feedback, then runs a read-only custom calculation plugin. Values, timing, and coupling are illustrative. **The example does not exercise all nine VTU test procedures.**