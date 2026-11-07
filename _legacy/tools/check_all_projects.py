import os
import xml.etree.ElementTree as ET

projs = [
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor\Universal_Sequence_Executor.lvproj",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor_AF.lvproj",
    r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor.lvproj",
]

for proj in projs:
    print("=" * 60)
    print("Checking:", proj)
    if not os.path.exists(proj):
        print("  DOES NOT EXIST!")
        continue
    base = os.path.dirname(proj)
    tree = ET.parse(proj)
    missing = 0
    for item in tree.getroot().iter("Item"):
        url = item.get("URL")
        name = item.get("Name", "")
        if not url or url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
            continue
        target = os.path.normpath(os.path.join(base, url))
        if not os.path.exists(target):
            print(f"  MISSING in {os.path.basename(proj)}: [{name}] -> {url}")
            missing += 1
    print(f"  Total missing in {os.path.basename(proj)}: {missing}")
