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


def prepare_interface_for_check(output_path=None):
    """
    准备用于 maa-checker 的 interface.json
    
    将开发环境的路径转换为适合 maa-checker 检查的路径
    maa-checker 从项目根目录运行，需要移除 ../../ 前缀
    
    Args:
        output_path: 输出路径，默认为项目根目录的 interface.json
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
                res["path"] = [
                    p.replace("../../assets/", "") for p in res["path"]
                ]
    
    if output_path is None:
        output_path = working_dir / "interface.json"
    else:
        output_path = Path(output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)
    
    print(f"Prepared interface.json for check: {output_path}")
    return output_path


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else None
    prepare_interface_for_check(output)
