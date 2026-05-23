"""
Setup interface.json for development environment
Just copy assets/interface.json to tools/MFAAvalonia/
"""
import shutil
from pathlib import Path

def setup_interface():
    root_dir = Path(__file__).parent.parent
    assets_interface = root_dir / "assets" / "interface.json"
    mfa_interface = root_dir / "tools" / "MFAAvalonia" / "interface.json"
    
    # Check if development environment
    if not assets_interface.exists():
        # Release package, nothing to do
        return
    
    if not mfa_interface.parent.exists():
        print("[WARN] tools/MFAAvalonia not found")
        return
    
    # Copy interface.json to MFAAvalonia directory
    shutil.copy2(assets_interface, mfa_interface)
    print(f"[OK] Copied interface.json to tools/MFAAvalonia/")

if __name__ == "__main__":
    setup_interface()
