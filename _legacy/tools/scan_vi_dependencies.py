import os
import re

af_root = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF"
main_root = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor"

# Build an index of all files in both workspaces and in LabVIEW vi.lib
all_known_files = set()

for d in [af_root, main_root, r"C:\Program Files\National Instruments\LabVIEW 2026\vi.lib"]:
    if os.path.exists(d):
        for root, dirs, files in os.walk(d):
            for f in files:
                all_known_files.add(f.lower())

print(f"Total known files indexed: {len(all_known_files)}")

# Regex to find potential file references in binary
ref_pattern = re.compile(rb'([A-Za-z0-9_\- ]+\.(?:vi|ctl|lvclass|lvlib))', re.IGNORECASE)

def scan_vi(vi_path):
    with open(vi_path, "rb") as f:
        data = f.read()
    matches = set()
    for m in ref_pattern.finditer(data):
        try:
            name = m.group(1).decode("ascii", errors="ignore").strip()
            if len(name) > 3:
                matches.add(name)
        except:
            pass
    return matches

print("\n--- SCANNING TOP-LEVEL VIs in AF WORKSPACE ---")
target_vis = [
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Launch_Sequence_Actor.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Test_Sequence_Actor_Messaging.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Host_Sequence_Executor_GUI.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\SequenceActor\Configure.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\SequenceActor\Add.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\SequenceActor\Reset.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\SequenceActor\Stop Core.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Messages\Execute_Step\Do.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Messages\Execute_Step\Send Add.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Messages\Reset\Do.vi",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\src\01_Host\Messages\Reset\Send Reset.vi",
]

for vi in target_vis:
    if os.path.exists(vi):
        refs = scan_vi(vi)
        missing_refs = [r for r in refs if r.lower() not in all_known_files]
        print(f"\nVI: {os.path.basename(vi)}")
        print(f"  Total refs: {len(refs)}")
        if missing_refs:
            print(f"  POTENTIAL MISSING ({len(missing_refs)}): {missing_refs}")
        else:
            print("  All referenced files found!")
    else:
        print(f"\nVI DOES NOT EXIST: {vi}")
