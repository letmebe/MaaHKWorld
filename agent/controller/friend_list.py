"""
自定义识别器和动作 - 好友列表管理与浇水操作
"""
import json
import time
import ctypes
import cv2
import numpy as np
import vgamepad as vg
from pathlib import Path
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RectType
from utils.common_action import GamepadController
from utils.logger import log


class FriendListController:
    """
    好友列表控制器（单例模式）
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.current_index = 0
            instance.friend_list = []
            instance.initialized = False
            instance.water_count = 0
            cls._instance = instance
        return cls._instance
    
    def set_friend_list(self, friend_list):
        """设置好友列表"""
        self.friend_list = friend_list
        self.current_index = 0
        self.initialized = True
        log(f"[FriendList] 设置好友列表: {friend_list}")
    
    def get_current_friend(self):
        """获取当前好友名称"""
        if self.current_index < len(self.friend_list):
            return self.friend_list[self.current_index]
        return None
    
    def next_friend(self):
        """移动到下一个好友"""
        self.current_index += 1
        log(f"[FriendList] 移动到下一个好友，index={self.current_index}")
    
    def has_more(self):
        """是否还有更多好友"""
        return self.current_index < len(self.friend_list)


class InitFriendList(CustomAction):
    """
    初始化好友列表
    从参数中获取好友列表并设置到控制器
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
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
        
        friend_list = param.get('friend_list', [])
        
        controller = FriendListController()
        controller.set_friend_list(friend_list)
        
        return True


class CheckCurrentFriend(CustomAction):
    """
    检查当前好友
    获取当前好友名称，通过override_pipeline设置OCR参数
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = FriendListController()
        friend_name = controller.get_current_friend()
        
        if friend_name:
            log(f"[CheckCurrentFriend] 当前好友: {friend_name}")
            
            # 通过override_pipeline设置OCR参数
            context.override_pipeline({
                "好友浇水_查找好友": {
                    "recognition": {
                        "type": "OCR",
                        "param": {
                            "roi": [1200, 250, 460, 770],
                            "expected": [friend_name]
                        }
                    }
                }
            })
            
            return True
        else:
            log(f"[CheckCurrentFriend] 无更多好友")
            return False


class CheckMoreFriends(CustomRecognition):
    """
    检查是否还有更多好友
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv) -> RectType:
        controller = FriendListController()
        
        if controller.has_more():
            log(f"[CheckMoreFriends] 还有更多好友")
            return None  # 返回None表示未命中，继续循环
        else:
            log(f"[CheckMoreFriends] 无更多好友，任务完成")
            return (0, 0, 100, 100)  # 返回命中，退出循环


class NextFriend(CustomAction):
    """
    移动到下一个好友
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        controller = FriendListController()
        controller.next_friend()
        # 清零浇水计数（为下一个好友准备）
        controller.water_count = 0
        log(f"[NextFriend] 清零浇水计数")
        return True


class OpenFriendMenu(CustomAction):
    """
    打开好友菜单
    
    按住左方向键下 → 打开快捷轮盘
    按住右摇杆下 → 移动到好友选项
    松开左方向键下 → 确认选择
    松开右摇杆 → 完成操作
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        log(f"[OpenFriendMenu] 开始执行")
        
        try:
            controller = GamepadController()
            
            # 1. 按住左方向键下（打开快捷轮盘）
            log(f"[OpenFriendMenu] 按住左方向键下")
            controller._gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 2. 按住右摇杆下（移动到好友选项）
            log(f"[OpenFriendMenu] 按住右摇杆下")
            controller._gamepad.right_joystick(x_value=0, y_value=-30000)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 3. 松开左方向键下（确认选择）
            log(f"[OpenFriendMenu] 松开左方向键下")
            controller._gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 4. 松开右摇杆（完成操作）
            log(f"[OpenFriendMenu] 松开右摇杆")
            controller._gamepad.right_joystick(x_value=0, y_value=0)
            controller._gamepad.update()
            
            log(f"[OpenFriendMenu] ✓ 完成")
            return True
        except Exception as e:
            log(f"[OpenFriendMenu] ❌ 异常: {e}")
            return False


