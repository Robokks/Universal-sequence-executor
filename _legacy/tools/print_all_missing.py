import os
import xml.etree.ElementTree as ET

proj_dir = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF"

def inspect_xml(file_path):
    try:
        tree = ET.parse(file_path)
        base = os.path.dirname(file_path)
        for item in tree.getroot().iter("Item"):
            url = item.get("URL")
            name = item.get("Name", "")
            if not url or url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
                continue
            target = os.path.normpath(os.path.join(base, url))
            if not os.path.exists(target):
                rel_file = os.path.relpath(file_path, proj_dir)
                print(f"{rel_file} -> [{name}] URL='{url}' | MISSING: {target}")
    except Exception as e:
        print(f"ERROR {file_path}: {e}")

print("--- CHECKING LVPROJ FILES ---")
inspect_xml(os.path.join(proj_dir, "Universal_Sequence_Executor_AF.lvproj"))
inspect_xml(os.path.join(proj_dir, "Universal_Sequence_Executor.lvproj"))

print("\n--- CHECKING ALL LVCLASS FILES ---")
for root, dirs, files in os.walk(proj_dir):
    for f in files:
        if f.endswith(".lvclass"):
            inspect_xml(os.path.join(root, f))
