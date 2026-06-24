"""
测试瞄准功能
使用校准映射表精确控制摇杆
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

import time
import cv2
import numpy as np
from PIL import ImageGrab
from crosshair_recognition import FindCrosshairRecognition
from stick_calibration_map import find_stick_params_for_axis
import vgamepad as vg

gamepad = vg.VX360Gamepad()
recognition = FindCrosshairRecognition()

class MockArgv:
    def __init__(self, image, param=None):
        self.image = image
        self.custom_recognition_param = param or {}

def find_crosshair():
    """截图并找到准星位置"""
    screenshot = ImageGrab.grab(bbox=(0, 0, 1920, 1080))
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    argv = MockArgv(image, {'threshold': 0.8})
    result = recognition.analyze(None, argv)
    
    if result and hasattr(result, 'detail'):
        detail = result.detail
        cx = detail.get('center_x')
        cy = detail.get('center_y')
        if cx is not None and cy is not None:
            return (cx, cy)
    
    return None

def aim_to_target(target_x, target_y, tolerance=10, max_iterations=20):
    """
    瞄准到目标位置
    
    Args:
        target_x, target_y: 目标坐标
        tolerance: 容差（像素）
        max_iterations: 最大迭代次数
    
    Returns:
        bool: 是否成功
    """
    print(f"\n开始瞄准: 目标({target_x}, {target_y}), 容差{tolerance}px")
    
    for iteration in range(max_iterations):
        crosshair = find_crosshair()
        if not crosshair:
            print(f"  迭代{iteration+1}: 未找到准星")
            time.sleep(0.1)
            continue
        
        cx, cy = crosshair
        dx = target_x - cx
        dy = target_y - cy
        distance = (dx*dx + dy*dy) ** 0.5
        
        print(f"  迭代{iteration+1}: 准星({cx}, {cy}), 距离={distance:.1f}px")
        
        if distance < tolerance:
            print(f"  ✓ 瞄准完成! 距离={distance:.1f}px")
            return True
        
        result = find_stick_params_for_axis(dx, dy)
        if not result:
            print(f"  ✗ 无法找到合适的摇杆参数")
            return False
        
        stick_x, stick_y, duration, actual_dist = result
        
        stick_y = -stick_y
        
        print(f"    摇杆: ({stick_x}, {stick_y}), 持续时间: {duration}s, 预期移动: {actual_dist:.1f}px")
        
        gamepad.left_joystick(x_value=stick_x, y_value=stick_y)
        gamepad.update()
        time.sleep(duration)
        gamepad.left_joystick(x_value=0, y_value=0)
        gamepad.update()
        time.sleep(0.1)
    
    print(f"  ✗ 达到最大迭代次数{max_iterations}")
    return False

print("激活游戏窗口...")
try:
    import win32gui
    import win32con
    
    hwnd = win32gui.FindWindow("UnrealWindow", "王者荣耀世界")
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        time.sleep(0.1)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.3)
        win32gui.SetForegroundWindow(hwnd)
        print("游戏窗口已激活")
    else:
        print("未找到游戏窗口")
except Exception as e:
    print(f"激活窗口失败: {e}")

time.sleep(1.0)

print("\n激活手柄模式...")
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.1)
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.3)
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.1)
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.5)
print("手柄模式已激活")

print("\n检测准星...")
for i in range(10):
    crosshair = find_crosshair()
    if crosshair:
        print(f"✓ 检测到准星: {crosshair}")
        break
    print(f"  等待准星... ({i+1}/10)")
    time.sleep(1)
else:
    print("✗ 未检测到准星，退出")
    sys.exit(1)

time.sleep(1.0)

print("\n" + "=" * 60)
print("测试1: 瞄准左上角 (640, 360)")
print("=" * 60)
success1 = aim_to_target(640, 360, tolerance=10, max_iterations=20)

time.sleep(2.0)

print("\n" + "=" * 60)
print("测试2: 瞄准右上角 (1280, 360)")
print("=" * 60)
success2 = aim_to_target(1280, 360, tolerance=10, max_iterations=20)

time.sleep(2.0)

print("\n" + "=" * 60)
print("测试3: 瞄准中心 (960, 540)")
print("=" * 60)
success3 = aim_to_target(960, 540, tolerance=10, max_iterations=20)

print("\n" + "=" * 60)
print("测试结果:")
print(f"  测试1 (左上角): {'✓ 成功' if success1 else '✗ 失败'}")
print(f"  测试2 (右上角): {'✓ 成功' if success2 else '✗ 失败'}")
print(f"  测试3 (中心): {'✓ 成功' if success3 else '✗ 失败'}")
print("=" * 60)