class GoHome(CustomAction):
    """
    回家
    
    按住左方向键下 → 打开快捷轮盘
    按住右摇杆右下45度 → 移动到回家选项
    松开左方向键下 → 确认选择
    松开右摇杆 → 完成操作
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        log(f"[GoHome] 开始执行")
        
        try:
            controller = GamepadController()
            
            # 右下45度：x=30000, y=-30000
            stick_x = 30000
            stick_y = -30000
            
            # 1. 按住左方向键下（打开快捷轮盘）
            log(f"[GoHome] 按住左方向键下")
            controller._gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 2. 按住右摇杆右下45度（移动到回家选项）
            log(f"[GoHome] 按住右摇杆右下45度")
            controller._gamepad.right_joystick(x_value=stick_x, y_value=stick_y)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 3. 松开左方向键下（确认选择）
            log(f"[GoHome] 松开左方向键下")
            controller._gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
            controller._gamepad.update()
            time.sleep(0.3)
            
            # 4. 松开右摇杆（完成操作）
            log(f"[GoHome] 松开右摇杆")
            controller._gamepad.right_joystick(x_value=0, y_value=0)
            controller._gamepad.update()
            

            log(f"[GoHome] ✓ 完成")
            return True
        except Exception as e:
            log(f"[GoHome] ❌ 异常: {e}")
            return False


class CheckWateringButtonByOCR(CustomRecognition):
    """
    检查浇水按钮
    根据好友名称OCR结果计算ROI，在ROI内查找浇水按钮模板
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv) -> RectType:
        log(f"[CheckWateringButtonByOCR] 开始执行")
        
        try:
            # 获取好友名称box（从custom_recognition_param中，由ExtractOCRTarget传递）
            param = argv.custom_recognition_param
            if isinstance(param, str):
                try:
                    parsed = json.loads(param)
                    if isinstance(parsed, str):
                        param = json.loads(parsed)
                    else:
                        param = parsed
                except:
                    param = {}
            
            target_x = param.get('target_x', 0)
            target_y = param.get('target_y', 0)
            
            # 计算好友名称box左上角坐标
            # 横坐标固定为1200，文本高度约25px，从中心坐标计算左上角
            box_x = 1200
            box_y = target_y - 12  # 文本高度25px，中心向上偏移12.5px
            
            # 计算浇水按钮ROI: 好友名称box左上角，宽640，高100
            roi_x = box_x
            roi_y = box_y
            roi_w = 640
            roi_h = 100
            
            log(f"[CheckWateringButtonByOCR] 浇水按钮ROI: [{roi_x}, {roi_y}, {roi_w}, {roi_h}]")
            
            # 使用原生模板匹配
            from maa.pipeline import JRecognitionType, JTemplateMatch
            
            template_param = JTemplateMatch(
                roi=[roi_x, roi_y, roi_w, roi_h],
                template=["jiaoshui.png"],
                threshold=[0.95]
            )
            
            result = context.run_recognition_direct(
                reco_type=JRecognitionType.TemplateMatch,
                reco_param=template_param,
                image=argv.image
            )
            
            if result and result.best_result:
                box = result.best_result.box
                score = result.best_result.score if hasattr(result.best_result, 'score') else 0
                log(f"[CheckWateringButtonByOCR] ✓ 找到浇水按钮, box={box}, score={score:.4f}")
                return box
            else:
                log(f"[CheckWateringButtonByOCR] ✗ 未找到浇水按钮")
                return None
                
        except Exception as e:
            log(f"[CheckWateringButtonByOCR] ❌ 异常: {e}")
            return None


