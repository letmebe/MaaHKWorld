"""
MaaFramework任务调试工具
直接使用interface.json中定义的任务，自动应用参数配置
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maa.tasker import Tasker
from maa.resource import Resource
from maa.controller import Win32Controller, MaaWin32ScreencapMethodEnum, MaaWin32InputMethodEnum
import json
import ctypes

def find_game_window():
    """
    查找游戏窗口
    
    Returns:
        窗口句柄(int)，如果未找到返回None
    """
    user32 = ctypes.windll.user32
    
    # 定义回调函数
    windows = []
    
    def enum_windows_proc(hwnd, lParam):
        # 获取窗口标题
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            
            # 查找包含"王者荣耀世界"的窗口
            if "王者荣耀世界" in title:
                # 获取窗口类名
                class_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buff, 256)
                class_name = class_buff.value
                
                # 检查是否是UnrealWindow类
                if "UnrealWindow" in class_name:
                    windows.append(hwnd)
        
        return True
    
    # 枚举所有窗口
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    
    if windows:
        return windows[0]  # 返回int
    return None

def load_interface():
    """加载interface.json"""
    interface_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'assets', 
        'interface.json'
    )
    
    with open(interface_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_tasks():
    """列出所有可用任务"""
    interface = load_interface()
    
    print("=" * 60)
    print("可用任务列表")
    print("=" * 60)
    
    for idx, task in enumerate(interface.get('task', []), 1):
        name = task.get('name')
        label = task.get('label')
        entry = task.get('entry')
        description = task.get('description', '')
        options = task.get('option', [])
        
        print(f"\n{idx}. {name} - {label}")
        print(f"   入口: {entry}")
        if options:
            print(f"   选项: {', '.join(options)}")
        if description:
            # 截断过长的描述
            desc = description if len(description) <= 80 else description[:77] + "..."
            print(f"   描述: {desc}")
    
    print("\n" + "=" * 60)

def get_task_config(task_name: str):
    """获取任务配置"""
    interface = load_interface()
    
    for task in interface.get('task', []):
        if task.get('name') == task_name:
            return task
    
    return None

def get_option_config(option_name: str):
    """获取选项配置"""
    interface = load_interface()
    
    # interface.option 是一个对象，key是选项名
    options = interface.get('option', {})
    return options.get(option_name)

def build_pipeline_override(task_config: dict, option_values: dict = None):
    """
    构建pipeline_override
    
    Args:
        task_config: 任务配置
        option_values: 选项值 {option_name: value}
    
    Returns:
        pipeline_override字典
    """
    pipeline_override = {}
    
    # 1. 任务级别的pipeline_override
    task_override = task_config.get('pipeline_override', {})
    pipeline_override.update(task_override)
    
    # 2. 选项级别的pipeline_override
    if option_values:
        for option_name, value in option_values.items():
            option_config = get_option_config(option_name)
            if option_config:
                # 根据选项类型处理
                option_type = option_config.get('type')
                
                if option_type == 'select':
                    # 选择类型：查找匹配的case
                    cases = option_config.get('cases', [])
                    for case in cases:
                        if case.get('name') == value:
                            case_override = case.get('pipeline_override', {})
                            pipeline_override.update(case_override)
                            break
                
                elif option_type == 'input':
                    # 输入类型：直接使用pipeline_override
                    inputs = option_config.get('inputs', [])
                    if inputs:
                        # 替换{input_name}占位符
                        override_str = json.dumps(option_config.get('pipeline_override', {}))
                        for inp in inputs:
                            input_name = inp.get('name')
                            if input_name in option_values:
                                placeholder = f"{{{input_name}}}"
                                override_str = override_str.replace(placeholder, str(option_values[input_name]))
                        pipeline_override.update(json.loads(override_str))
    
    return pipeline_override

def debug_task(task_name: str, option_values: dict = None):
    """
    调试任务
    
    Args:
        task_name: 任务名称
        option_values: 选项值
    """
    # 获取任务配置
    task_config = get_task_config(task_name)
    if not task_config:
        print(f"[Error] 任务不存在: {task_name}")
        return
    
    label = task_config.get('label')
    entry = task_config.get('entry')
    options = task_config.get('option', [])
    
    print("=" * 60)
    print(f"任务调试工具")
    print(f"任务: {task_name} - {label}")
    print(f"入口: {entry}")
    print("=" * 60)
    
    # 如果有选项但未提供值，提示用户
    if options and not option_values:
        print("\n该任务需要以下选项:")
        for opt_name in options:
            opt_config = get_option_config(opt_name)
            if opt_config:
                opt_label = opt_config.get('label', opt_name)
                opt_type = opt_config.get('type')
                
                print(f"\n  {opt_label} ({opt_name}):")
                
                if opt_type == 'select':
                    cases = opt_config.get('cases', [])
                    default_case = opt_config.get('default_case')
                    for case in cases:
                        case_name = case.get('name')
                        case_label = case.get('label')
                        marker = " (默认)" if case_name == default_case else ""
                        print(f"    - {case_name}: {case_label}{marker}")
                
                elif opt_type == 'input':
                    inputs = opt_config.get('inputs', [])
                    for inp in inputs:
                        inp_name = inp.get('name')
                        inp_default = inp.get('default', '')
                        print(f"    默认值: {inp_default}")
        
        print("\n使用 --option 参数指定选项值:")
        print(f"  python tools/debug_task.py {task_name} --option <option_name>=<value>")
        return
    
    # 构建pipeline_override
    pipeline_override = build_pipeline_override(task_config, option_values)
    
    if pipeline_override:
        print("\nPipeline参数覆盖:")
        print(json.dumps(pipeline_override, ensure_ascii=False, indent=2))
    
    # 加载资源
    resource_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'resource')
    res = Resource()
    job = res.post_bundle(resource_path)
    job.wait()
    
    if not job.succeeded:
        print("[Error] 资源加载失败")
        return
    
    print("\n[OK] 资源加载成功")
    
    # 查找游戏窗口
    print("\n正在查找游戏窗口...")
    hwnd = find_game_window()
    
    if not hwnd:
        print("[Error] 未找到游戏窗口")
        print("请确保游戏已启动，窗口标题包含'王者荣耀世界'")
        return
    
    print(f"[OK] 找到游戏窗口: hwnd={hwnd}")
    
    # 创建控制器
    ctrl = Win32Controller(
        hWnd=hwnd,
        screencap_method=MaaWin32ScreencapMethodEnum.FramePool,
        mouse_method=MaaWin32InputMethodEnum.SendMessage,
        keyboard_method=MaaWin32InputMethodEnum.SendMessage
    )
    
    # 连接控制器
    print("\n正在连接控制器...")
    job = ctrl.post_connection()
    job.wait()
    
    if not job.succeeded:
        print("[Error] 控制器连接失败")
        return
    
    print("[OK] 控制器连接成功")
    
    # 创建Tasker
    tasker = Tasker()
    tasker.bind(res, ctrl)
    
    # 启用调试模式
    tasker.set_debug_mode(True)
    print("[OK] 调试模式已启用")
    
    # 应用pipeline_override（在Resource上）
    if pipeline_override:
        res.override_pipeline(pipeline_override)
        print("[OK] 已应用参数覆盖")
    
    # 创建EventSink监听任务执行
    from maa.tasker import TaskerEventSink
    from maa.event_sink import NotificationType
    
    class DebugEventSink(TaskerEventSink):
        def on_tasker_task(self, tasker, noti_type, detail):
            if noti_type == NotificationType.TaskStarted:
                print(f"\n[Task Start] {detail.entry}")
            elif noti_type == NotificationType.TaskCompleted:
                print(f"[Task End] {detail.entry}")
            elif noti_type == NotificationType.TaskFailed:
                print(f"[Task Failed] {detail.entry}")
        
        def on_raw_notification(self, tasker, msg, details):
            # 输出节点执行信息
            if msg == "NodeHit":
                node_name = details.get('name', 'Unknown')
                print(f"  [Node] {node_name}: 命中 ✓")
            elif msg == "NodeMiss":
                node_name = details.get('name', 'Unknown')
                print(f"  [Node] {node_name}: 未命中 ✗")
            elif msg == "ActionRun":
                action_name = details.get('name', 'Unknown')
                print(f"  [Action] {action_name}")
    
    # 添加EventSink
    sink = DebugEventSink()
    tasker.add_sink(sink)
    
    print("\n" + "=" * 60)
    print("开始执行任务...")
    print("=" * 60 + "\n")
    
    # 运行任务
    try:
        job = tasker.post_task(entry)
        job.wait()
        
        print("\n" + "=" * 60)
        print("任务执行完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n[Error] 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MaaFramework任务调试工具")
    parser.add_argument('task', nargs='?', help='任务名称（如FarmPlant）')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用任务')
    parser.add_argument('--option', '-o', action='append', help='选项值（格式: option_name=value）')
    
    args = parser.parse_args()
    
    if args.list:
        list_tasks()
        sys.exit(0)
    
    if not args.task:
        print("用法:")
        print("  python tools/debug_task.py --list           # 列出所有任务")
        print("  python tools/debug_task.py <task_name>      # 调试任务")
        print("  python tools/debug_task.py <task_name> --option <name>=<value>  # 指定选项")
        print("\n示例:")
        print("  python tools/debug_task.py FarmPlant")
        print("  python tools/debug_task.py FarmPlant --option crop_name=冰魄辣椒")
        print("  python tools/debug_task.py FriendWatering --option friend_list_json='{\"friend_list\": [\"Trueman\"]}'")
        sys.exit(0)
    
    # 解析选项值
    option_values = {}
    if args.option:
        for opt_str in args.option:
            if '=' in opt_str:
                key, value = opt_str.split('=', 1)
                option_values[key] = value
    
    debug_task(args.task, option_values)