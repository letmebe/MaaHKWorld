"""
Agent 服务 - 注册自定义动作和识别器
"""
import sys
import os
import threading
import queue
from datetime import datetime
from pathlib import Path
from maa.agent.agent_server import AgentServer
from custom_action import (
    GamepadController,
    ActivateGameWindow,
    ActivateGamepad,
)
from fishing_recognition import FishingMultiMatchRecognition
from fishing_action import FishingMultiMatchAction

# ========== 统一日志系统 ==========
LOG_QUEUE: queue.Queue = queue.Queue()
LOG_FILE = Path(__file__).parent / 'logs' / 'agent.log'
_log_thread = None
_log_running = False

def _log_writer():
    """后台线程：从队列取日志写入文件"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8', buffering=8192) as f:
        while _log_running:
            try:
                msg = LOG_QUEUE.get(timeout=0.5)
                if msg is None:  # 停止信号
                    break
                f.write(msg)
                f.flush()
            except queue.Empty:
                continue

def log(message: str):
    """日志输出 - 放入队列，后台线程写入"""
    global _log_thread, _log_running
    
    # 首次调用时启动日志线程
    if _log_thread is None:
        _log_running = True
        _log_thread = threading.Thread(target=_log_writer, daemon=True)
        _log_thread.start()
    
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {message}\n"
    
    # 同时输出到 stdout 和队列
    print(message)
    sys.stdout.flush()
    LOG_QUEUE.put(full_msg)

# ===================================


def register_custom_actions():
    """注册所有自定义动作"""
    
    AgentServer.register_custom_action("ActivateGameWindow", ActivateGameWindow())
    AgentServer.register_custom_action("ActivateGamepad", ActivateGamepad())
    AgentServer.register_custom_action("FishingMultiMatchAction", FishingMultiMatchAction())
    
    log("[Agent] 自定义动作注册完成")


def register_custom_recognitions():
    """注册所有自定义识别器"""
    
    AgentServer.register_custom_recognition("FishingMultiMatch", FishingMultiMatchRecognition())
    
    log("[Agent] 自定义识别器注册完成")


def start_agent_server(sock_id: str = "maa-fisher-agent"):
    """启动 Agent 服务"""
    
    log("=" * 50)
    log("[Agent] 启动 Agent 服务")
    log(f"[Agent] Socket ID: {sock_id}")
    log("=" * 50)
    
    # 初始化虚拟手柄（不立即激活）
    log("[Agent] 初始化虚拟手柄...")
    gamepad = GamepadController()
    log("[Agent] 虚拟手柄已就绪")
    
    # 注册自定义动作
    register_custom_actions()
    
    # 注册自定义识别器
    register_custom_recognitions()
    
    # 启动 Agent 服务
    AgentServer.start_up(sock_id)
    log(f"[Agent] Agent 服务已启动: {sock_id}")
    
    # 保持运行，等待调用
    log("[Agent] Agent 服务运行中，等待调用...")
    log("=" * 50)
    AgentServer.join()
