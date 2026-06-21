"""
自定义动作 - 移动系统光标
"""
import json
import time
import math
import ctypes
from maa.custom_action import CustomAction
from maa.context import Context
from logger import log


class MoveCursor(CustomAction):
    """
    移动系统光标位置
    
    用于测试：通过操作系统光标位置控制游戏内准星位置
    """
    
    def __init__(self):
        super().__init__()
        self.user32 = ctypes.windll.user32
    
    def get_cursor_pos(self):
        """获取当前鼠标位置"""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    
    def set_cursor_pos(self, x, y):
        """设置鼠标位置"""
        self.user32.SetCursorPos(int(x), int(y))
    
    def run(self, context: Context, argv) -> bool:
        """
        执行光标移动
        
        Args:
            argv.custom_action_param: 参数
                - x: 目标X坐标
                - y: 目标Y坐标
        
        Returns:
            bool: True成功，False失败
        """
        param = argv.custom_action_param
        
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        target_x = param.get('x', 960)
        target_y = param.get('y', 540)
        
        try:
            self.set_cursor_pos(target_x, target_y)
            log(f"[MoveCursor] 光标移动到: ({target_x}, {target_y})")
            return True
        except Exception as e:
            log(f"[MoveCursor] 移动光标失败: {e}")
            return False


class MoveCursorSmooth(CustomAction):
    """
    平滑移动系统光标位置
    
    使用固定帧率（60fps）和缓动函数实现平滑移动
    """
    
    def __init__(self):
        super().__init__()
        self.user32 = ctypes.windll.user32
        self.fps = 60
        self.frame_delay = 1.0 / self.fps
    
    def get_cursor_pos(self):
        """获取当前鼠标位置"""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    
    def set_cursor_pos(self, x, y):
        """设置鼠标位置"""
        self.user32.SetCursorPos(int(x), int(y))
    
    def run(self, context: Context, argv) -> bool:
        """
        执行平滑光标移动
        
        Args:
            argv.custom_action_param: 参数
                - x: 目标X坐标
                - y: 目标Y坐标
                - duration: 移动总时间（秒），默认0.3
        
        Returns:
            bool: True成功，False失败
        """
        param = argv.custom_action_param
        
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        # 兼容两种参数名：x/y 或 target_x/target_y
        target_x = param.get('x', param.get('target_x', 960))
        target_y = param.get('y', param.get('target_y', 540))
        duration = param.get('duration', 0.3)
        
        try:
            # 获取当前光标位置
            start_x, start_y = self.get_cursor_pos()
            
            # 计算总距离
            distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
            
            # 如果距离太近（小于5像素），直接瞬移
            if distance < 5:
                self.set_cursor_pos(target_x, target_y)
                log(f"[MoveCursorSmooth] 距离太近，直接瞬移到: ({target_x}, {target_y})")
                return True
            
            # 根据总耗时和帧率，计算需要移动的总步数
            total_steps = max(1, int(duration * self.fps))
            
            log(f"[MoveCursorSmooth] 当前: ({start_x}, {start_y}), 目标: ({target_x}, {target_y}), 距离: {distance:.1f}px, 步数: {total_steps}")
            
            # 线性插值 + 缓动函数循环
            for step in range(1, total_steps + 1):
                # 计算当前进度的百分比 (0.0 到 1.0)
                progress = step / total_steps
                
                # 缓动函数：开始慢、中间快、结束慢
                progress = progress * progress * (3 - 2 * progress)
                
                # 线性插值公式: start + (target - start) * progress
                current_x = start_x + (target_x - start_x) * progress
                current_y = start_y + (target_y - start_y) * progress
                
                # 移动鼠标
                self.set_cursor_pos(current_x, current_y)
                
                # 输出当前位置日志
                #log(f"[MoveCursorSmooth] 步骤{step}/{total_steps}: ({int(current_x)}, {int(current_y)})")
                
                # 休眠，控制移动速度
                time.sleep(self.frame_delay)
            
            # 确保最终位置准确
            self.set_cursor_pos(target_x, target_y)
            log(f"[MoveCursorSmooth] 光标平滑移动完成: ({target_x}, {target_y})")
            return True
        except Exception as e:
            log(f"[MoveCursorSmooth] 移动光标失败: {e}")
            return False
