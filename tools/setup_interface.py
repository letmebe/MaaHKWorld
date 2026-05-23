"""
Setup interface.json for development environment
"""
import json
import shutil
from pathlib import Path

def setup_interface():
    root_dir = Path(__file__).parent.parent
    assets_interface = root_dir / "assets" / "interface.json"
    mfa_dir = root_dir / "tools" / "MFAAvalonia"
    
    # Check if development environment
    if not assets_interface.exists():
        # Release package, nothing to do
        return
    
    if not mfa_dir.exists():
        print("[WARN] tools/MFAAvalonia not found")
        return
    
    # Copy interface.json to MFAAvalonia directory
    target_interface = mfa_dir / "interface.json"
    
    with open(assets_interface, "r", encoding="utf-8") as f:
        interface = json.load(f)
    
    # Modify paths for development environment
    # From tools/MFAAvalonia/ directory:
    # - venv is at ../../venv/
    # - agent is at ../../agent/
    # - resource is at ../../assets/resource/
    
    if "agent" in interface:
        # venv path: from tools/MFAAvalonia to root/venv
        interface["agent"]["child_exec"] = "../../venv/Scripts/python.exe"
        # agent path: from tools/MFAAvalonia to root/agent
        interface["agent"]["child_args"] = ["../../agent/start_agent.py"]
    
    if "resource" in interface:
        for res in interface["resource"]:
            if "path" in res:
                # resource path: from tools/MFAAvalonia to root/assets/resource
                res["path"] = ["../../assets/resource"]
    
    # Write modified interface.json
    with open(target_interface, "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)
    
    print(f"[OK] Setup interface.json for development environment")

if __name__ == "__main__":
    setup_interface()
