"""
Agent 服务 - 注册自定义动作和识别器
"""
import sys
import os
from maa.agent.agent_server import AgentServer
from utils.common_action import (
    GamepadController,
    ActivateGameWindow,
    ActivateGamepad,
    TestGamepadButtons,
    TestGamepadSticks,
    TestStickAim,
    TapButton,
    AimAndClick,
    JumpForward,
    MoveStickOnce,
    WiggleStick,
    MoveStickAction,
    ExtractOCRTarget,
    MoveCursor,
    MoveCursorSmooth,
)

from controller.fishing import FishingMultiMatchRecognition, FishingMultiMatchAction
from utils.common_recognition import FindCrosshairRecognition, FindCrosshairNearTargetRecognition
from controller.dispatch import DispatchLoopController, CheckLocationCount, CheckPersonCount
from controller.dispatch_result import SetDispatchResultIndex, IncrementDispatchResultIndex
from controller.herb import (
    HerbPlantController,
    CheckPlantCount,
    IncrementPlantCount,
    ParseWateringTime,
    SaveWateringTime,
    ResetHerbPlant,
    CheckTilledField,
    IncrementPlantCountIfHit,
    CheckWateringTimeText,
    ParseWateringTimeIfHit,
)

from controller.friend_list import (
    InitFriendList, 
    CheckCurrentFriend, 
    CheckMoreFriends, 
    NextFriend,
    OpenFriendMenu, 
    GoHome,
    CheckWateringButtonByOCR,
    MoveCursorToWateringButton,
    CheckWateredField,
    IncrementWaterCountIfHit,
    CheckWaterCount
)
from utils.logger import log, start_log_thread


def register_custom_actions():
    """注册所有自定义动作"""
    
    AgentServer.register_custom_action("ActivateGameWindow", ActivateGameWindow())
    AgentServer.register_custom_action("ActivateGamepad", ActivateGamepad())
    AgentServer.register_custom_action("FishingMultiMatchAction", FishingMultiMatchAction())
    AgentServer.register_custom_action("TestGamepadButtons", TestGamepadButtons())
    AgentServer.register_custom_action("TestGamepadSticks", TestGamepadSticks())
    AgentServer.register_custom_action("TestStickAim", TestStickAim())
    AgentServer.register_custom_action("MoveStick", MoveStickAction())
    AgentServer.register_custom_action("TapButton", TapButton())
    AgentServer.register_custom_action("AimAndClick", AimAndClick())
    AgentServer.register_custom_action("ExtractOCRTarget", ExtractOCRTarget())
    AgentServer.register_custom_action("WiggleStick", WiggleStick())
    AgentServer.register_custom_action("MoveStickOnce", MoveStickOnce())
    AgentServer.register_custom_action("MoveCursor", MoveCursor())
    AgentServer.register_custom_action("MoveCursorSmooth", MoveCursorSmooth())
    AgentServer.register_custom_action("DispatchLoopController", DispatchLoopController())
    AgentServer.register_custom_action("IncrementPlantCount", IncrementPlantCount())
    AgentServer.register_custom_action("ParseWateringTime", ParseWateringTime())
    AgentServer.register_custom_action("SaveWateringTime", SaveWateringTime())
    AgentServer.register_custom_action("ResetHerbPlant", ResetHerbPlant())
    AgentServer.register_custom_action("IncrementPlantCountIfHit", IncrementPlantCountIfHit())
    AgentServer.register_custom_action("ParseWateringTimeIfHit", ParseWateringTimeIfHit())
    AgentServer.register_custom_action("SetDispatchResultIndex", SetDispatchResultIndex())
    AgentServer.register_custom_action("IncrementDispatchResultIndex", IncrementDispatchResultIndex())
    AgentServer.register_custom_action("JumpForward", JumpForward())
    AgentServer.register_custom_action("OpenFriendMenu", OpenFriendMenu())
    AgentServer.register_custom_action("GoHome", GoHome())

    AgentServer.register_custom_action("MoveCursorToWateringButton", MoveCursorToWateringButton())
    AgentServer.register_custom_action("NextFriend", NextFriend())
    AgentServer.register_custom_action("CheckCurrentFriend", CheckCurrentFriend())
    AgentServer.register_custom_action("InitFriendList", InitFriendList())
    AgentServer.register_custom_action("IncrementWaterCountIfHit", IncrementWaterCountIfHit())



    
    log("[Agent] Custom actions registered")


def register_custom_recognitions():
    """注册所有自定义识别器"""
    
    AgentServer.register_custom_recognition("FishingMultiMatch", FishingMultiMatchRecognition())
    AgentServer.register_custom_recognition("FindCrosshair", FindCrosshairRecognition())
    AgentServer.register_custom_recognition("FindCrosshairNearTarget", FindCrosshairNearTargetRecognition())
    AgentServer.register_custom_recognition("CheckLocationCount", CheckLocationCount())
    AgentServer.register_custom_recognition("CheckPersonCount", CheckPersonCount())
    AgentServer.register_custom_recognition("CheckPlantCount", CheckPlantCount())
    AgentServer.register_custom_recognition("CheckTilledField", CheckTilledField())
    AgentServer.register_custom_recognition("CheckWateringTimeText", CheckWateringTimeText())

    AgentServer.register_custom_recognition("CheckMoreFriends", CheckMoreFriends())
    AgentServer.register_custom_recognition("CheckWateringButtonByOCR", CheckWateringButtonByOCR())
    AgentServer.register_custom_recognition("CheckWateredField", CheckWateredField())
    AgentServer.register_custom_recognition("CheckWaterCount", CheckWaterCount())

    
    log("[Agent] Custom recognitions registered")


def start_agent_server(sock_id: str = "maa-hkworld-agent"):
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
