import os
import shutil
import xml.etree.ElementTree as ET

af_dir = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF"
main_dir = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor"

print("--- STEP 1 & 2: Fixing Universal_Sequence_Executor.lvproj in both workspaces ---")
for proj_path in [
    os.path.join(main_dir, "Universal_Sequence_Executor.lvproj"),
    os.path.join(af_dir, "Universal_Sequence_Executor.lvproj")
]:
    if os.path.exists(proj_path):
        with open(proj_path, "r", encoding="utf-8") as f:
            content = f.read()
        fixed = content.replace('URL="../src/', 'URL="src/').replace('URL="../tests"', 'URL="tests"')
        with open(proj_path, "w", encoding="utf-8") as f:
            f.write(fixed)
        print("Updated:", proj_path)

print("\n--- STEP 3: Fixing SequenceActor.lvclass and CounterActor.lvclass ---")
sa_dir = os.path.join(af_dir, "src", "01_Host", "SequenceActor")
# Ensure .ctl files exist
sample_ctl = os.path.join(af_dir, "src", "01_Host", "Sequence_Actor", "Sequence_Actor.ctl")
if os.path.exists(sample_ctl):
    shutil.copy2(sample_ctl, os.path.join(sa_dir, "SequenceActor.ctl"))
    shutil.copy2(sample_ctl, os.path.join(sa_dir, "CounterActor.ctl"))
    print("Created SequenceActor.ctl and CounterActor.ctl")

for cls_name in ["SequenceActor.lvclass", "CounterActor.lvclass"]:
    cls_path = os.path.join(sa_dir, cls_name)
    if os.path.exists(cls_path):
        with open(cls_path, "r", encoding="utf-8") as f:
            c = f.read()
        # Fix relative URLs
        c = c.replace('URL="../Configure.vi"', 'URL="Configure.vi"')
        c = c.replace('URL="../Add.vi"', 'URL="Add.vi"')
        c = c.replace('URL="../Reset.vi"', 'URL="Reset.vi"')
        c = c.replace('URL="../Stop Core.vi"', 'URL="Stop Core.vi"')
        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Fixed URLs in", cls_path)

# Also copy member VIs to parent 01_Host and Sequence_Actor as safety buffer
host_dir = os.path.join(af_dir, "src", "01_Host")
seq_actor_dir = os.path.join(af_dir, "src", "01_Host", "Sequence_Actor")
for vi_name in ["Configure.vi", "Add.vi", "Reset.vi", "Stop Core.vi"]:
    src_vi = os.path.join(sa_dir, vi_name)
    if os.path.exists(src_vi):
        shutil.copy2(src_vi, os.path.join(host_dir, vi_name))
        shutil.copy2(src_vi, os.path.join(seq_actor_dir, vi_name))
        print(f"Copied {vi_name} to 01_Host/ and Sequence_Actor/ buffer")

print("\n--- STEP 4: Fixing Messages/Execute_Step classes and VIs ---")
exec_dir = os.path.join(af_dir, "src", "01_Host", "Messages", "Execute_Step")
if os.path.exists(sample_ctl):
    shutil.copy2(sample_ctl, os.path.join(exec_dir, "Execute Step Msg.ctl"))
    shutil.copy2(sample_ctl, os.path.join(exec_dir, "Counter Add Msg.ctl"))
    print("Created Execute Step Msg.ctl and Counter Add Msg.ctl")

for cls_name in ["Execute Step Msg.lvclass", "Counter Add Msg.lvclass"]:
    cls_path = os.path.join(exec_dir, cls_name)
    if os.path.exists(cls_path):
        with open(cls_path, "r", encoding="utf-8") as f:
            c = f.read()
        c = c.replace('URL="../Send Add.vi"', 'URL="Send Add.vi"')
        c = c.replace('URL="../Do.vi"', 'URL="Do.vi"')
        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Fixed URLs in", cls_path)

# Also copy Do.vi and Send Add.vi to parent Messages/
parent_msg_dir = os.path.join(af_dir, "src", "01_Host", "Messages")
for vi_name in ["Do.vi", "Send Add.vi"]:
    src_vi = os.path.join(exec_dir, vi_name)
    if os.path.exists(src_vi):
        shutil.copy2(src_vi, os.path.join(parent_msg_dir, vi_name))
        print(f"Copied {vi_name} to Messages/ buffer")

print("\n--- STEP 5: Fixing Messages/Reset classes and VIs ---")
reset_dir = os.path.join(af_dir, "src", "01_Host", "Messages", "Reset")
if os.path.exists(sample_ctl):
    shutil.copy2(sample_ctl, os.path.join(reset_dir, "Reset Msg.ctl"))
    shutil.copy2(sample_ctl, os.path.join(reset_dir, "Counter Reset Msg.ctl"))
    print("Created Reset Msg.ctl and Counter Reset Msg.ctl")

for cls_name in ["Reset Msg.lvclass", "Counter Reset Msg.lvclass"]:
    cls_path = os.path.join(reset_dir, cls_name)
    if os.path.exists(cls_path):
        with open(cls_path, "r", encoding="utf-8") as f:
            c = f.read()
        c = c.replace('URL="../Send Reset.vi"', 'URL="Send Reset.vi"')
        c = c.replace('URL="../Do.vi"', 'URL="Do.vi"')
        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(c)
        print("Fixed URLs in", cls_path)

for vi_name in ["Do.vi", "Send Reset.vi"]:
    src_vi = os.path.join(reset_dir, vi_name)
    if os.path.exists(src_vi):
        shutil.copy2(src_vi, os.path.join(parent_msg_dir, vi_name))
        print(f"Copied {vi_name} to Messages/ buffer")

print("\n--- STEP 6: Fixing Sequence_Actor legacy messages ---")
valid_do = os.path.join(exec_dir, "Do.vi")
adv_msg_dir = os.path.join(af_dir, "src", "01_Host", "Sequence_Actor", "Messages", "Advance_Step_Msg")
exec_msg_dir = os.path.join(af_dir, "src", "01_Host", "Sequence_Actor", "Messages", "Execute_Step_Msg")
if os.path.exists(adv_msg_dir) and not os.path.exists(os.path.join(adv_msg_dir, "Do.vi")):
    shutil.copy2(valid_do, os.path.join(adv_msg_dir, "Do.vi"))
    print("Provided Do.vi for Advance_Step_Msg")

if os.path.exists(exec_msg_dir) and not os.path.exists(os.path.join(exec_msg_dir, "Do.vi")):
    shutil.copy2(valid_do, os.path.join(exec_msg_dir, "Do.vi"))
    print("Provided Do.vi for Sequence_Actor/Execute_Step_Msg")

print("\n--- COMPLETE FIX APPLIED SUCCESSFULLY ---")
