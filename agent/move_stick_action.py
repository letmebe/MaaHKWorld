"""
自定义动作 - 摇杆移动
"""
import json
import time
from maa.custom_action import CustomAction
from maa.context import Context

from custom_action import GamepadController
from logger import log


class MoveStickAction(CustomAction):
    """
    根据准星识别结果移动摇杆
    
    从识别结果中获取准星位置，计算与目标的偏移，移动摇杆
    """
    
    def __init__(self):
        super().__init__()
        self.controller = GamepadController()
        
        # 迭代计数器
        self.iteration_count = 0
        
        # 上次准星位置（用于计算ROI和检测误匹配）
        self.last_crosshair_x = None
        self.last_crosshair_y = None
        
        # 误匹配检测：位置不变次数
        self.position_unchanged_count = 0
        self.last_position = None
        
        # 当前任务的目标（用于检测新任务）
        self.current_target = None
        self.current_task_id = None
        
        # 连续找不到准星次数
        self.not_found_count = 0
    
    def run(self, context: Context, argv) -> bool:
        """
        执行摇杆移动
        
        Args:
            argv: ActionParam
                - reco_detail: 识别结果（包含准星位置）
                - custom_action_param: 参数（JSON字符串或dict）
                    - target_x: 目标X坐标
                    - target_y: 目标Y坐标
                    - tolerance: 容差（像素）
                    - stick: 'left' 或 'right'
                    - max_iterations: 最大迭代次数
        
        Returns:
            bool: True表示继续循环，False表示停止
        """
        # 获取识别结果
        reco_detail = argv.reco_detail
        if not reco_detail:
            log("[MoveStick] 无识别结果")
            self.not_found_count += 1
            if self.not_found_count >= 3:
                log(f"[MoveStick] ⚠ 连续{self.not_found_count}次未找到准星，切换到全图搜索")
                self.not_found_count = 0
                current_task = argv.node_name
                context.override_pipeline({
                    current_task: {
                        "recognition": "Custom",
                        "custom_recognition": "FindCrosshair",
                        "custom_recognition_param": {
                            "threshold": 0.6
                        }
                    }
                })
                return True
            return False
        
        # 找到准星，重置计数器
        self.not_found_count = 0
        
        # 从raw_detail获取准星位置
        detail_dict = reco_detail.raw_detail
        if not detail_dict:
            log("[MoveStick] 无识别detail")
            return False
        
        best = detail_dict.get('best', {})
        detail = best.get('detail', {})
        
        if not detail:
            log("[MoveStick] detail为空")
            return False
        
        center_x = detail.get('center_x')
        center_y = detail.get('center_y')
        
        if center_x is None or center_y is None:
            log("[MoveStick] 无准星位置")
            return False
        
        # 解析参数（处理双重JSON编码）
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
        
        target_x = param.get('target_x', 960)
        target_y = param.get('target_y', 540)
        tolerance = param.get('tolerance', 10)
        stick = param.get('stick', 'right')
        max_iterations = param.get('max_iterations', 20)
        
        # 检测是否是新目标（新任务）
        new_target = (target_x, target_y)
        current_task_id = argv.task_detail.task_id
        
        if self.current_target != new_target or self.current_task_id != current_task_id:
            log(f"[MoveStick] 检测到新目标或新任务: {new_target}, task_id={current_task_id}, 重置计数器")
            self.iteration_count = 0
            self.current_target = new_target
            self.current_task_id = current_task_id
            self.last_crosshair_x = None
            self.last_crosshair_y = None
            self.position_unchanged_count = 0
            self.last_position = None
        
        # 使用实例计数器
        iteration = self.iteration_count
        self.iteration_count += 1
        
        # 检查是否超过最大迭代次数
        if iteration >= max_iterations:
            log(f"[MoveStick] 达到最大迭代次数 {max_iterations}，继续尝试")
            # 不重置计数器，继续循环
        
        # 计算偏移
        dx = target_x - center_x
        dy = target_y - center_y
        
        distance = (dx*dx + dy*dy) ** 0.5
        
        log(f"[MoveStick] 迭代{iteration+1}: 准星({center_x}, {center_y}), 目标({target_x}, {target_y}), 距离={distance:.1f}")
        
        # 检查是否到达目标（两点间距离）
        if distance < tolerance:
            log(f"[MoveStick] ✓ 瞄准完成! 距离={distance:.1f}")
            self.controller.reset_sticks()
            self.iteration_count = 0  # 重置计数器
            self.last_crosshair_x = None  # 清除历史位置
            self.last_crosshair_y = None
            self.position_unchanged_count = 0  # 重置误匹配检测
            self.last_position = None
            return True  # 返回True执行next（瞄准完成）
        
        # 检测误匹配：准星位置连续3次不变且未到达目标
        current_position = (center_x, center_y)
        log(f"[MoveStick] 误匹配检测: last_position={self.last_position}, current={current_position}, unchanged_count={self.position_unchanged_count}")
        
        if self.last_position == current_position:
            self.position_unchanged_count += 1
            log(f"[MoveStick] 位置未变，计数: {self.position_unchanged_count}")
            if self.position_unchanged_count >= 3:
                log(f"[MoveStick] ⚠ 检测到误匹配！准星位置连续{self.position_unchanged_count}次不变且未到达目标，切换到全图搜索")
                # 重置状态，切换到全图搜索
                self.position_unchanged_count = 0
                self.last_position = None
                # 不设置ROI，让下次Recognition全图搜索
                current_task = argv.node_name
                context.override_pipeline({
                    current_task: {
                        "recognition": "Custom",
                        "custom_recognition": "FindCrosshair",
                        "custom_recognition_param": {
                            "threshold": 0.6
                        }
                    }
                })
                return True
        else:
            self.position_unchanged_count = 0
            log(f"[MoveStick] 位置变化，重置计数器")
        
        self.last_position = current_position
        
        # 计算摇杆值（返回移动指令列表）
        log(f"[MoveStick] 开始计算摇杆值: dx={dx:.1f}, dy={dy:.1f}")
        moves = self._calculate_stick_values(dx, dy, tolerance)
        
        if not moves:
            log(f"[MoveStick] ⚠ 无需移动，返回True结束瞄准")
            return True
        
        log(f"[MoveStick] 将执行 {len(moves)} 个独立移动")
        
        # 依次执行每个移动指令
        for i, (stick_x, stick_y, move_duration) in enumerate(moves):
            log(f"[MoveStick] 执行移动 {i+1}/{len(moves)}: ({stick_x}, {stick_y}), duration={move_duration:.3f}s, 摇杆={stick}")
            
            # 反转Y轴（vgamepad的Y轴正值向上，屏幕Y轴向下为正）
            adjusted_stick_y = -stick_y
            
            # 移动摇杆
            if stick == 'right':
                self.controller.set_right_stick(stick_x, adjusted_stick_y)
            else:
                self.controller.set_left_stick(stick_x, adjusted_stick_y)
            
            # 等待移动生效（保持摇杆状态）
            time.sleep(move_duration)
            
            # 松开摇杆（需要额外延迟让游戏响应）
            time.sleep(0.05)
            self.controller.reset_sticks()
            time.sleep(0.1)  # 每次移动后稍作停顿
        
        log(f"[MoveStick] 所有移动指令执行完成")
        
        # 计算ROI（排除法：当前位置 -> 目标方向 -> 屏幕边界）
        # 计算移动方向
        move_dir_x = 1 if dx > 0 else -1 if dx < 0 else 0
        move_dir_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        # ROI边界：从当前位置沿移动方向到屏幕边界
        roi_margin = 100  # 垂直于移动方向的缓冲区
        
        if move_dir_x > 0:  # 向右移动
            roi_x1 = max(0, int(center_x - roi_margin))
            roi_x2 = 1920
        elif move_dir_x < 0:  # 向左移动
            roi_x1 = 0
            roi_x2 = min(1920, int(center_x + roi_margin))
        else:  # X轴不动
            roi_x1 = max(0, int(center_x - roi_margin))
            roi_x2 = min(1920, int(center_x + roi_margin))
        
        if move_dir_y > 0:  # 向下移动
            roi_y1 = max(0, int(center_y - roi_margin))
            roi_y2 = 1080
        elif move_dir_y < 0:  # 向上移动
            roi_y1 = 0
            roi_y2 = min(1080, int(center_y + roi_margin))
        else:  # Y轴不动
            roi_y1 = max(0, int(center_y - roi_margin))
            roi_y2 = min(1080, int(center_y + roi_margin))
        
        # 通过override_pipeline传递ROI给下次Recognition
        current_task = argv.node_name
        context.override_pipeline({
            current_task: {
                "recognition": "Custom",
                "custom_recognition": "FindCrosshair",
                "custom_recognition_param": {
                    "threshold": 0.6,
                    "roi": [roi_x1, roi_y1, roi_x2, roi_y2]
                }
            }
        })
        
        log(f"[MoveStick] ROI(排除法): ({roi_x1}, {roi_y1}) - ({roi_x2}, {roi_y2}), 方向=({move_dir_x}, {move_dir_y})")
        
        # 记录当前位置，用于下次ROI计算
        self.last_crosshair_x = center_x
        self.last_crosshair_y = center_y
        
        # 返回True让节点完成，触发JumpBack循环（next为空时JumpBack回上级节点）
        return True
    
    def _calculate_stick_values(self, dx, dy, tolerance=10):
        """
        计算摇杆值（使用校准映射表）
        
        Args:
            dx, dy: 偏移量（像素）
            tolerance: 容差，小于此值的轴不移动
        
        Returns:
            [(stick_x, stick_y, duration), ...] 移动指令列表
            每个元素是一次独立的移动（纯X或纯Y）
        """
        from stick_calibration_map import find_stick_params_by_distance
        
        log(f"[MoveStick] [_calculate_stick_values] 输入: dx={dx:.1f}, dy={dy:.1f}, tolerance={tolerance}")
        
        moves = []
        
        # 分别处理X轴和Y轴
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # X轴移动
        if abs_dx >= tolerance:
            result_x = find_stick_params_by_distance(abs_dx, axis='x')
            if result_x:
                stick_x_val, base_duration, actual_dist_x = result_x
                stick_x = int(stick_x_val * (1 if dx > 0 else -1))
                
                # 远距离优化
                multiplier = 1
                if abs_dx > 247:
                    multiplier = max(1, round(abs_dx / 247))
                    multiplier = min(multiplier, 3)
                
                duration_x = base_duration * multiplier
                expected_dist_x = actual_dist_x * multiplier  # 按比例放大预计距离
                
                if multiplier > 1:
                    log(f"[MoveStick] X轴远距离优化: {abs_dx:.1f}px, {multiplier}x, duration={base_duration:.2f}s→{duration_x:.2f}s")
                
                moves.append((stick_x, 0, duration_x))
                log(f"[MoveStick] X轴移动: stick={stick_x}, duration={duration_x:.2f}s, 预计移动={expected_dist_x:.1f}px")
            else:
                log(f"[MoveStick] ⚠ X轴未找到合适参数")
        
        # Y轴移动
        if abs_dy >= tolerance:
            result_y = find_stick_params_by_distance(abs_dy, axis='y')
            if result_y:
                stick_y_val, base_duration, actual_dist_y = result_y
                stick_y = int(stick_y_val * (1 if dy > 0 else -1))
                
                # 远距离优化
                multiplier = 1
                if abs_dy > 143:  # Y轴最大距离约143px (0.25s, 32767)
                    multiplier = max(1, round(abs_dy / 143))
                    multiplier = min(multiplier, 3)
                
                duration_y = base_duration * multiplier
                expected_dist_y = actual_dist_y * multiplier  # 按比例放大预计距离
                
                if multiplier > 1:
                    log(f"[MoveStick] Y轴远距离优化: {abs_dy:.1f}px, {multiplier}x, duration={base_duration:.2f}s→{duration_y:.2f}s")
                
                moves.append((0, stick_y, duration_y))
                log(f"[MoveStick] Y轴移动: stick={stick_y}, duration={duration_y:.2f}s, 预计移动={expected_dist_y:.1f}px")
            else:
                log(f"[MoveStick] ⚠ Y轴未找到合适参数")
        
        if not moves:
            log(f"[MoveStick] 两轴都在容差范围内，无需移动")
            return []
        
        log(f"[MoveStick] 生成 {len(moves)} 个移动指令")
        return moves
