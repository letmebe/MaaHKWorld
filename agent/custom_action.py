"""
自定义动作模块 - 虚拟手柄控制
"""
import time
import json
from pathlib import Path
from typing import Optional
from maa.context import Context
from maa.custom_action import CustomAction

try:
    import vgamepad as vg
    _VG_AVAILABLE = True
except ImportError:
    vg = None
    _VG_AVAILABLE = False

try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import win32com.client
    _WIN32_AVAILABLE = True
except ImportError:
    win32gui = None
    win32con = None
    win32api = None
    win32process = None
    win32com = None
    _WIN32_AVAILABLE = False


def _force_foreground_window(hwnd: int):
    """强制将窗口置于前台 - 多层尝试方法"""
    import ctypes
    user32 = ctypes.windll.user32
    
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)
    
    # 方法1: 简单方法
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        if user32.GetForegroundWindow() == hwnd:
            return
    except Exception:
        pass
    
    # 方法2: ALT键技巧
    try:
        import pythoncom
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        if user32.GetForegroundWindow() == hwnd:
            return
    except Exception as e:
        print(f"[Window] SendKeys 激活失败: {e}")
    
    # 方法3: AttachThreadInput
    try:
        foreground_thread_id = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        
        current_thread_id = win32api.GetCurrentThreadId()
        
        # 附加当前线程到目标窗口线程
        if current_thread_id != foreground_thread_id:
            user32.AttachThreadInput(current_thread_id, foreground_thread_id, True)
        if current_thread_id != target_thread_id:
            user32.AttachThreadInput(current_thread_id, target_thread_id, True)
        
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        if current_thread_id != target_thread_id:
            user32.AttachThreadInput(current_thread_id, target_thread_id, False)
        if current_thread_id != foreground_thread_id:
            user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
        
        time.sleep(0.2)
    except Exception as e:
        print(f"[Window] AttachThreadInput 激活失败: {e}")


