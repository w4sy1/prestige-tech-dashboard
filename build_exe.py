from pathlib import Path
import os, subprocess, sys
root=Path(__file__).resolve().parent
if os.name!="nt": raise SystemExit("Windows EXE musi być budowany na Windows.")
cmd=[sys.executable,"-m","PyInstaller","--noconfirm","--onefile","--windowed","--name",root.name,
     "--hidden-import","module_manager","--add-data","modules.json;."]
for name in ("metadata.json","LICENSE","THIRD_PARTY_NOTICES.txt","config","assets"):
    p=root/name
    if p.exists(): cmd += ["--add-data",str(p)+";"+(name if p.is_dir() else ".")]
cmd.append("gui.py")
subprocess.run(cmd,cwd=root,check=True)
print(root/"dist"/(root.name+".exe"))

