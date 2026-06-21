"""
自定义动作 - 晃动摇杆激活准星
"""
import json
import time
from maa.custom_action import CustomAction
from maa.context import Context
from logger import log
from custom_action import GamepadController


class WiggleStick(CustomAction):
    """晃动摇杆激活准星"""
    
    def run(self, context: Context, argv) -> bool:
        # 解析参数
        param = argv.custom_action_param if argv.custom_action_param else {}
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        stick_value = param.get('stick_value', 10000)
        duration = param.get('duration', 0.1)
        
        log(f"[WiggleStick] 晃动摇杆激活准星, 值={stick_value}, 持续时间={duration}s")
        
        controller = GamepadController()
        
        # 向右移动
        controller.set_left_stick(stick_value, 0)
        time.sleep(duration)
        controller.reset_sticks()
        time.sleep(0.1)
        
        # 向左移动
        controller.set_left_stick(-stick_value, 0)
        time.sleep(duration)
        controller.reset_sticks()
        time.sleep(0.1)
        
        log(f"[WiggleStick] 晃动完成")
        return True