class MoveCursorToWateringButton(CustomAction):
    """
    移动准星到浇水按钮
    根据好友名称OCR结果计算目标位置
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        log(f"[MoveCursorToWateringButton] 开始执行")
        
        try:
            # 获取好友名称box（从custom_action_param中，由ExtractOCRTarget传递）
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
            
            target_x = param.get('target_x', 0)
            target_y = param.get('target_y', 0)
            
            # 计算好友名称box左上角坐标（参考CheckWateringButtonByOCR）
            box_x = 1200
            box_y = target_y - 12  # 文本高度25px，中心向上偏移
            
            # 计算目标坐标: box左上角 + (595, 40)
            button_x = box_x + 595
            button_y = box_y + 40
            
            log(f"[MoveCursorToWateringButton] 目标坐标: ({button_x}, {button_y})")
            
            # 移动准星到目标位置
            user32 = ctypes.windll.user32
            user32.SetCursorPos(int(button_x), int(button_y))
            time.sleep(0.3)
            
            log(f"[MoveCursorToWateringButton] ✓ 完成")
            return True
                
        except Exception as e:
            log(f"[MoveCursorToWateringButton] ❌ 异常: {e}")
            return False


class CheckWateredField(CustomRecognition):
    """
    检查是否显示"这里不是可摘取的地方"文本
    
    始终返回命中，在detail中记录是否真的识别到文本
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv):
        from maa.pipeline import JRecognitionType, JOCR
        
        # 从参数中提取roi
        param = argv.custom_recognition_param
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        roi = param.get('roi', [400, 400, 1120, 280])
        
        image = argv.image
        if image is None:
            return CustomRecognition.AnalyzeResult(
                box=(960, 540, 100, 100),
                detail=json.dumps({'texts': []})
            )
        
        # 使用context.run_recognition_direct执行OCR，不使用expected过滤
        ocr_param = JOCR(roi=roi)
        
        result = context.run_recognition_direct(
            reco_type=JRecognitionType.OCR,
            reco_param=ocr_param,
            image=image
        )
        
        # 收集所有识别到的文本
        texts = []
        if result and result.all_results:
            for r in result.all_results:
                ocr_text = r.text if hasattr(r, 'text') else ''
                if ocr_text:
                    texts.append(ocr_text)
        
        log(f"[CheckWateredField] OCR识别(roi={roi}): 识别到{len(texts)}个文本: {texts}")
        
        # 始终返回命中，detail包含所有识别到的文本
        return CustomRecognition.AnalyzeResult(
            box=(960, 540, 100, 100),
            detail=json.dumps({'texts': texts})
        )


class IncrementWaterCountIfHit(CustomAction):
    """
    根据识别到的文本更新浇水计数
    
    - 未识别到文本：啥也不做
    - 识别到"这里不是可摘取的地方"：次数加一
    - 识别到其他文本：次数清零
    """
    
    def __init__(self):
        super().__init__()
    
    def run(self, context: Context, argv) -> bool:
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[IncrementWaterCountIfHit] 无reco_detail")
            return True
        
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[IncrementWaterCountIfHit] 无detail_dict")
            return True
        
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        # detail可能是字符串，需要双重解析
        if isinstance(detail, str):
            try:
                parsed = json.loads(detail)
                if isinstance(parsed, str):
                    detail = json.loads(parsed)
                else:
                    detail = parsed
            except:
                detail = {}
        
        texts = detail.get('texts', [])
        controller = FriendListController()
        
        if not texts:
            # 未识别到文本，啥也不做
            log(f"[IncrementWaterCountIfHit] 未识别到文本，保持计数: {controller.water_count}")
        elif any("这里不是可摘取的地方" in t for t in texts):
            # 识别到目标文本，次数加一
            controller.water_count = getattr(controller, 'water_count', 0) + 1
            log(f"[IncrementWaterCountIfHit] 识别到目标文本，计数加一: {controller.water_count}")
        else:
            # 识别到其他文本，次数清零
            controller.water_count = 0
            log(f"[IncrementWaterCountIfHit] 识别到其他文本{texts}，计数清零")
        
        return True


class CheckWaterCount(CustomRecognition):
    """
    检查浇水计数是否超过阈值
    
    如果计数 >= threshold，返回命中
    """
    
    def __init__(self):
        super().__init__()
    
    def analyze(self, context: Context, argv):
        param = argv.custom_recognition_param
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        threshold = param.get('threshold', 10)
        
        controller = FriendListController()
        water_count = getattr(controller, 'water_count', 0)
        
        if water_count >= threshold:
            log(f"[CheckWaterCount] 浇水计数已达阈值: {water_count}/{threshold}，返回命中")
            return (960, 540, 100, 100)
        else:
            log(f"[CheckWaterCount] 浇水计数未达阈值: {water_count}/{threshold}，返回未命中")
            return None


