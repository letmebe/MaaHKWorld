"""
自定义动作模块 - 虚拟手柄控制
"""
import time
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
            # 测试：按下一个按钮验证手柄工作
            self._gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            self._gamepad.update()
            time.sleep(0.05)
            self._gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            self._gamepad.update()
            print("[Gamepad] 测试输入已发送")
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
        }
        
        if button in button_id_map:
            self._gamepad.press_button(button_id_map[button])
            self._gamepad.update()
            time.sleep(duration)
            self._gamepad.release_button(button_id_map[button])
            self._gamepad.update()
    
    def quick_tap(self, button: str, count: int = 4, interval: float = 0.05):
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


class ActivateGameWindow(CustomAction):
    """激活游戏窗口"""
    
    _activated = False
    
    def run(self, context: Context, argv) -> bool:
        if self._activated:
            return True
        
        from logger import log
        log("[Window] Activating game window...")
        
        if not _WIN32_AVAILABLE:
            log("[Window] win32gui not available, skipping")
            self._activated = True
            return True
        
        try:
            hwnd = win32gui.FindWindow("UnrealWindow", "王者荣耀世界")
            if not hwnd:
                log("[Window] Game window not found")
                self._activated = True
                return True
            
            log(f"[Window] Found game window: HWND={hwnd}")
            
            # 强制激活窗口到前台（虚拟手柄需要前台窗口）
            _force_foreground_window(hwnd)
            
            log("[Window] Game window activated")
            time.sleep(0.5)
            
        except Exception as e:
            log(f"[Window] Failed to activate window: {e}")
        
        self._activated = True
        return True


class ActivateGamepad(CustomAction):
    """激活游戏手柄模式"""
    
    _activated = False
    
    def run(self, context: Context, argv) -> bool:
        if self._activated:
            return True
        
        from logger import log
        log("[Gamepad] Activating virtual gamepad mode...")
        
        controller = GamepadController()
        
        controller.tap_button('A', duration=0.1)
        time.sleep(0.3)
        controller.tap_button('A', duration=0.1)
        time.sleep(0.5)
        
        log("[Gamepad] Virtual gamepad mode activated")
        self._activated = True
        return True
