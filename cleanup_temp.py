"""Clean up temporary scripts and update .gitignore"""
import os

PROJ = r"C:\Users\gfl_s\Desktop\consensus-pipeline-dev-v2-stance"

# 1. Delete temporary files
temp_files = [
    "verify_files.py",
    "verify_app.py",
    "apply_ui_patch.py",
    "fix_init.py",
    "download_files.ps1",
    "_patch.py",
    "_patch2.py",
]

print("=== Deleting temp files ===")
for f in temp_files:
    p = os.path.join(PROJ, f)
    if os.path.exists(p):
        os.remove(p)
        print(f"  DEL {f}")
    else:
        print(f"  SKIP {f} (not found)")

# 2. Update .gitignore to prevent temp files from being committed
gitignore_path = os.path.join(PROJ, ".gitignore")
patterns_to_add = [
    "# Temporary scripts (auto-generated, do not commit)",
    "verify_files.py",
    "verify_app.py",
    "apply_ui_patch.py",
    "fix_init.py",
    "download_files.ps1",
    "_patch*.py",
]

existing = ""
if os.path.exists(gitignore_path):
    with open(gitignore_path, "r", encoding="utf-8") as fh:
        existing = fh.read()

new_lines = []
for p in patterns_to_add:
    if p not in existing:
        new_lines.append(p)

if new_lines:
    with open(gitignore_path, "a", encoding="utf-8") as fh:
        fh.write("\n" + "\n".join(new_lines) + "\n")
    print(f"\n=== Updated .gitignore (+{len(new_lines)} patterns) ===")
    for p in new_lines:
        print(f"  + {p}")
else:
    print("\n=== .gitignore already up to date ===")

# 3. Check if any temp files are already tracked by git
import subprocess
result = subprocess.run(
    ["git", "ls-files", "--cached"],
    cwd=PROJ, capture_output=True, text=True, encoding="utf-8", errors="replace"
)
tracked = result.stdout.strip().split("\n")
tracked_temps = [f for f in temp_files if f in tracked]

if tracked_temps:
    print(f"\n=== WARNING: {len(tracked_temps)} temp files already tracked by git ===")
    for f in tracked_temps:
        print(f"  git rm --cached {f}")
    # Remove from git index (keep local copy already deleted above, so just untrack)
    subprocess.run(
        ["git", "rm", "--cached"] + tracked_temps,
        cwd=PROJ, capture_output=True, text=True
    )
    print("  Done. Files removed from git index.")
else:
    print("\n=== No temp files tracked by git (good) ===")

print("\n=== Clean up complete ===")
