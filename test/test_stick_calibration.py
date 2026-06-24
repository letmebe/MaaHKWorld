"""
测试摇杆值和持续时间对移动距离的影响
生成二维映射表
"""
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

import vgamepad as vg
import cv2
from PIL import ImageGrab
import numpy as np
from crosshair_recognition import FindCrosshairRecognition

gamepad = vg.VX360Gamepad()
screenshot_count = 0  # 截图计数器
recognition = FindCrosshairRecognition()

class MockArgv:
    """模拟MaaFramework的argv对象"""
    def __init__(self, image, param=None):
        self.image = image
        self.custom_recognition_param = param or {}



def find_crosshair():
    """截图并找到准星位置"""
    global screenshot_count
    screenshot = ImageGrab.grab(bbox=(0, 0, 1920, 1080))
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    # 保存前5张截图
    current_count = screenshot_count
    if current_count < 5:
        filename = f"test_screenshot_{current_count}.png"
        cv2.imwrite(filename, image)
        print(f"  截图成功: {image.shape} -> 已保存到 {filename}", end='')
        screenshot_count += 1
    else:
        print(f"  截图成功: {image.shape}", end='')
    
    # 使用原项目的准星识别器
    argv = MockArgv(image, {'threshold': 0.8})
    result = recognition.analyze(None, argv)
    
    if result and hasattr(result, 'detail'):
        detail = result.detail
        cx = detail.get('center_x')
        cy = detail.get('center_y')
        if cx is not None and cy is not None:
            center = (cx, cy)
            print(f" -> 找到准星: {center}")
            # 在前5张截图上标记准星位置
            if current_count < 5:
                marked_image = image.copy()
                cv2.circle(marked_image, (cx, cy), 50, (0, 255, 0), 2)
                cv2.circle(marked_image, (cx, cy), 3, (0, 0, 255), -1)
                cv2.putText(marked_image, f"({cx}, {cy})", (cx + 10, cy - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                marked_filename = f"test_screenshot_{current_count}_marked.png"
                cv2.imwrite(marked_filename, marked_image)
                print(f"    已标记准星位置: {marked_filename}")
            return center
    
    print(f" -> 未找到准星")
    return None

def test_stick_value(stick_value, duration):
    """测试指定摇杆值和持续时间的移动距离"""
    print(f"  测试摇杆值={stick_value}, 持续时间={duration}s")
    
    # 找到初始准星位置
    result1 = find_crosshair()
    if result1 is None:
        print(f"  初始位置: 未找到准星")
        return None, None
    x1, y1 = result1
    print(f"  初始位置: ({x1}, {y1})")
    
    # 检查是否靠近边界（留150像素缓冲）
    if x1 < 150 or x1 > 1770 or y1 < 150 or y1 > 930:
        print(f"  靠近边界，跳过测试")
        return x1, None
    
    # 移动摇杆
    print(f"  移动摇杆...")
    gamepad.left_joystick(x_value=stick_value, y_value=0)
    gamepad.update()
    time.sleep(duration)
    gamepad.left_joystick(x_value=0, y_value=0)
    gamepad.update()
    time.sleep(0.2)  # 等待稳定
    
    # 找到移动后准星位置
    result2 = find_crosshair()
    if result2 is None:
        print(f"  移动后位置: 未找到准星")
        return x1, None
    x2, y2 = result2
    print(f"  移动后位置: ({x2}, {y2})")
    
    # 计算移动距离
    distance = abs(x2 - x1)
    print(f"  移动距离: {distance}px")
    return x2, distance

print("创建虚拟手柄成功")

# 激活游戏窗口
print("激活游戏窗口...")
try:
    import win32gui
    import win32con
    
    hwnd = win32gui.FindWindow("UnrealWindow", "王者荣耀世界")
    if hwnd:
        print(f"找到游戏窗口: HWND={hwnd}")
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

# 激活手柄模式
print("激活手柄模式...")
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

print("\n请确认游戏已进入手柄模式...")
print("检测准星是否存在（确保手柄已启用）...")

max_wait = 30  # 最多等待30秒
for i in range(max_wait):
    result = find_crosshair()
    if result is not None and result[0] is not None and result[1] is not None:
        print(f"\n✓ 检测到准星: {result}，手柄已启用")
        break
    print(f"  等待准星出现... ({i+1}/{max_wait}s)", end='\r')
    time.sleep(1)
else:
    print(f"\n✗ {max_wait}秒内未检测到准星，请确认手柄是否启用")
    print("继续测试...")

time.sleep(1.0)
print("\n开始测试！\n")

# 测试不同的摇杆值和持续时间
stick_values = [
    32767,  # 最大值
    30000,
    25000,
    20000,
    15000,
    12000,
    10000,
    8000,
    6000,
    5000,
    4000,
    3000,
    2000,
    1000,
]

durations = [
    0.05,
    0.08,
    0.10,
    0.12,
    0.15,
    0.20,
    0.25,
]

results = {}  # {(stick, duration): distance}

print(f"测试参数：摇杆值 x 持续时间")
print(f"摇杆值数量：{len(stick_values)}")
print(f"持续时间数量：{len(durations)}")
print(f"总测试数：{len(stick_values) * len(durations)}")
print("=" * 60)

test_count = 0
total_tests = len(stick_values) * len(durations)

for duration in durations:
    print(f"\n持续时间: {duration}s")
    print("-" * 60)
    print(f"{'摇杆值':>8} | {'移动距离':>8} | {'进度':>10}")
    
    for stick_val in stick_values:
        test_count += 1
        
        # 测试正向
        x_after, dist = test_stick_value(stick_val, duration)
        
        if dist is not None:
            results[(stick_val, duration)] = dist
            print(f"{stick_val:>8} | {dist:>8.1f}px | {test_count}/{total_tests}")
            
            # 移回中心，避免靠近边界
            time.sleep(0.5)  # 等待准星稳定
            gamepad.left_joystick(x_value=-stick_val, y_value=0)
            gamepad.update()
            time.sleep(duration)
            gamepad.left_joystick(x_value=0, y_value=0)
            gamepad.update()
            time.sleep(0.5)  # 等待准星稳定
        else:
            print(f"{stick_val:>8} | {'N/A':>8} | {test_count}/{total_tests}")
        
        time.sleep(0.5)  # 测试之间的延迟

print("\n" + "=" * 60)

# 生成二维映射表
print("\n生成的二维映射表：")
print("STICK_DURATION_MAP = {")
for duration in durations:
    print(f"    {duration}: {{  # 持续时间 {duration}s")
    for stick_val in stick_values:
        if (stick_val, duration) in results:
            dist = results[(stick_val, duration)]
            print(f"        {stick_val}: {dist:.1f},")
    print("    },")
print("}")

# 生成距离查询函数
print("\n建议的距离查询函数：")
print("""
def find_stick_params(target_distance, duration=0.10):
    '''根据目标距离查找合适的摇杆值'''
    if duration not in STICK_DURATION_MAP:
        return None
    
    duration_map = STICK_DURATION_MAP[duration]
    
    # 找到最接近的距离
    best_stick = None
    best_diff = float('inf')
    
    for stick, dist in duration_map.items():
        diff = abs(dist - target_distance)
        if diff < best_diff:
            best_diff = diff
            best_stick = stick
    
    return best_stick
""")

print(f"\n测试完成！共测试 {test_count} 组合")
