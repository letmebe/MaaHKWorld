"""
自定义动作 - 处理多模板匹配结果
根据识别结果执行对应的操作
"""
import time
import json
from maa.custom_action import CustomAction
from maa.context import Context

from custom_action import GamepadController
from logger import log  # 使用统一的日志函数


class FishingMultiMatchAction(CustomAction):
    """
    处理多模板匹配结果
    根据识别结果detail执行对应操作
    """
    
    def __init__(self):
        super().__init__()
        self.controller = GamepadController()
        self._last_time = {}
        self._cooldown = {
            'paogan': 2.0,
            'lagan': 2.0,
            'X_quick': 0.2,
            'quick_B': 0.2,
            'X_single': 0.5,
            'Y_single': 0.5,
            'A_single': 0.5,
            'B_single': 0.5,
            'to_bag': 0.5,
            'fanui': 0.5,
            'quxiaozhunbei': 10.0,
        }
        self._quxiaozhunbei_executed = False
        self._cast_count = 0
    
    def _check_cooldown(self, name: str) -> bool:
        now = time.time()
        last = self._last_time.get(name, 0)
        cd = self._cooldown.get(name, 0)
        return now - last >= cd
    
    def _update_cooldown(self, name: str):
        self._last_time[name] = time.time()
    
    def run(self, context: Context, argv) -> bool:
        """执行动作"""
        t_start = time.perf_counter()
        
        # 从 argv 获取识别结果
        reco_detail = argv.reco_detail
        
        if not reco_detail:
            log("[FishingAction] 无识别结果")
            return True  # 继续循环
        
        # 从 raw_detail 获取 - 结构是 {'best': {'detail': {...}}}
        detail_dict = reco_detail.raw_detail
        
        if not detail_dict:
            log("[FishingAction] 无识别detail")
            return True  # 继续循环
        
        # 从 best.detail 获取自定义字段
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        if not detail:
            log("[FishingAction] detail 为空")
            return True  # 继续循环
        
        name = detail.get('name')
        action = detail.get('action')
        score = detail.get('score', 0)
        
        # 特殊动作：跳过（取消状态）
        if action == 'skip':
            return True
        
        # 检查冷却（冷却中跳过但继续循环）
        if not self._check_cooldown(name):
            return True
        
        # 特殊处理：取消准备只执行一次
        if name == 'quxiaozhunbei':
            if self._quxiaozhunbei_executed:
                return True  # 已执行过，跳过但继续循环
            self._quxiaozhunbei_executed = True
        
        # 执行对应动作
        executed = False
        
        if action == 'tap_A':
            self.controller.tap_button('A')
            if name in ['paogan', 'lagan']:
                self._cast_count += 1
            executed = True
        
        elif action == 'tap_X':
            self.controller.tap_button('X')
            executed = True
        
        elif action == 'tap_Y':
            self.controller.tap_button('Y')
            executed = True
        
        elif action == 'tap_B':
            self.controller.tap_button('B')
            executed = True
        
        elif action == 'quick_tap_X':
            self.controller.quick_tap('X', count=2)
            executed = True
        
        elif action == 'quick_tap_B':
            self.controller.quick_tap('B', count=2)
            executed = True
        
        elif action == 'long_press_START':
            self.controller.long_press('START', duration=3.0)
            executed = True
        
        # 更新冷却
        if executed:
            self._update_cooldown(name)
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Action] {name} → {action} | 耗时: {t_elapsed:.1f}ms")
        
        return True  # 始终返回 True 以继续循环
