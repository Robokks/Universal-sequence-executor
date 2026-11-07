import os
import xml.etree.ElementTree as ET

def check_project(proj_path):
    print("==================================================")
    print("CHECKING PROJECT:", proj_path)
    print("==================================================")
    if not os.path.exists(proj_path):
        print("Project does not exist:", proj_path)
        return

    proj_dir = os.path.dirname(os.path.abspath(proj_path))
    tree = ET.parse(proj_path)
    root = tree.getroot()

    all_missing = []
    checked_classes = set()

    for item in root.iter("Item"):
        url = item.get("URL")
        name = item.get("Name", "")
        item_type = item.get("Type", "")

        if not url:
            continue
        if url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
            continue

        target_path = os.path.normpath(os.path.join(proj_dir, url))
        if not os.path.exists(target_path):
            print(f"[MISSING PROJECT ITEM] Type={item_type} Name='{name}' URL='{url}' -> Path: {target_path}")
            all_missing.append((proj_path, name, target_path))
        else:
            if target_path.endswith(".lvclass"):
                checked_classes.add(target_path)

    # Now inspect every lvclass in the workspace
    print("\n==================================================")
    print("CHECKING ALL .lvclass FILES IN WORKSPACE")
    print("==================================================")
    for root_dir, dirs, files in os.walk(proj_dir):
        for f in files:
            if f.endswith(".lvclass"):
                class_path = os.path.join(root_dir, f)
                c_dir = os.path.dirname(class_path)
                try:
                    c_tree = ET.parse(class_path)
                    c_root = c_tree.getroot()
                    for c_item in c_root.iter("Item"):
                        c_url = c_item.get("URL")
                        c_name = c_item.get("Name", "")
                        if not c_url:
                            continue
                        if c_url.startswith("/<vilib>") or c_url.startswith("&lt;vilib&gt;"):
                            continue
                        c_target = os.path.normpath(os.path.join(c_dir, c_url))
                        if not os.path.exists(c_target):
                            print(f"[MISSING CLASS MEMBER] In '{os.path.relpath(class_path, proj_dir)}': Item='{c_name}' URL='{c_url}' -> Expected at: {c_target}")
                            all_missing.append((class_path, c_name, c_target))
                except Exception as e:
                    print(f"Error parsing class {class_path}: {e}")

    print("\n==================================================")
    print(f"TOTAL MISSING REFERENCES DETECTED: {len(all_missing)}")
    print("==================================================")
    return all_missing

if __name__ == "__main__":
    check_project(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor_AF.lvproj")
    check_project(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor.lvproj")
