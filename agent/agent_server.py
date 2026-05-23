"""
Agent 服务 - 注册自定义动作和识别器
"""
import sys
import os
from maa.agent.agent_server import AgentServer
from custom_action import (
    GamepadController,
    ActivateGameWindow,
    ActivateGamepad,
)
from fishing_recognition import FishingMultiMatchRecognition
from fishing_action import FishingMultiMatchAction
from logger import log, start_log_thread


def register_custom_actions():
    """注册所有自定义动作"""
    
    AgentServer.register_custom_action("ActivateGameWindow", ActivateGameWindow())
    AgentServer.register_custom_action("ActivateGamepad", ActivateGamepad())
    AgentServer.register_custom_action("FishingMultiMatchAction", FishingMultiMatchAction())
    
    log("[Agent] Custom actions registered")


def register_custom_recognitions():
    """注册所有自定义识别器"""
    
    AgentServer.register_custom_recognition("FishingMultiMatch", FishingMultiMatchRecognition())
    
    log("[Agent] Custom recognitions registered")


def start_agent_server(sock_id: str = "maa-fisher-agent"):
    """启动 Agent 服务"""
    
    # 启动日志线程
    start_log_thread()
    
    log("=" * 50)
    log("[Agent] Starting Agent Server")
    log(f"[Agent] Socket ID: {sock_id}")
    log("=" * 50)
    
    # 初始化虚拟手柄（不立即激活）
    log("[Agent] Initializing virtual gamepad...")
    gamepad = GamepadController()
    log("[Agent] Virtual gamepad ready")
    
    # 注册自定义动作
    register_custom_actions()
    
    # 注册自定义识别器
    register_custom_recognitions()
    
    # 启动 Agent 服务
    AgentServer.start_up(sock_id)
    log(f"[Agent] Agent server started: {sock_id}")
    
    # 保持运行，等待调用
    log("[Agent] Agent server running, waiting for calls...")
    log("=" * 50)
    AgentServer.join()
