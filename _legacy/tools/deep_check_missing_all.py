import os
import sys
import xml.etree.ElementTree as ET

def deep_audit_project(proj_path):
    print("=" * 80)
    print(f"DEEP AUDIT FOR: {proj_path}")
    print("=" * 80)
    
    if not os.path.exists(proj_path):
        print(f"CRITICAL: Project file not found: {proj_path}")
        return False
        
    proj_dir = os.path.dirname(os.path.abspath(proj_path))
    tree = ET.parse(proj_path)
    root = tree.getroot()
    
    missing_items = []
    checked_files = set()
    
    # 1. Project level Item checks
    print("\n[Phase 1] Auditing all items in .lvproj XML...")
    for item in root.iter("Item"):
        url = item.get("URL")
        name = item.get("Name", "")
        item_type = item.get("Type", "")
        
        if not url:
            continue
        if url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
            continue
            
        full_path = os.path.normpath(os.path.join(proj_dir, url))
        if not os.path.exists(full_path):
            print(f"  [MISSING ITEM] Name='{name}', Type='{item_type}', URL='{url}' -> Resolved: {full_path}")
            missing_items.append((proj_path, name, full_path))
        else:
            checked_files.add(full_path)
            
    print(f"  Phase 1 complete. Found {len(missing_items)} missing items in project tree.")
    
    # 2. Auditing all .lvclass and .lvlib in the workspace
    print("\n[Phase 2] Auditing all .lvclass and .lvlib files in workspace...")
    class_missing = []
    for r, d, files in os.walk(proj_dir):
        for f in files:
            if f.endswith(".lvclass") or f.endswith(".lvlib"):
                lib_path = os.path.join(r, f)
                lib_dir = os.path.dirname(lib_path)
                try:
                    lib_tree = ET.parse(lib_path)
                    for item in lib_tree.getroot().iter("Item"):
                        url = item.get("URL")
                        name = item.get("Name", "")
                        if not url or url.startswith("/<vilib>") or url.startswith("&lt;vilib&gt;"):
                            continue
                        target = os.path.normpath(os.path.join(lib_dir, url))
                        if not os.path.exists(target):
                            rel_lib = os.path.relpath(lib_path, proj_dir)
                            print(f"  [MISSING IN {rel_lib}] Name='{name}', URL='{url}' -> Expected at: {target}")
                            class_missing.append((lib_path, name, target))
                except Exception as e:
                    print(f"  [XML ERROR in {lib_path}]: {e}")
                    class_missing.append((lib_path, "PARSE_ERROR", str(e)))
                    
    print(f"  Phase 2 complete. Found {len(class_missing)} missing member references in classes/libraries.")
    
    # 3. Disk Folder integrity check
    print("\n[Phase 3] Checking auto-populating disk folders...")
    disk_folder_missing = []
    for item in root.iter("Item"):
        url = item.get("URL")
        name = item.get("Name", "")
        # Check if it has NI.DISK property
        is_disk = False
        for prop in item.iter("Property"):
            if prop.get("Name") == "NI.DISK" and prop.text == "true":
                is_disk = True
                break
        if is_disk and url:
            disk_path = os.path.normpath(os.path.join(proj_dir, url))
            if not os.path.isdir(disk_path):
                print(f"  [MISSING DISK FOLDER] Name='{name}', URL='{url}' -> {disk_path}")
                disk_folder_missing.append((name, disk_path))
            else:
                count = len([x for x in os.listdir(disk_path)])
                # print(f"  Disk folder OK: {name} -> {count} items")
                
    print(f"  Phase 3 complete. Found {len(disk_folder_missing)} missing disk folders.")
    
    # 4. Total summary
    total_issues = len(missing_items) + len(class_missing) + len(disk_folder_missing)
    print("\n" + "-" * 80)
    print(f"TOTAL MISSING FILES/FOLDERS FOR THIS PROJECT: {total_issues}")
    print("-" * 80)
    return total_issues == 0

if __name__ == "__main__":
    qmh_ok = deep_audit_project(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor\Universal_Sequence_Executor.lvproj")
    af_ok = deep_audit_project(r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF\Universal_Sequence_Executor_AF.lvproj")
    
    print("\n" + "=" * 80)
    print(f"FINAL AUDIT RESULT:")
    print(f"  QMH Project Clean? {'YES - ZERO MISSING' if qmh_ok else 'NO - ISSUES FOUND'}")
    print(f"  AF Project Clean?  {'YES - ZERO MISSING' if af_ok else 'NO - ISSUES FOUND'}")
    print("=" * 80)
    
    if not (qmh_ok and af_ok):
        sys.exit(1)
