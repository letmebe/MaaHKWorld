"""
摇杆校准映射表
通过test_stick_calibration.py生成
注意其中的距离是单方向的dx或dy！

重要：X轴和Y轴灵敏度不同
- X轴 (20000, 1.0s) → 497px
- Y轴 (20000, 1.0s) → 221px
- Y轴灵敏度约为X轴的44.5%
"""

# X轴校准映射表（原始数据）
X_AXIS_DURATION_MAP = {
    0.05: {
        30000: 35.0,
        25000: 26.0,
        20000: 19.0,
        15000: 15.0,
        12000: 6.0,
        10000: 4.0,
    },
    0.08: {
        32767: 78.0,
        30000: 57.0,
        25000: 54.0,
        20000: 32.0,
        15000: 19.0,
        12000: 13.0,
        10000: 7.0,
    },
    0.1: {
        32767: 79.0,
        30000: 69.0,
        25000: 63.0,
        20000: 44.0,
        15000: 23.0,
        12000: 15.0,
        10000: 8.0,
    },
    0.12: {
        32767: 103.0,
        30000: 92.0,
        25000: 72.0,
        20000: 50.0,
        15000: 30.0,
        12000: 17.0,
        10000: 9.0,
    },
    0.15: {
        32767: 142.0,
        30000: 111.0,
        25000: 80.0,
        20000: 57.0,
        15000: 38.0,
        12000: 20.0,
        10000: 10.0,
    },
    0.2: {
        32767: 220.0,
        30000: 170.0,
        25000: 126.0,
        20000: 76.0,
        15000: 49.0,
        12000: 28.0,
        10000: 13.0,
    },
    0.25: {
        32767: 247.0,
        30000: 231.0,
        25000: 145.0,
        20000: 95.0,
        15000: 52.0,
        12000: 34.0,
        10000: 17.0,
    },
}

# Y轴校准映射表（基于实测数据重新估算）
# 实测：Y轴 (20000, 1.0s) → 221px
# 实测：Y轴 (32767, 1.0s) → 574px
# 注意：实际游戏中Y轴可能比预期更灵敏
Y_AXIS_DURATION_MAP = {
    0.05: {
        # 基于1.0s数据按比例缩小，考虑非线性
        30000: 28.0,
        25000: 20.0,
        20000: 11.0,
        15000: 7.0,
        12000: 4.0,
        10000: 2.0,
    },
    0.08: {
        32767: 46.0,
        30000: 35.0,
        25000: 28.0,
        20000: 18.0,
        15000: 11.0,
        12000: 7.0,
        10000: 4.0,
    },
    0.1: {
        32767: 57.0,
        30000: 44.0,
        25000: 35.0,
        20000: 22.0,
        15000: 14.0,
        12000: 9.0,
        10000: 5.0,
    },
    0.12: {
        32767: 69.0,
        30000: 53.0,
        25000: 42.0,
        20000: 27.0,
        15000: 17.0,
        12000: 11.0,
        10000: 6.0,
    },
    0.15: {
        32767: 86.0,
        30000: 66.0,
        25000: 53.0,
        20000: 33.0,
        15000: 21.0,
        12000: 13.0,
        10000: 7.0,
    },
    0.2: {
        32767: 115.0,
        30000: 88.0,
        25000: 70.0,
        20000: 44.0,
        15000: 28.0,
        12000: 18.0,
        10000: 9.0,
    },
    0.25: {
        32767: 143.0,
        30000: 110.0,
        25000: 88.0,
        20000: 55.0,
        15000: 35.0,
        12000: 22.0,
        10000: 11.0,
    },
}

def find_stick_params_by_distance(target_distance, preferred_duration=None, axis='x'):
    """
    根据目标距离查找最优摇杆值和持续时间
    
    Args:
        target_distance: 目标移动距离（像素），单方向距离（dx或dy的绝对值）
        preferred_duration: 首选持续时间（秒），None表示自动选择
        axis: 轴类型 'x' 或 'y'
    
    Returns:
        (stick_value, duration, actual_distance) 或 None
    """
    if target_distance <= 0:
        return None
    
    # 选择对应的映射表
    duration_map_dict = X_AXIS_DURATION_MAP if axis == 'x' else Y_AXIS_DURATION_MAP
    
    best_result = None
    best_diff = float('inf')
    
    durations_to_try = [preferred_duration] if preferred_duration else sorted(duration_map_dict.keys())
    
    for duration in durations_to_try:
        if duration not in duration_map_dict:
            continue
        
        duration_map = duration_map_dict[duration]
        
        for stick, dist in duration_map.items():
            if dist <= 0:
                continue
            
            diff = abs(dist - target_distance)
            if diff < best_diff:
                best_diff = diff
                best_result = (stick, duration, dist)
    
    return best_result

def find_stick_params_for_axis(dx, dy, preferred_duration=None):
    """
    根据X/Y偏移查找摇杆参数
    
    Args:
        dx: X轴偏移量（可正可负）
        dy: Y轴偏移量（可正可负）
        preferred_duration: 首选持续时间（秒）
    
    Returns:
        (stick_x, stick_y, duration, actual_dx, actual_dy) 或 None
        其中stick_x和stick_y包含方向信息（正负号）
        actual_dx和actual_dy是实际能达到的移动距离（带符号）
    """
    if dx == 0 and dy == 0:
        return None
    
    # 分别处理X轴和Y轴
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    
    result_x = None
    result_y = None
    
    # 如果dx不为0，查找X轴参数
    if abs_dx > 0:
        result_x = find_stick_params_by_distance(abs_dx, preferred_duration, axis='x')
    
    # 如果dy不为0，查找Y轴参数
    if abs_dy > 0:
        result_y = find_stick_params_by_distance(abs_dy, preferred_duration, axis='y')
    
    # 确定共同的duration
    if preferred_duration:
        common_duration = preferred_duration
    elif result_x and result_y:
        # 如果两个轴都有结果，选择较大的duration以确保都能达到目标距离
        common_duration = max(result_x[1], result_y[1])
    elif result_x:
        common_duration = result_x[1]
    elif result_y:
        common_duration = result_y[1]
    else:
        return None
    
    # 使用共同的duration重新查找（如果需要）
    if result_x and result_x[1] != common_duration:
        result_x = find_stick_params_by_distance(abs_dx, common_duration, axis='x')
    
    if result_y and result_y[1] != common_duration:
        result_y = find_stick_params_by_distance(abs_dy, common_duration, axis='y')
    
    # 计算带方向的摇杆值
    if result_x:
        stick_x_val, _, actual_dist_x = result_x
        stick_x = int(stick_x_val * (1 if dx > 0 else -1))
    else:
        stick_x = 0
        actual_dist_x = 0
    
    if result_y:
        stick_y_val, _, actual_dist_y = result_y
        stick_y = int(stick_y_val * (1 if dy > 0 else -1))
    else:
        stick_y = 0
        actual_dist_y = 0
    
    return (stick_x, stick_y, common_duration, actual_dist_x, actual_dist_y)