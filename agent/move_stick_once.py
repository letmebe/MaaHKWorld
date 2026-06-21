"""
自定义动作 - 一次性推动摇杆
"""
import json
import time
from maa.custom_action import CustomAction
from maa.context import Context
from logger import log
from custom_action import GamepadController


class MoveStickOnce(CustomAction):
    """一次性推动摇杆"""
    
    def run(self, context: Context, argv) -> bool:
        log(f"[MoveStickOnce] 开始执行")
        
        # 解析参数（处理双重JSON编码）
        param = argv.custom_action_param
        log(f"[MoveStickOnce] 原始参数: {param}, 类型: {type(param)}")
        
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                log(f"[MoveStickOnce] 第一次解析: {parsed}, 类型: {type(parsed)}")
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                    log(f"[MoveStickOnce] 第二次解析: {param}")
                else:
                    param = parsed
            except Exception as e:
                log(f"[MoveStickOnce] 解析失败: {e}")
                param = {}
        
        stick = param.get('stick', 'left')
        x = param.get('x', 0)
        y = param.get('y', 0)
        duration = param.get('duration', 0.1)
        
        log(f"[MoveStickOnce] 参数: stick={stick}, x={x}, y={y}, duration={duration}s")
        
        controller = GamepadController()
        log(f"[MoveStickOnce] GamepadController已创建")
        
        # 设置摇杆位置
        if stick == 'left':
            log(f"[MoveStickOnce] 设置左摇杆: ({x}, {y})")
            controller.set_left_stick(x, y)
        else:
            log(f"[MoveStickOnce] 设置右摇杆: ({x}, {y})")
            controller.set_right_stick(x, y)
        
        # 等待
        log(f"[MoveStickOnce] 等待 {duration}s")
        time.sleep(duration)
        
        # 重置摇杆
        log(f"[MoveStickOnce] 重置摇杆")
        controller.reset_sticks()
        
        log(f"[MoveStickOnce] ✓ 完成")
        return True