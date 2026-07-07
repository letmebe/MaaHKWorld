"""
测试摇杆持续移动
"""
import time
import vgamepad as vg

gamepad = vg.VX360Gamepad()

print("创建虚拟手柄成功")
print("请切换到游戏窗口（10秒后开始测试）...")
for i in range(10, 0, -1):
    print(f"{i}秒...", end='\r')
    time.sleep(1)
print("\n开始测试！")

# 测试1：持续按住摇杆
print("\n测试1：持续按住左摇杆向右（持续2秒）")
gamepad.left_joystick(x_value=20000, y_value=0)
gamepad.update()
time.sleep(2.0)
gamepad.left_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试2：持续按住摇杆向下（Y轴负值）
print("\n测试2：持续按住左摇杆向下（持续2秒）- Y值=-20000")
gamepad.left_joystick(x_value=0, y_value=-20000)
gamepad.update()
time.sleep(2.0)
gamepad.left_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试3：推一下松开（当前方式）
print("\n测试3：推一下左摇杆向右（推0.15秒后松开）")
gamepad.left_joystick(x_value=20000, y_value=0)
gamepad.update()
time.sleep(0.15)
gamepad.left_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试4：连续推多次
print("\n测试4：连续推左摇杆向右（推5次，每次0.15秒）")
for i in range(5):
    gamepad.left_joystick(x_value=20000, y_value=0)
    gamepad.update()
    time.sleep(0.15)
    gamepad.left_joystick(x_value=0, y_value=0)
    gamepad.update()
    time.sleep(0.1)
print("完成")

time.sleep(1.0)

# 测试5：右摇杆向右（调整视角）
print("\n测试5：右摇杆向右（持续2秒）- 调整视角")
gamepad.right_joystick(x_value=20000, y_value=0)
gamepad.update()
time.sleep(2.0)
gamepad.right_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试6：右摇杆向左
print("\n测试6：右摇杆向左（持续2秒）")
gamepad.right_joystick(x_value=-20000, y_value=0)
gamepad.update()
time.sleep(2.0)
gamepad.right_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试7：右摇杆向上
print("\n测试7：右摇杆向上（持续2秒）")
gamepad.right_joystick(x_value=0, y_value=-20000)
gamepad.update()
time.sleep(2.0)
gamepad.right_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试8：右摇杆向下
print("\n测试8：右摇杆向下（持续2秒）")
gamepad.right_joystick(x_value=0, y_value=20000)
gamepad.update()
time.sleep(2.0)
gamepad.right_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

time.sleep(1.0)

# 测试9：右摇杆右下（对角线）
print("\n测试9：右摇杆右下（持续2秒）")
gamepad.right_joystick(x_value=20000, y_value=20000)
gamepad.update()
time.sleep(2.0)
gamepad.right_joystick(x_value=0, y_value=0)
gamepad.update()
print("完成")

print("\n所有测试完成")