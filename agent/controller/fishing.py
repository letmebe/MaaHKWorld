"""
钓鱼控制器 - 多模板匹配识别与动作处理
"""
import cv2
import numpy as np
import json
import time
from typing import Optional, Union, List, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RectType

from utils.common_action import GamepadController
from utils.logger import log


class FishingMultiMatchRecognition(CustomRecognition):
    """
    钓鱼多模板匹配识别器
    一次截图，按优先级匹配多个模板，返回最佳匹配
    """
    
    def __init__(self):
        super().__init__()
        
        dev_path = Path(__file__).parent.parent.parent / 'assets' / 'resource' / 'image'
        release_path = Path(__file__).parent.parent.parent / 'resource' / 'image'
        self.template_dir = dev_path if dev_path.exists() else release_path
        
        self.templates = {}
        self._load_templates()
        
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
        }
        
        self.roi_fishing = (1620, 800, 280, 260)
        self.roi_quick = (190, 130, 1510, 690)
        self.roi_bag = (1515, 910, 155, 60)
        self.roi_return = (1694, 950, 187, 108)
    
    def _load_templates(self):
        """加载模板图片（灰度图）"""
        template_files = {
            'paogan': 'paogan.png',
            'lagan': 'lagan.png',
            'quxiao': 'quxiao.png',
            'X_quick': 'X_quick.png',
            'quick_B': 'quick_B.png',
            'X_single': 'X_single.png',
            'Y_single': 'Y_single.png',
            'A_single': 'A_single.png',
            'B_single': 'B_single.png',
            'to_bag': 'to_bag.png',
            'fanui': 'fanui.png',
            'quxiaozhunbei': 'quxiaozhunbei.png',
        }
        
        for name, filename in template_files.items():
            path = self.template_dir / filename
            if path.exists():
                img = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if img is not None:
                    self.templates[name] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    def _match_template(self, image: np.ndarray, template_name: str,
                        roi: Tuple[int, int, int, int],
                        threshold: float = 0.75) -> Tuple[Optional[Tuple[float, Tuple[int, int, int, int]]], float]:
        """
        模板匹配（灰度图，速度更快）
        
        Returns:
            (result, score) - result为(score, box)或None，score为匹配分数
        """
        if template_name not in self.templates:
            return None, 0.0
        
        template = self.templates[template_name]
        x, y, w, h = roi
        
        roi_img = image[y:y+h, x:x+w]
        gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        
        th, tw = template.shape[:2]
        if gray_roi.shape[0] < th or gray_roi.shape[1] < tw:
            return None, 0.0
        
        result = cv2.matchTemplate(gray_roi, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            match_x = x + max_loc[0]
            match_y = y + max_loc[1]
            return (max_val, (match_x, match_y, tw, th)), max_val
        
        return None, max_val
    
    def _check_cooldown(self, name: str) -> bool:
        """检查冷却时间"""
        now = time.time()
        last = self._last_time.get(name, 0)
        cd = self._cooldown.get(name, 0)
        return now - last >= cd
    
    def analyze(self, context: Context, argv) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        """
        执行多模板匹配识别
        参考原程序逻辑：匹配成功立即返回，不继续匹配
        """
        t_start = time.perf_counter()
        image = argv.image
        log(f"[Recognition] 开始识别，图像尺寸: {image.shape}")
        
        param = argv.custom_recognition_param
        if isinstance(param, str):
            try:
                param = json.loads(param)
            except:
                param = {}
        
        threshold = param.get('threshold', 0.6) if isinstance(param, dict) else 0.6
        
        scores = {}
        
        for name in ['paogan', 'lagan', 'quxiao']:
            result, score = self._match_template(image, name, self.roi_fishing, threshold)
            scores[name] = score
        
        best_fishing = None
        best_fishing_score = 0.0
        for name in ['paogan', 'lagan', 'quxiao']:
            score = scores.get(name, 0)
            if score >= threshold and score > best_fishing_score:
                best_fishing = name
                best_fishing_score = score
        
        if best_fishing:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            if best_fishing == 'quxiao':
                log(f"[Recognition] ✓ quxiao (score: {best_fishing_score:.3f}) | 耗时: {t_elapsed:.1f}ms")
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 0, 0),
                    detail={
                        'name': 'quxiao',
                        'score': best_fishing_score,
                        'action': 'skip',
                        'priority': 2
                    }
                )
            else:
                log(f"[Recognition] ✓ {best_fishing} (score: {best_fishing_score:.3f}) | 耗时: {t_elapsed:.1f}ms")
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 0, 0),
                    detail={
                        'name': best_fishing,
                        'score': best_fishing_score,
                        'action': 'tap_A',
                        'priority': 1
                    }
                )
        
        result_x, score_x = self._match_template(image, 'X_quick', self.roi_quick, 0.8)
        scores['X_quick'] = score_x
        result_b, score_b = self._match_template(image, 'quick_B', self.roi_quick, 0.8)
        scores['quick_B'] = score_b
        
        if result_x and score_x >= score_b:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ X_quick (score: {score_x:.3f}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=result_x[1],
                detail={
                    'name': 'X_quick',
                    'score': score_x,
                    'action': 'quick_tap_X',
                    'priority': 3
                }
            )
        elif result_b:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ quick_B (score: {score_b:.3f}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=result_b[1],
                detail={
                    'name': 'quick_B',
                    'score': score_b,
                    'action': 'quick_tap_B',
                    'priority': 3
                }
            )
        
        for name, action in [('X_single', 'tap_X'), ('Y_single', 'tap_Y'),
                             ('A_single', 'tap_A'), ('B_single', 'tap_B')]:
            result, score = self._match_template(image, name, self.roi_quick, 0.8)
            scores[name] = score
            if result:
                scores[f'{name}_result'] = result
        
        best_single = None
        best_single_score = 0.0
        for name in ['X_single', 'Y_single', 'A_single', 'B_single']:
            score = scores.get(name, 0)
            if score >= 0.8 and score > best_single_score:
                best_single = name
                best_single_score = score
        
        if best_single:
            action_map = {
                'X_single': 'tap_X',
                'Y_single': 'tap_Y',
                'A_single': 'tap_A',
                'B_single': 'tap_B'
            }
            result = scores.get(f'{best_single}_result')
            if result:
                box = result[1]
            else:
                box = (0, 0, 0, 0)
            
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ {best_single} (score: {best_single_score:.3f}, box: {box}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=box,
                detail={
                    'name': best_single,
                    'score': best_single_score,
                    'action': action_map[best_single],
                    'priority': 4
                }
            )
        
        result, score = self._match_template(image, 'to_bag', self.roi_bag, threshold)
        scores['to_bag'] = score
        if result:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ to_bag (score: {score:.3f}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=result[1],
                detail={
                    'name': 'to_bag',
                    'score': score,
                    'action': 'tap_X',
                    'priority': 5
                }
            )
        
        result, score = self._match_template(image, 'fanui', self.roi_return, threshold)
        scores['fanui'] = score
        if result:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ fanui (score: {score:.3f}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=result[1],
                detail={
                    'name': 'fanui',
                    'score': score,
                    'action': 'tap_B',
                    'priority': 6
                }
            )
        
        h, w = image.shape[:2]
        result, score = self._match_template(image, 'quxiaozhunbei', (0, 0, w, h), threshold)
        scores['quxiaozhunbei'] = score
        if result:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Recognition] ✓ quxiaozhunbei (score: {score:.3f}) | 耗时: {t_elapsed:.1f}ms")
            return CustomRecognition.AnalyzeResult(
                box=result[1],
                detail={
                    'name': 'quxiaozhunbei',
                    'score': score,
                    'action': 'long_press_START',
                    'priority': 7
                }
            )
        
        t_elapsed = (time.perf_counter() - t_start) * 1000
        scores_str = ' '.join([f"{k}={v:.2f}" for k, v in scores.items()])
        log(f"[Recognition] ✗ 无匹配 | 耗时: {t_elapsed:.1f}ms | {scores_str}")
        return None


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
        
        reco_detail = argv.reco_detail
        
        if not reco_detail:
            log("[FishingAction] 无识别结果")
            return True
        
        detail_dict = reco_detail.raw_detail
        
        if not detail_dict:
            log("[FishingAction] 无识别detail")
            return True
        
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        if not detail:
            log("[FishingAction] detail 为空")
            return True
        
        name = detail.get('name')
        action = detail.get('action')
        score = detail.get('score', 0)
        
        if action == 'skip':
            return True
        
        if not self._check_cooldown(name):
            return True
        
        if name == 'quxiaozhunbei':
            if self._quxiaozhunbei_executed:
                return True
            self._quxiaozhunbei_executed = True
        
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
        
        if executed:
            self._update_cooldown(name)
            t_elapsed = (time.perf_counter() - t_start) * 1000
            log(f"[Action] {name} → {action} | 耗时: {t_elapsed:.1f}ms")
        
        return True