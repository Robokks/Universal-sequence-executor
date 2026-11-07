// Private data for Sequence Executor Actor
// This control defines the private state used by the actor.
// Fields are intentionally simple placeholders for now.

define Cluster {
    string  CurrentTestID;      // e.g., "VTU_ACCEPTANCE_TEST_01"
    string  ConfigPath;         // Path to JSON config file
    int32   CurrentGroupIdx;    // Index of current group in the sequence
    int32   CurrentStepIdx;     // Index of current step within the group
    enum    ExecutionState {IDLE, LOADED, RUNNING_STEP, DWELLING, RAMPING, WAITING_IO, FAULT_RETRACT, COMPLETED};
    string  ExecutionStateStr;  // Human‑readable status for UI
    double  TargetFlow;         // Flow setpoint (LPM)
    double  TargetPressure;     // Pressure setpoint (bar)
    double  TargetServo;        // Servo displacement (mm)
    double  MeasuredFlow;       // Live feedback from hardware / simulation
    double  MeasuredPressure;   // Live feedback
    double  MeasuredHitchLoad;  // Live feedback (kN)
    bool    FaultDetected;      // Flag set when a safety condition occurs
    string  FaultCode;          // Optional code describing the fault
}
