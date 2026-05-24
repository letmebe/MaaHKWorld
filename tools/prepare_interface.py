from pathlib import Path
import sys

try:
    import jsonc
except ModuleNotFoundError as e:
    raise ImportError(
        "Missing dependency 'json-with-comments' (imported as 'jsonc').\n"
        f"Install it with:\n  {sys.executable} -m pip install json-with-comments\n"
        "Or add it to your project's requirements."
    ) from e


def prepare_interface_for_check():
    """
    准备用于 maa-checker 的 interface.json
    
    直接修改 assets/interface.json 中的路径
    将开发环境的路径转换为适合 maa-checker 检查的路径
    """
    working_dir = Path(__file__).parent.parent.resolve()
    interface_file = working_dir / "assets" / "interface.json"
    
    if not interface_file.exists():
        print(f"Error: {interface_file} not found")
        sys.exit(1)
    
    with open(interface_file, "r", encoding="utf-8") as f:
        interface = jsonc.load(f)
    
    # 修正路径，移除 ../../ 前缀
    if "agent" in interface:
        if "child_exec" in interface["agent"]:
            interface["agent"]["child_exec"] = interface["agent"]["child_exec"].replace("../../", "")
        if "child_args" in interface["agent"]:
            interface["agent"]["child_args"] = [
                arg.replace("../../", "") for arg in interface["agent"]["child_args"]
            ]
    
    if "resource" in interface:
        for res in interface["resource"]:
            if "path" in res:
                # ../../assets/resource -> ./resource
                res["path"] = ["./resource"]
    
    with open(interface_file, "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)
    
    print(f"Prepared interface.json for check: {interface_file}")


if __name__ == "__main__":
    prepare_interface_for_check()
