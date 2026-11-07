import os

af_root = r"c:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF"

# Files to remove from AF repo to ensure 100% clean separation
files_to_remove = [
    os.path.join(af_root, "Universal_Sequence_Executor.lvproj"),
    os.path.join(af_root, "Universal_Sequence_Executor.aliases"),
    os.path.join(af_root, "Universal_Sequence_Executor.lvlps"),
    os.path.join(af_root, ".Universal_Sequence_Executor.UserState"),
]

for f in files_to_remove:
    if os.path.exists(f):
        if os.path.isdir(f):
            import shutil
            shutil.rmtree(f)
            print("Removed dir:", f)
        else:
            os.remove(f)
            print("Removed file:", f)

print("AF workspace now strictly contains ONLY Universal_Sequence_Executor_AF.lvproj!")
