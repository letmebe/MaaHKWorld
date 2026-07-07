"""
自定义识别器 - 准星位置识别（两阶段检测+环形连续性验证）
算法来源：F:\\test\\crosshair_detect_final.py
准确度：8张真值图像上的平均误差 2.3px
"""
import cv2
import numpy as np
import json
from pathlib import Path
from typing import Optional, Union
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType

from utils.logger import log

# 预计算角度用于径向采样
NUM_ANGLES = 72
ANGLES = np.linspace(0, 2 * np.pi, NUM_ANGLES, endpoint=False)
COS_ANGLES = np.cos(ANGLES)
SIN_ANGLES = np.sin(ANGLES)

# 准星参数
NORMAL_RING_R = 42
INTERACT_RING_R = 25
MAX_RING_R = NORMAL_RING_R

# 准星中心颜色特征
TARGET_B = 231
TARGET_G = 227
TARGET_R = 220
TARGET_GRAY = 225
BGR_TOL = 10
GRAY_TOL = 10

# 置信度阈值
FULL_SCORE_THRESHOLD = 250
EDGE_SCORE_THRESHOLD = 60


class FindCrosshairRecognition(CustomRecognition):
    """
    准星位置识别器
    使用两阶段检测+环形连续性验证算法
    """
    
    def analyze(self, context: Context, argv) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        """
        识别准星位置
        
        Args:
            argv.image: 截图（由MaaFramework提供）
        
        Returns:
            AnalyzeResult: box为准星中心坐标(x, y, 1, 1)
        """
        bgr = argv.image
        if bgr is None:
            return None
        
        # 解析参数
        param = argv.custom_recognition_param
        if isinstance(param, str):
            try:
                param = json.loads(param)
            except:
                param = {}
        
        roi = param.get('roi', None) if isinstance(param, dict) else None
        
        # 如果指定了ROI，先在ROI内查找
        if roi is not None:
            x1, y1, x2, y2 = roi
            x1 = max(0, int(x1))
            y1 = max(0, int(y1))
            x2 = min(bgr.shape[1], int(x2))
            y2 = min(bgr.shape[0], int(y2))
            
            if x2 > x1 and y2 > y1:
                bgr_roi = bgr[y1:y2, x1:x2]
                roi_offset = (x1, y1)
                log(f"[CrosshairReco] 使用ROI: ({x1}, {y1}) - ({x2}, {y2})")
            else:
                bgr_roi = bgr
                roi_offset = (0, 0)
            
            # 先在ROI内检测
            result = self._detect_crosshair(bgr_roi)
            
            # 如果ROI内找不到，切换到全屏查找
            if result['type'] == 'none':
                log(f"[CrosshairReco] ROI内未找到准星，切换到全屏查找")
                result = self._detect_crosshair(bgr)
                roi_offset = (0, 0)
        else:
            bgr_roi = bgr
            roi_offset = (0, 0)
            result = self._detect_crosshair(bgr_roi)
        
        if result['type'] == 'none':
            log(f"[CrosshairReco] 未找到准星")
            return None
        
        # 转换为全图坐标
        cx = result['cx'] + roi_offset[0]
        cy = result['cy'] + roi_offset[1]
        
        log(f"[CrosshairReco] 找到准星: ({cx}, {cy}), 类型={result['type']}, 分数={result['score']:.1f}")
        
        return CustomRecognition.AnalyzeResult(
            box=(cx, cy, 1, 1),
            detail={
                'center_x': cx,
                'center_y': cy,
                'type': result['type'],
                'score': result['score'],
            }
        )
    
    def _detect_crosshair(self, bgr):
        """两阶段准星检测"""
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        local_bg = cv2.blur(gray.astype(np.float32), (151, 151))
        
        # 阶段1：全图检测
        full_result = self._phase1_full_image_detect(gray, bgr, local_bg, h, w)
        
        # 如果阶段1结果置信度高，立即返回
        if full_result is not None and full_result['score'] >= FULL_SCORE_THRESHOLD:
            return full_result
        
        # 阶段2：边缘检测
        edge_result = self._phase2_edge_detect(gray, bgr, local_bg, h, w)
        
        # 如果边缘检测找到了目标，优先选择它
        if edge_result is not None and edge_result['score'] >= EDGE_SCORE_THRESHOLD:
            return edge_result
        
        if edge_result is not None:
            return edge_result
        
        # 回退到阶段1结果
        if full_result is not None:
            return full_result
        
        return {'cx': w // 2, 'cy': h // 2, 'type': 'none', 'score': 0}
    
    def _phase1_full_image_detect(self, gray, bgr, local_bg, h, w):
        """阶段1：全图检测"""
        candidates = self._find_color_candidates(gray, bgr, local_bg, h, w, margin=20)
        
        best_score = -999
        best_result = None
        
        for cx, cy, center_gray, center_inc, sharpness, area in candidates:
            ring_checks = [(NORMAL_RING_R, 'normal'), (INTERACT_RING_R, 'interact')]
            
            adaptive_r, adaptive_val = self._find_adaptive_ring_r(cx, cy, gray, local_bg, h, w)
            if adaptive_r is not None:
                if abs(adaptive_r - NORMAL_RING_R) > 5 and abs(adaptive_r - INTERACT_RING_R) > 5:
                    ring_checks.append((adaptive_r, f'adaptive_r{adaptive_r}'))
            
            for ring_r, ctype in ring_checks:
                max_r = min(cx, w - cx - 1, cy, h - cy - 1, 55)
                if max_r < ring_r + 8:
                    continue
                
                ring_info = self._verify_ring_full(cx, cy, gray, local_bg, ring_r, h, w)
                if ring_info is None:
                    continue
                
                continuity, arc_coverage = self._measure_ring_continuity(
                    cx, cy, gray, local_bg, ring_r, h, w)
                
                s = self._score_candidate(ring_info, center_inc, sharpness, area, center_gray, continuity)
                if s > best_score:
                    best_score = s
                    best_result = {
                        'cx': cx, 'cy': cy, 'type': ctype, 'score': s,
                        'ring_peak': ring_info['ring_peak'],
                        'rpg': ring_info['rpg'],
                        'center_inc': center_inc,
                        'sharpness': sharpness,
                    }
        
        return best_result
    
    def _phase2_edge_detect(self, gray, bgr, local_bg, h, w):
        """阶段2：边缘条带检测"""
        strip_width = MAX_RING_R * 2 + 30
        candidates = self._find_edge_candidates(gray, bgr, local_bg, h, w, strip_width)
        
        best_score = -999
        best_result = None
        
        for cx, cy, center_gray, center_inc, sharpness, area, near_edges in candidates:
            for ring_r, ctype in [(NORMAL_RING_R, 'normal'), (INTERACT_RING_R, 'interact')]:
                ring_info = self._verify_ring_partial(cx, cy, gray, local_bg, ring_r, h, w)
                if ring_info is None:
                    continue
                
                vr = ring_info['visible_ratio']
                if ring_info['ring_peak'] < 5 and vr >= 0.5:
                    continue
                if ring_info['ring_peak'] < -50:
                    continue
                if vr < 0.2:
                    continue
                
                continuity, arc_coverage = self._measure_ring_continuity(
                    cx, cy, gray, local_bg, ring_r, h, w)
                
                s = self._score_edge_candidate(ring_info, center_inc, sharpness,
                                               area, center_gray, continuity)
                if s > best_score:
                    best_score = s
                    best_result = {
                        'cx': cx, 'cy': cy, 'type': ctype, 'score': s,
                        'ring_peak': ring_info['ring_peak'],
                        'rpg': ring_info['rpg'],
                        'center_inc': center_inc,
                        'sharpness': sharpness,
                        'visible_ratio': ring_info['visible_ratio'],
                        'continuity': continuity,
                    }
        
        return best_result
    
    def _find_color_candidates(self, gray, bgr, local_bg, h, w, margin=20):
        """在全图中查找颜色匹配的候选点"""
        b_diff = np.abs(bgr[:, :, 0].astype(np.int16) - TARGET_B)
        g_diff = np.abs(bgr[:, :, 1].astype(np.int16) - TARGET_G)
        r_diff = np.abs(bgr[:, :, 2].astype(np.int16) - TARGET_R)
        gray_diff = np.abs(gray.astype(np.int16) - TARGET_GRAY)
        
        bgr_ok = (b_diff <= BGR_TOL) & (g_diff <= BGR_TOL) & (r_diff <= BGR_TOL)
        full_match = bgr_ok & (gray_diff <= GRAY_TOL)
        secondary = bgr_ok & (gray.astype(int) >= 210) & (gray.astype(int) <= 240) & ~full_match
        color_mask = full_match | secondary
        
        binary = (color_mask.astype(np.uint8)) * 255
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1 or area > 80:
                continue
            M = cv2.moments(cnt)
            if M['m00'] == 0:
                continue
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            y1, y2 = max(0, cy - 3), min(h, cy + 4)
            x1, x2 = max(0, cx - 3), min(w, cx + 4)
            patch = color_mask[y1:y2, x1:x2]
            ys, xs = np.where(patch)
            if len(ys) > 0:
                ys_abs = ys + y1
                xs_abs = xs + x1
                brightest_idx = np.argmax(gray[ys_abs, xs_abs])
                cx, cy = int(xs_abs[brightest_idx]), int(ys_abs[brightest_idx])
            
            if margin <= cy < h - margin and margin <= cx < w - margin:
                center_gray = int(gray[cy, cx])
                bg = float(local_bg[cy, cx])
                center_inc = center_gray - bg
                
                if center_inc < 30:
                    continue
                
                sharpness = 0
                if cy >= 3 and cy < h - 3 and cx >= 3 and cx < w - 3:
                    for dx, dy in [(3, 0), (-3, 0), (0, 3), (0, -3)]:
                        sharpness += max(0, center_gray - int(gray[cy + dy, cx + dx]))
                    sharpness /= 4.0
                
                if sharpness < 20:
                    continue
                
                candidates.append((cx, cy, center_gray, center_inc, sharpness, float(area)))
        
        return candidates
    
    def _find_edge_candidates(self, gray, bgr, local_bg, h, w, strip_width=120):
        """在边缘条带中查找候选点"""
        EDGE_BGR_TOL = 25
        
        b_diff = np.abs(bgr[:, :, 0].astype(np.int16) - TARGET_B)
        g_diff = np.abs(bgr[:, :, 1].astype(np.int16) - TARGET_G)
        r_diff = np.abs(bgr[:, :, 2].astype(np.int16) - TARGET_R)
        
        bgr_ok = (b_diff <= EDGE_BGR_TOL) & (g_diff <= EDGE_BGR_TOL) & (r_diff <= EDGE_BGR_TOL)
        color_mask = bgr_ok & (gray.astype(int) >= 200) & (gray.astype(int) <= 250)
        
        binary = (color_mask.astype(np.uint8)) * 255
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1 or area > 150:
                continue
            M = cv2.moments(cnt)
            if M['m00'] == 0:
                continue
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            y1, y2 = max(0, cy - 3), min(h, cy + 4)
            x1, x2 = max(0, cx - 3), min(w, cx + 4)
            patch = color_mask[y1:y2, x1:x2]
            ys, xs = np.where(patch)
            if len(ys) > 0:
                ys_abs = ys + y1
                xs_abs = xs + x1
                brightest_idx = np.argmax(gray[ys_abs, xs_abs])
                cx, cy = int(xs_abs[brightest_idx]), int(ys_abs[brightest_idx])
            
            dist_l = cx
            dist_r = w - 1 - cx
            dist_t = cy
            dist_b = h - 1 - cy
            min_edge = min(dist_l, dist_r, dist_t, dist_b)
            
            if min_edge >= strip_width:
                continue
            
            if 0 <= cy < h and 0 <= cx < w:
                center_gray = int(gray[cy, cx])
                bg = float(local_bg[cy, cx])
                center_inc = center_gray - bg
                
                if center_inc < 20:
                    continue
                
                sharpness = 0
                sharp_count = 0
                for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        sharpness += max(0, center_gray - int(gray[ny, nx]))
                        sharp_count += 1
                if sharp_count > 0:
                    sharpness /= sharp_count
                
                if sharpness < 10:
                    continue
                
                near_edges = []
                if dist_l < strip_width:
                    near_edges.append('left')
                if dist_r < strip_width:
                    near_edges.append('right')
                if dist_t < strip_width:
                    near_edges.append('top')
                if dist_b < strip_width:
                    near_edges.append('bottom')
                
                candidates.append((cx, cy, center_gray, center_inc, sharpness,
                                   float(area), near_edges))
        
        return candidates
    
    def _verify_ring_full(self, cx, cy, gray, local_bg, ring_r, h, w):
        """对完全可见的准星进行环形验证"""
        max_r = min(cx, w - cx - 1, cy, h - cy - 1, 55)
        if max_r < ring_r + 8:
            return None
        
        ring_s = max(0, ring_r - 4)
        ring_e = min(max_r, ring_r + 4)
        gap_s, gap_e = 5, ring_s
        beyond_s, beyond_e = ring_e + 1, max_r
        
        ring_peak = -999
        ring_total = 0
        ring_count = 0
        
        for r in range(ring_s, ring_e + 1):
            px = np.clip(cx + (r * COS_ANGLES).astype(int), 0, w - 1)
            py = np.clip(cy + (r * SIN_ANGLES).astype(int), 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            r_inc = float(inc_vals.mean())
            ring_total += r_inc
            ring_count += 1
            if r_inc > ring_peak:
                ring_peak = r_inc
        
        if ring_count == 0:
            return None
        ring_avg = ring_total / ring_count
        
        gap_total, gap_count = 0.0, 0
        for r in range(gap_s, min(gap_e + 1, 30), 2):
            px = np.clip(cx + (r * COS_ANGLES).astype(int), 0, w - 1)
            py = np.clip(cy + (r * SIN_ANGLES).astype(int), 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            gap_total += float(inc_vals.mean())
            gap_count += 1
        gap_inc = gap_total / max(gap_count, 1)
        
        beyond_total, beyond_count = 0.0, 0
        for r in range(beyond_s, min(beyond_e + 1, beyond_s + 15), 3):
            px = np.clip(cx + (r * COS_ANGLES).astype(int), 0, w - 1)
            py = np.clip(cy + (r * SIN_ANGLES).astype(int), 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            beyond_total += float(inc_vals.mean())
            beyond_count += 1
        beyond_inc = beyond_total / max(beyond_count, 1)
        
        rpg = ring_peak - gap_inc
        rpb = ring_peak - beyond_inc
        cg = (float(gray[cy, cx]) - float(local_bg[cy, cx])) - gap_inc
        ring_narrowness = ring_peak / max(abs(ring_avg), 0.1)
        
        return {
            'ring_peak': ring_peak, 'rpg': rpg, 'rpb': rpb, 'cg': cg,
            'ring_narrowness': ring_narrowness, 'gap_inc': gap_inc,
            'ring_avg': ring_avg,
        }
    
    def _verify_ring_partial(self, cx, cy, gray, local_bg, ring_r, h, w):
        """对屏幕边缘部分可见的准星进行环形验证"""
        pad = 2
        ring_s = max(1, ring_r - 4)
        ring_e = ring_r + 4
        
        ring_peak = -999
        ring_total = 0.0
        ring_count = 0
        total_valid = 0
        total_angles = 0
        
        for r in range(ring_s, ring_e + 1):
            raw_x = cx + (r * COS_ANGLES).astype(int)
            raw_y = cy + (r * SIN_ANGLES).astype(int)
            
            valid = (raw_x >= pad) & (raw_x < w - pad) & (raw_y >= pad) & (raw_y < h - pad)
            n_valid = valid.sum()
            total_valid += n_valid
            total_angles += NUM_ANGLES
            
            if n_valid < 4:
                continue
            
            px = np.clip(raw_x, 0, w - 1)
            py = np.clip(raw_y, 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            
            valid_inc = inc_vals[valid]
            r_peak = float(valid_inc.max())
            r_mean = float(valid_inc.mean())
            
            if r_peak > ring_peak:
                ring_peak = r_peak
            ring_total += r_mean
            ring_count += 1
        
        if ring_count == 0 or total_angles == 0:
            return None
        
        visible_ratio = total_valid / total_angles
        ring_avg = ring_total / ring_count
        
        gap_s = 5
        gap_e = ring_s
        gap_total, gap_count = 0.0, 0
        for r in range(gap_s, min(gap_e + 1, 30), 2):
            raw_x = cx + (r * COS_ANGLES).astype(int)
            raw_y = cy + (r * SIN_ANGLES).astype(int)
            valid = (raw_x >= pad) & (raw_x < w - pad) & (raw_y >= pad) & (raw_y < h - pad)
            if valid.sum() < 4:
                continue
            px = np.clip(raw_x, 0, w - 1)
            py = np.clip(raw_y, 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            gap_total += float(inc_vals[valid].mean())
            gap_count += 1
        gap_inc = gap_total / max(gap_count, 1)
        
        beyond_s = ring_e + 1
        beyond_e = min(beyond_s + 15, ring_r + 20)
        beyond_total, beyond_count = 0.0, 0
        for r in range(beyond_s, beyond_e + 1, 3):
            raw_x = cx + (r * COS_ANGLES).astype(int)
            raw_y = cy + (r * SIN_ANGLES).astype(int)
            valid = (raw_x >= pad) & (raw_x < w - pad) & (raw_y >= pad) & (raw_y < h - pad)
            if valid.sum() < 4:
                continue
            px = np.clip(raw_x, 0, w - 1)
            py = np.clip(raw_y, 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            beyond_total += float(inc_vals[valid].mean())
            beyond_count += 1
        beyond_inc = beyond_total / max(beyond_count, 1)
        
        rpg = ring_peak - gap_inc
        rpb = ring_peak - beyond_inc
        center_inc = float(gray[cy, cx]) - float(local_bg[cy, cx])
        cg = center_inc - gap_inc
        ring_narrowness = ring_peak / max(abs(ring_avg), 0.1)
        
        inner_arc_peak = -999
        if visible_ratio < 0.50:
            max_inner_r = min(21, min(cx, w-cx-1, cy, h-cy-1))
            for r in range(5, max_inner_r):
                raw_x = cx + (r * COS_ANGLES).astype(int)
                raw_y = cy + (r * SIN_ANGLES).astype(int)
                valid = (raw_x >= pad) & (raw_x < w - pad) & (raw_y >= pad) & (raw_y < h - pad)
                if valid.sum() < 4:
                    continue
                px = np.clip(raw_x, 0, w - 1)
                py = np.clip(raw_y, 0, h - 1)
                inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
                arc_peak = float(inc_vals[valid].max())
                if arc_peak > inner_arc_peak:
                    inner_arc_peak = arc_peak
        
        return {
            'ring_peak': ring_peak, 'rpg': rpg, 'rpb': rpb, 'cg': cg,
            'ring_narrowness': ring_narrowness, 'gap_inc': gap_inc,
            'ring_avg': ring_avg, 'visible_ratio': visible_ratio,
            'inner_arc_peak': inner_arc_peak,
        }
    
    def _find_adaptive_ring_r(self, cx, cy, gray, local_bg, h, w, r_min=20, r_max=55):
        """通过扫描峰值查找实际环形半径"""
        max_r = min(cx, w - cx - 1, cy, h - cy - 1, r_max + 5)
        if max_r < r_min + 5:
            return None, None
        
        best_r = None
        best_val = -999
        for r in range(r_min, min(r_max + 1, max_r - 4)):
            px = np.clip(cx + (r * COS_ANGLES).astype(int), 0, w - 1)
            py = np.clip(cy + (r * SIN_ANGLES).astype(int), 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            r_mean = float(inc_vals.mean())
            if r_mean > best_val:
                best_val = r_mean
                best_r = r
        
        if best_r is not None and best_val > 10:
            return best_r, best_val
        return None, None
    
    def _measure_ring_continuity(self, cx, cy, gray, local_bg, ring_r, h, w, threshold=20):
        """测量环形结构的角度连续性"""
        pad = 2
        search_band = 5
        ring_s = max(1, ring_r - search_band)
        ring_e = ring_r + search_band
        
        angle_incs = np.full(NUM_ANGLES, -999.0)
        valid_mask = np.zeros(NUM_ANGLES, dtype=bool)
        
        for r in range(ring_s, ring_e + 1):
            raw_x = cx + (r * COS_ANGLES).astype(int)
            raw_y = cy + (r * SIN_ANGLES).astype(int)
            valid = (raw_x >= pad) & (raw_x < w - pad) & (raw_y >= pad) & (raw_y < h - pad)
            
            if valid.sum() < 4:
                continue
            
            px = np.clip(raw_x, 0, w - 1)
            py = np.clip(raw_y, 0, h - 1)
            inc_vals = gray[py, px].astype(np.float64) - local_bg[py, px].astype(np.float64)
            
            for i in range(NUM_ANGLES):
                if valid[i]:
                    valid_mask[i] = True
                    if inc_vals[i] > angle_incs[i]:
                        angle_incs[i] = inc_vals[i]
        
        n_valid = valid_mask.sum()
        if n_valid < 4:
            return 0.0, 0.0
        
        bright_mask = (angle_incs > threshold) & valid_mask
        n_bright = bright_mask.sum()
        
        if n_bright < 2:
            return 0.0, 0.0
        
        doubled = np.concatenate([bright_mask, bright_mask])
        
        max_arc = 0
        current_arc = 0
        for i in range(len(doubled)):
            if doubled[i]:
                current_arc += 1
                if current_arc > max_arc:
                    max_arc = current_arc
            else:
                current_arc = 0
        
        max_arc = min(max_arc, n_valid)
        
        continuity = max_arc / n_valid if n_valid > 0 else 0.0
        arc_coverage = max_arc / NUM_ANGLES
        
        return continuity, arc_coverage
    
    def _score_candidate(self, ring_info, center_inc, sharpness, area, center_gray, continuity=0.0):
        """全图检测评分"""
        ring_factor = continuity
        
        score = 0
        score += ring_info['rpg'] * 3.0 * ring_factor
        score += ring_info['rpb'] * 1.0 * ring_factor
        rn = ring_info['ring_narrowness']
        rn_bonus = 30 if rn > 3 else (20 if rn > 2 else (10 if rn > 1.5 else 0))
        score += rn_bonus * ring_factor
        score += ring_info['cg'] * 0.3
        score += sharpness * 0.2
        score += center_inc * 0.05
        score += 15 if area < 10 else (8 if area < 25 else 0)
        gray_dist = abs(center_gray - TARGET_GRAY)
        score += 10 if gray_dist < 3 else (5 if gray_dist < 5 else 0)
        score -= 300 if ring_info['ring_peak'] < 5 else (100 if ring_info['ring_peak'] < 15 else 0)
        if center_inc > ring_info['ring_peak'] and center_inc > 30:
            score += 15
        return score
    
    def _score_edge_candidate(self, ring_info, center_inc, sharpness, area, center_gray, continuity=0.0):
        """边缘检测评分"""
        score = 0
        
        ring_factor = continuity
        
        vr = ring_info['visible_ratio']
        if vr < 0.5 and ring_factor < 0.15:
            ring_factor = 0.15
        
        score += ring_info['rpg'] * 3.0 * ring_factor
        score += ring_info['rpb'] * 1.0 * ring_factor
        
        rn = ring_info['ring_narrowness']
        rn_bonus = 25 if rn > 3 else (15 if rn > 2 else (8 if rn > 1.5 else 0))
        score += rn_bonus * ring_factor
        
        vr = ring_info['visible_ratio']
        if vr > 0.7:
            score += 20
        elif vr > 0.5:
            score += 10
        elif vr > 0.3:
            score += 5
        
        score += ring_info['cg'] * 0.3
        
        score += sharpness * 0.3
        score += center_inc * 0.05
        
        if area < 10:
            score += 15
        elif area < 25:
            score += 8
        elif area > 50:
            score -= 100
        
        gray_dist = abs(center_gray - TARGET_GRAY)
        score += 8 if gray_dist < 3 else (4 if gray_dist < 5 else 0)
        
        if continuity >= 0.8:
            score += 40
        elif continuity >= 0.6:
            score += 20
        elif continuity >= 0.4:
            score += 5
        
        if ring_info['ring_peak'] < 5:
            iap = ring_info.get('inner_arc_peak', -999)
            vr = ring_info['visible_ratio']
            if vr < 0.50 and iap > 40 and center_inc > 60:
                score += iap * 2.0
                score += center_inc * 0.3
            else:
                score -= 200
        elif ring_info['ring_peak'] < 15:
            iap = ring_info.get('inner_arc_peak', -999)
            vr = ring_info['visible_ratio']
            if vr < 0.50 and iap > 30 and center_inc > 50:
                score += iap * 1.5
                score += center_inc * 0.2
            else:
                score -= 60
        
        if center_inc > ring_info['ring_peak'] and center_inc > 25:
            score += 12
        
        return score


class FindCrosshairNearTargetRecognition(CustomRecognition):
    """
    准星接近目标识别器
    先调用FindCrosshair识别准星位置，再判断准星与目标坐标的距离是否小于容差
    """
    
    def __init__(self):
        super().__init__()
        self._finder = FindCrosshairRecognition()
    
    def analyze(self, context: Context, argv) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        param = argv.custom_recognition_param
        log(f"[CrosshairNearTarget] 收到的custom_recognition_param: {param}, 类型: {type(param)}")
        
        if isinstance(param, str):
            try:
                parsed = json.loads(param)
                if isinstance(parsed, str):
                    param = json.loads(parsed)
                else:
                    param = parsed
            except:
                param = {}
        
        log(f"[CrosshairNearTarget] 解析后的param: {param}, 类型: {type(param)}")
        
        target_x = param.get('target_x')
        target_y = param.get('target_y')
        tolerance = param.get('tolerance', 10)
        
        log(f"[CrosshairNearTarget] target_x={target_x}, target_y={target_y}, tolerance={tolerance}")
        
        if target_x is None or target_y is None:
            log("[CrosshairNearTarget] 缺少target_x或target_y参数")
            return None
        
        result = self._finder.analyze(context, argv)
        
        if result is None:
            return None
        
        cx = result.detail['center_x']
        cy = result.detail['center_y']
        
        dx = target_x - cx
        dy = target_y - cy
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < tolerance:
            log(f"[CrosshairNearTarget] 准星已到达目标: ({cx}, {cy}), 距离={distance:.1f}")
            return CustomRecognition.AnalyzeResult(
                box=(cx, cy, 1, 1),
                detail={
                    'center_x': cx,
                    'center_y': cy,
                    'distance': distance,
                }
            )
        else:
            log(f"[CrosshairNearTarget] 准星未到达目标: ({cx}, {cy}), 目标=({target_x}, {target_y}), 距离={distance:.1f}")
            return None
