"""
创建桌面快捷方式
"""
import win32com.client
import os
import sys

def create_shortcut():
    # 获取参数
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        # 默认使用VBS文件
        target_path = os.path.join(os.path.dirname(__file__), '启动王世界助手.vbs')
        if not os.path.exists(target_path):
            # 如果VBS不存在，使用BAT文件
            target_path = os.path.join(os.path.dirname(__file__), '启动王世界助手.bat')
    
    shortcut_path = os.path.expanduser('~\\Desktop\\MaaHKWorld.lnk')
    
    # 检测图标路径
    icon_path = None
    dev_icon = os.path.join(os.path.dirname(__file__), 'assets', 'resource', 'image', 'logo.ico')
    release_icon = os.path.join(os.path.dirname(__file__), 'resource', 'image', 'logo.ico')
    
    if os.path.exists(dev_icon):
        icon_path = dev_icon
    elif os.path.exists(release_icon):
        icon_path = release_icon
    
    # 创建快捷方式
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(__file__)
    shortcut.Description = 'MaaHKWorld - Automation Assistant'
    
    if icon_path:
        shortcut.IconLocation = icon_path
    
    shortcut.Save()
    
    return os.path.exists(shortcut_path)

if __name__ == '__main__':
    if create_shortcut():
        print('[OK] Desktop shortcut created')
    else:
        print('[WARNING] Failed to create desktop shortcut')