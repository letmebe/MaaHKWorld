"""
MaaFramework Pipeline调试工具
直接运行Pipeline并输出详细节点执行信息
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maa.context import Context
from maa.resource import Resource
from maa.controller import CustomController
import json

def debug_pipeline(pipeline_file: str, entry_task: str, task_param: dict = None):
    """
    调试Pipeline，输出每个节点的执行信息
    
    Args:
        pipeline_file: Pipeline JSON文件路径
        entry_task: 入口任务名称
        task_param: 任务参数（可选）
    """
    print("=" * 60)
    print(f"Pipeline调试工具")
    print(f"Pipeline文件: {pipeline_file}")
    print(f"入口任务: {entry_task}")
    if task_param:
        print(f"任务参数: {json.dumps(task_param, ensure_ascii=False, indent=2)}")
    print("=" * 60)
    
    # 加载资源
    resource_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'resource')
    res = Resource()
    job = res.post_bundle(resource_path)
    job.wait()
    
    if not job.succeeded:
        print("[Error] 资源加载失败")
        return
    
    print("[OK] 资源加载成功")
    
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
        screencap_method=18,  # FramePool
        mouse_method=3,       # SendMessage
        keyboard_method=3     # SendMessage
    )
    
    # 连接控制器
    print("\n正在连接控制器...")
    job = ctrl.post_connection()
    job.wait()
    
    if not job.succeeded:
        print("[Error] 控制器连接失败")
        return
    
    print("[OK] 控制器连接成功")
    
    # 创建上下文
    ctx = Context()
    ctx.bind(res)
    ctx.bind(ctrl)
    
    # 启用调试模式
    ctx.run_option.debug_mode = True
    print("[OK] 调试模式已启用")
    
    # 如果有参数，通过override_pipeline设置
    if task_param:
        override_data = {entry_task: task_param}
        ctx.override_pipeline(override_data)
        print(f"[OK] 已设置任务参数")
    
    # 设置回调函数，输出节点执行信息
    def on_task_start(task_name):
        print(f"\n[Task Start] {task_name}")
    
    def on_task_completed(task_name, result):
        print(f"[Task End] {task_name}")
        if result:
            print(f"  - 结果: {result}")
    
    def on_recognition(recognition_name, hit):
        status = "命中 ✓" if hit else "未命中 ✗"
        print(f"  [Recognition] {recognition_name}: {status}")
    
    def on_action(action_name):
        print(f"  [Action] {action_name}")
    
    # 注册回调
    ctx.on_task_start += on_task_start
    ctx.on_task_completed += on_task_completed
    ctx.on_recognition += on_recognition
    ctx.on_action += on_action
    
    print("\n" + "=" * 60)
    print("开始执行Pipeline...")
    print("=" * 60 + "\n")
    
    # 运行任务
    try:
        result = ctx.run_task(entry_task)
        print("\n" + "=" * 60)
        print("Pipeline执行完成")
        print("=" * 60)
        print(f"最终结果: {result}")
    except Exception as e:
        print(f"\n[Error] 执行失败: {e}")
        import traceback
        traceback.print_exc()

def list_pipeline_nodes(pipeline_file: str):
    """
    列出Pipeline中的所有节点
    
    Args:
        pipeline_file: Pipeline JSON文件路径
    """
    print("=" * 60)
    print(f"Pipeline节点列表")
    print(f"文件: {pipeline_file}")
    print("=" * 60)
    
    with open(pipeline_file, 'r', encoding='utf-8') as f:
        pipeline = json.load(f)
    
    for node_name, node_config in pipeline.items():
        recognition = node_config.get('recognition', 'N/A')
        action = node_config.get('action', 'N/A')
        next_nodes = node_config.get('next', [])
        
        print(f"\n节点: {node_name}")
        print(f"  识别: {recognition}")
        print(f"  动作: {action}")
        if next_nodes:
            print(f"  下一步: {next_nodes}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MaaFramework Pipeline调试工具")
    parser.add_argument('command', choices=['run', 'list'], help='命令: run(运行) 或 list(列出节点)')
    parser.add_argument('--pipeline', '-p', help='Pipeline文件路径')
    parser.add_argument('--task', '-t', help='入口任务名称')
    parser.add_argument('--param', help='任务参数（JSON字符串或JSON文件路径）')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        if not args.pipeline:
            print("[Error] 请指定Pipeline文件: --pipeline <file>")
            sys.exit(1)
        list_pipeline_nodes(args.pipeline)
    
    elif args.command == 'run':
        if not args.pipeline or not args.task:
            print("[Error] 请指定Pipeline文件和入口任务:")
            print("  --pipeline <file> --task <task_name>")
            sys.exit(1)
        
        # 解析参数
        task_param = None
        if args.param:
            # 尝试作为JSON文件读取
            if os.path.exists(args.param):
                with open(args.param, 'r', encoding='utf-8') as f:
                    task_param = json.load(f)
            else:
                # 作为JSON字符串解析
                try:
                    task_param = json.loads(args.param)
                except json.JSONDecodeError:
                    print(f"[Error] 参数格式错误，应为JSON字符串或JSON文件路径")
                    sys.exit(1)
        
        debug_pipeline(args.pipeline, args.task, task_param)