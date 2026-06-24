"""
自定义动作 - 领取派遣控制器
"""
import json
from maa.custom_action import CustomAction
from maa.context import Context
from utils.logger import log


class DispatchResultController:
    """
    领取派遣控制器（单例模式）
    
    管理当前处理的完成派遣index
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.current_index = 0
            instance.initialized = False
            cls._instance = instance
        return cls._instance
    
    def reset(self):
        """重置状态"""
        self.current_index = 0
        self.initialized = True
        log(f"[DispatchResult] 状态重置，index=0")
    
    def increment(self):
        """增加index"""
        self.current_index += 1
        log(f"[DispatchResult] index递增: {self.current_index}")


class SetDispatchResultIndex(CustomAction):
    """
    修改查找完成派遣的index号
    
    通过context.override_pipeline动态修改OCR的index参数
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = DispatchResultController()
        
        # 首次执行时重置
        if not controller.initialized:
            controller.reset()
        
        current_index = controller.current_index
        
        # 动态修改OCR的index参数
        override_data = {
            "领取派遣_查找完成派遣": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "roi": [70, 310, 210, 250],
                        "expected": ["完成派遣"],
                        "order_by": "Vertical",
                        "index": current_index
                    }
                }
            }
        }
        
        context.override_pipeline(override_data)
        log(f"[SetDispatchResultIndex] 设置查找index={current_index}")
        
        return True


class IncrementDispatchResultIndex(CustomAction):
    """
    index计数加一
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = DispatchResultController()
        controller.increment()
        return True