class GamepadController:
    """虚拟手柄控制器"""
    
    _instance: Optional['GamepadController'] = None
    _gamepad = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_gamepad()
        return cls._instance
    
    def _init_gamepad(self):
        """初始化虚拟手柄"""
        if not _VG_AVAILABLE:
            print("[Gamepad] vgamepad 未安装")
            self._gamepad = None
            return
        
        try:
            self._gamepad = vg.VX360Gamepad()
            print("[Gamepad] 虚拟手柄初始化成功")
        except Exception as e:
            print(f"[Gamepad] 虚拟手柄初始化失败: {e}")
            self._gamepad = None
    
    def tap_button(self, button: str, duration: float = 0.1):
        """点击按钮"""
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        button_id_map = {
            'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            'LEFT_THUMB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            'RIGHT_THUMB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            'DPAD_UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            'DPAD_DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            'DPAD_LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            'DPAD_RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        
        if button in button_id_map:
            self._gamepad.press_button(button_id_map[button])
            self._gamepad.update()
            time.sleep(duration)
            self._gamepad.release_button(button_id_map[button])
            self._gamepad.update()
    
    def quick_tap(self, button: str, count: int = 2, interval: float = 0.05):
        """快速连点"""
        for _ in range(count):
            self.tap_button(button, duration=0.05)
            time.sleep(interval)
    
    def long_press(self, button: str, duration: float = 3.0):
        """长按按钮"""
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        button_id_map = {
            'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        }
        
        if button in button_id_map:
            self._gamepad.press_button(button_id_map[button])
            self._gamepad.update()
            time.sleep(duration)
            self._gamepad.release_button(button_id_map[button])
            self._gamepad.update()
    
    def jump_forward(self, stick_y: int = 30000, stick_duration: float = 0.3):
        """
        前跳动作：按住左摇杆前进的同时，按A键跳跃
        
        Args:
            stick_y: 前进摇杆值，默认30000
            stick_duration: 摇杆持续时间，默认0.3秒
        """
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        # 限制摇杆值范围
        stick_y = max(-32768, min(32767, stick_y))
        
        # 1. 按住跳跃键和左摇杆前进（同时生效）
        self._gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self._gamepad.left_joystick(x_value=0, y_value=stick_y)
        self._gamepad.update()
        
        # 2. 继续按住摇杆和跳跃键一段时间
        time.sleep(stick_duration)
        
        # 3. 松开A键和摇杆（同时生效）
        self._gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self._gamepad.left_joystick(x_value=0, y_value=0)
        self._gamepad.update()
    
    def set_left_stick(self, x: int, y: int):
        """
        设置左摇杆位置
        
        Args:
            x: X轴值 (-32768 ~ 32767), 负值向左，正值向右
            y: Y轴值 (-32768 ~ 32767), 正值向上，负值向下
        """
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        x = max(-32768, min(32767, x))
        y = max(-32768, min(32767, y))
        
        self._gamepad.left_joystick(x_value=x, y_value=y)
        self._gamepad.update()
    
    def set_right_stick(self, x: int, y: int):
        """
        设置右摇杆位置
        
        Args:
            x: X轴值 (-32768 ~ 32767), 负值向左，正值向右
            y: Y轴值 (-32768 ~ 32767), 正值向上，负值向下
        """
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        x = max(-32768, min(32767, x))
        y = max(-32768, min(32767, y))
        
        self._gamepad.right_joystick(x_value=x, y_value=y)
        self._gamepad.update()

    
    def reset_sticks(self):
        """重置所有摇杆到中心位置"""
        if not self._gamepad or not _VG_AVAILABLE:
            return
        
        self._gamepad.left_joystick(x_value=0, y_value=0)
        self._gamepad.right_joystick(x_value=0, y_value=0)
        self._gamepad.update()


class ActivateGameWindow(CustomAction):
    """激活游戏窗口"""
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        log("[Window] Activating game window...")
        
        if not _WIN32_AVAILABLE:
            log("[Window] win32gui not available, skipping")
            return True
        
        try:
            import ctypes
            
            hwnd = win32gui.FindWindow("UnrealWindow", "王者荣耀世界")
            if not hwnd:
                log("[Window] Game window not found")
                return True
            
            log(f"[Window] Found game window: HWND={hwnd}")
            
            # Method 1: Minimize then restore (make window screenshot-ready)
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                time.sleep(0.1)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)
            except Exception as e:
                log(f"[Window] ShowWindow failed: {e}")
            
            # Method 2: Try to set foreground (may cause taskbar flash)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            
            log("[Window] Game window activated")
            time.sleep(0.5)
            
        except Exception as e:
            log(f"[Window] Failed to activate window: {e}")
        
        return True


class ActivateGamepad(CustomAction):
    """激活游戏手柄模式"""
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        log("[Gamepad] Activating virtual gamepad mode...")
        
        controller = GamepadController()
        
        controller.tap_button('A', duration=0.1)
        time.sleep(0.3)
        controller.tap_button('A', duration=0.1)
        time.sleep(0.5)
        
        log("[Gamepad] Virtual gamepad mode activated")
        return True


class TestGamepadButtons(CustomAction):
    """测试手柄按键"""
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        log("[Test] 开始测试手柄按键...")
        
        controller = GamepadController()
        if not controller._gamepad:
            log("[Test] 手柄未初始化")
            return False
        
        # 测试各个按键
        buttons = ['A', 'B', 'X', 'Y']
        
        for button in buttons:
            log(f"[Test] 点击按键 {button}")
            controller.tap_button(button, duration=0.2)
            time.sleep(0.5)
        
        log("[Test] 手柄按键测试完成")
        return True


class TestGamepadSticks(CustomAction):
    """测试摇杆移动"""
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        log("[Test] 开始测试摇杆移动...")
        
        controller = GamepadController()
        if not controller._gamepad:
            log("[Test] 手柄未初始化")
            return False
        
        # 测试左摇杆
        log("[Test] 测试左摇杆")
        
        # 向右
        log("[Test] 左摇杆向右")
        controller.set_left_stick(20000, 0)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向左
        log("[Test] 左摇杆向左")
        controller.set_left_stick(-20000, 0)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向上
        log("[Test] 左摇杆向上")
        controller.set_left_stick(0, -20000)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向下
        log("[Test] 左摇杆向下")
        controller.set_left_stick(0, 20000)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 测试右摇杆
        log("[Test] 测试右摇杆")
        
        # 向右
        log("[Test] 右摇杆向右")
        controller.set_right_stick(20000, 0)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向左
        log("[Test] 右摇杆向左")
        controller.set_right_stick(-20000, 0)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向上
        log("[Test] 右摇杆向上")
        controller.set_right_stick(0, -20000)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        # 向下
        log("[Test] 右摇杆向下")
        controller.set_right_stick(0, 20000)
        time.sleep(1.0)
        controller.reset_sticks()
        time.sleep(0.5)
        
        log("[Test] 摇杆测试完成")
        return True


class TestStickAim(CustomAction):
    """测试摇杆瞄准到指定坐标"""
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        log('[Test] 摇杆瞄准测试已迁移到 test/test_aim_with_calibration.py')
        log('[Test] 请运行: python test/test_aim_with_calibration.py')
        return True



class TapButton(CustomAction):
    """点击手柄按钮"""
    
    def run(self, context: Context, argv) -> bool:
        import json
        from logger import log
        
        log(f"[TapButton] 开始执行, argv类型: {type(argv)}")
        log(f"[TapButton] argv内容: {argv}")
        
        # 解析参数
        params = {}  # 先初始化
        try:
            if hasattr(argv, 'custom_action_param'):
                param_str = argv.custom_action_param
                log(f"[TapButton] custom_action_param: {param_str}, 类型: {type(param_str)}")
                log(f"[TapButton] 开始解析JSON...")
                
                # 检查param_str是否已经是字典
                if isinstance(param_str, dict):
                    params = param_str
                    log(f"[TapButton] param_str已经是字典: {params}")
                else:
                    # 第一次解析
                    parsed = json.loads(param_str) if param_str else {}
                    log(f"[TapButton] 第一次JSON解析: {parsed}, 类型: {type(parsed)}")
                    
                    # 如果结果是字符串，需要再次解析（双重编码）
                    if isinstance(parsed, str):
                        params = json.loads(parsed)
                        log(f"[TapButton] 第二次JSON解析: {params}, 类型: {type(params)}")
                    else:
                        params = parsed
            else:
                log(f"[TapButton] 无custom_action_param属性，尝试直接解析argv")
                params = json.loads(argv) if argv else {}
        except Exception as e:
            log(f"[TapButton] 参数解析失败: {e}")
            import traceback
            log(f"[TapButton] 异常堆栈:\n{traceback.format_exc()}")
            params = {}
        
        log(f"[TapButton] try块结束，params={params}, 类型={type(params)}")
        
        log(f"[TapButton] 准备获取button参数")
        button = params.get('button', 'A')
        log(f"[TapButton] button={button}")
        
        log(f"[TapButton] 准备获取duration参数")
        duration = params.get('duration', 0.1)
        log(f"[TapButton] duration={duration}")
        
        # 强制立即输出到日志和控制台
        import sys
        msg1 = f"[TapButton] 解析结果 - 按钮: {button}, 持续时间: {duration}s"
        log(msg1)
        print(msg1, flush=True)
        
        try:
            controller = GamepadController()
            msg2 = f"[TapButton] GamepadController已创建"
            log(msg2)
            print(msg2, flush=True)
            
            controller.tap_button(button, duration)
            msg3 = f"[TapButton] tap_button已调用"
            log(msg3)
            print(msg3, flush=True)
        except Exception as e:
            msg4 = f"[TapButton] 执行异常: {e}"
            log(msg4)
            print(msg4, flush=True)
            import traceback
            log(f"[TapButton] 异常堆栈:\n{traceback.format_exc()}")
        
        msg5 = f"[TapButton] 执行完成"
        log(msg5)
        print(msg5, flush=True)
        return True


class AimAndClick(CustomAction):
    """将准星移动到识别目标位置并点击"""
    
    def __init__(self):
        super().__init__()
        self.controller = GamepadController()
    
    def run(self, context: Context, argv) -> bool:
        import json
        from logger import log
        from stick_calibration_map import find_stick_params_for_axis
        
        log(f"[AimAndClick] 开始执行")
        
        # 获取识别结果
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[AimAndClick] 无识别结果")
            return False
        
        log(f"[AimAndClick] reco_detail类型: {type(reco_detail)}")
        
        # 从raw_detail获取目标位置
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[AimAndClick] 无识别detail")
            return False
        
        log(f"[AimAndClick] detail_dict: {detail_dict}")
        
        best = detail_dict.get('best', {})
        log(f"[AimAndClick] best: {best}")
        
        box = best.get('box', [])
        log(f"[AimAndClick] box: {box}")
        
        if not box or len(box) < 4:
            log("[AimAndClick] 无目标位置")
            return False
        
        # OCR返回的box格式是[x, y, w, h]，需要转换为中心点
        x, y, w, h = box[0], box[1], box[2], box[3]
        target_x = x + w // 2
        target_y = y + h // 2
        
        log(f"[AimAndClick] box解析: x={x}, y={y}, w={w}, h={h}")
        log(f"[AimAndClick] 目标中心点: ({target_x}, {target_y})")
        
        # 解析参数
        params = {}
        try:
            if hasattr(argv, 'custom_action_param'):
                param_str = argv.custom_action_param
                if param_str:
                    # 第一次解析
                    parsed = json.loads(param_str)
                    # 如果结果是字符串，需要再次解析（双重编码）
                    if isinstance(parsed, str):
                        params = json.loads(parsed)
                    else:
                        params = parsed
        except Exception as e:
            log(f"[AimAndClick] 参数解析失败: {e}")
            params = {}
        
        button = params.get('button', 'A')
        tolerance = params.get('tolerance', 10)
        max_iterations = params.get('max_iterations', 15)
        
        log(f"[AimAndClick] 参数: 按钮={button}, 容差={tolerance}px, 最大迭代={max_iterations}")
        log(f"[AimAndClick] 开始瞄准循环...")
        
        # 先晃动摇杆让准星显示出来
        log(f"[AimAndClick] 晃动摇杆激活准星...")
        self.controller.set_left_stick(10000, 0)
        time.sleep(0.1)
        self.controller.reset_sticks()
        time.sleep(0.2)
        
        # 瞄准循环
        for iteration in range(max_iterations):
            log(f"[AimAndClick] === 迭代 {iteration+1}/{max_iterations} ===")
            # 获取准星位置（需要调用准星识别）
            from crosshair_recognition import FindCrosshairRecognition
            import cv2
            import numpy as np
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab(bbox=(0, 0, 1920, 1080))
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            class MockArgv:
                def __init__(self, image, param=None):
                    self.image = image
                    self.custom_recognition_param = param or {}
            
            recognition = FindCrosshairRecognition()
            result = recognition.analyze(None, MockArgv(image, {'threshold': 0.8}))
            
            if not result or not hasattr(result, 'detail'):
                log(f"[AimAndClick] 迭代{iteration+1}: 未找到准星")
                time.sleep(0.1)
                continue
            
            cx = result.detail.get('center_x')
            cy = result.detail.get('center_y')
            
            if cx is None or cy is None:
                log(f"[AimAndClick] 迭代{iteration+1}: 准星位置无效")
                time.sleep(0.1)
                continue
            
            # 计算偏移
            dx = target_x - cx
            dy = target_y - cy
            distance = (dx*dx + dy*dy) ** 0.5
            
            log(f"[AimAndClick] 迭代{iteration+1}: 准星({cx}, {cy}), 距离={distance:.1f}px")
            
            # 检查是否到达目标
            if distance < tolerance:
                log(f"[AimAndClick] ✓ 瞄准完成! 距离={distance:.1f}px")
                
                # 点击按钮
                self.controller.tap_button(button, 0.1)
                log(f"[AimAndClick] 点击按钮: {button}")
                
                return True
            
            # 查询摇杆参数
            log(f"[AimAndClick] 查询摇杆参数: dx={dx}, dy={dy}")
            result = find_stick_params_for_axis(dx, dy)
            if not result:
                log(f"[AimAndClick] 无法找到合适的摇杆参数")
                return False
            
            stick_x, stick_y, duration, actual_dist = result
            
            # 反转Y轴
            stick_y = -stick_y
            
            log(f"[AimAndClick] 移动摇杆: ({stick_x}, {stick_y}), 持续时间={duration}s")
            
            # 移动摇杆
            self.controller.set_left_stick(stick_x, stick_y)
            time.sleep(duration)
            self.controller.reset_sticks()
            time.sleep(0.1)
            
            log(f"[AimAndClick] 摇杆移动完成")
        
        log(f"[AimAndClick] ✗ 达到最大迭代次数{max_iterations}")
        return False


class JumpForward(CustomAction):
    """
    前跳动作：按住左摇杆前进的同时，按A键跳跃
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        from logger import log
        
        log(f"[JumpForward] 开始执行")
        
        # 解析参数
        param = argv.custom_action_param if hasattr(argv, 'custom_action_param') else {}
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        # 获取参数
        stick_y = param.get('stick_y', 30000)  # 前进摇杆值，默认30000
        stick_duration = param.get('stick_duration', 0.3)  # 摇杆持续时间
        
        log(f"[JumpForward] 参数: stick_y={stick_y}, stick_duration={stick_duration}s")
        
        try:
            controller = GamepadController()
            controller.jump_forward(stick_y, stick_duration)
            log(f"[JumpForward] ✓ 完成")
            return True
        except Exception as e:
            log(f"[JumpForward] 执行异常: {e}")
            return False
