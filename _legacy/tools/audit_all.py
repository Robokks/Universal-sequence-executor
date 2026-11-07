import os
import xml.etree.ElementTree as ET

def check_dir(base_dir):
    print("=" * 70)
    print("AUDITING DIRECTORY:", base_dir)
    print("=" * 70)

    # 1. Projects
    for f in os.listdir(base_dir):
        if f.endswith(".lvproj"):
            proj_path = os.path.join(base_dir, f)
            print(f"\n--- Checking Project: {f} ---")
            try:
                tree = ET.parse(proj_path)
                for item in tree.getroot().iter("Item"):
                    url = item.get("URL")
                    name = item.get("Name", "")
                    if not url or url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
                        continue
                    target = os.path.normpath(os.path.join(base_dir, url))
                    if not os.path.exists(target):
                        print(f"  [MISSING IN PROJ] Item='{name}' URL='{url}' -> {target}")
            except Exception as e:
                print(f"  [ERROR] {e}")

    # 2. All lvclass and lvlib files
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".lvclass") or f.endswith(".lvlib"):
                lib_path = os.path.join(root, f)
                lib_dir = os.path.dirname(lib_path)
                try:
                    tree = ET.parse(lib_path)
                    for item in tree.getroot().iter("Item"):
                        url = item.get("URL")
                        name = item.get("Name", "")
                        if not url or url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
                            continue
                        target = os.path.normpath(os.path.join(lib_dir, url))
                        if not os.path.exists(target):
                            rel_lib = os.path.relpath(lib_path, base_dir)
                            print(f"  [MISSING IN {rel_lib}] Item='{name}' URL='{url}' -> {target}")
                except Exception as e:
                    print(f"  [ERROR parsing {lib_path}] {e}")

if __name__ == "__main__":
    check_dir(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF")
    check_dir(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor")
