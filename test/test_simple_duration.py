"""
测试简化的duration倍增策略
"""
import sys
import os

# 添加agent目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from stick_calibration_map import find_stick_params_for_axis

def calculate_duration_simple(dx, dy):
    """
    简化的duration计算：距离/247取整 * 0.25s
    """
    max_distance = max(abs(dx), abs(dy))
    
    if max_distance <= 247:
        # 正常查找参数
        result = find_stick_params_for_axis(dx, dy)
        if result:
            return result[2]  # duration
        return 0.05
    
    # 距离超过247，按比例增加duration
    multiplier = max(1, round(max_distance / 247))
    multiplier = min(multiplier, 3)  # 限制最大3倍，避免过冲
    
    duration = 0.25 * multiplier
    return duration

def test_simple_strategy():
    """测试简化策略"""
    
    print("=" * 80)
    print("🚀 简化版duration倍增策略测试")
    print("=" * 80)
    print("\n策略说明:")
    print("- 距离 ≤ 247px: 使用校准表正常参数")
    print("- 距离 > 247px: duration = 0.25s × round(距离/247)")
    print("- 最大倍数: 3倍（即最长0.75s，避免过冲）")
    print()
    
    test_cases = [
        {"name": "小距离", "dx": 50, "dy": 30},
        {"name": "中等距离", "dx": 150, "dy": 100},
        {"name": "接近阈值", "dx": 240, "dy": 200},
        {"name": "刚超阈值", "dx": 250, "dy": 200},
        {"name": "2倍距离", "dx": 500, "dy": 300},
        {"name": "3倍距离", "dx": 750, "dy": 500},
        {"name": "4倍距离", "dx": 1000, "dy": 600},
        {"name": "超大距离", "dx": 1920, "dy": 1080},
    ]
    
    print(f"{'场景':<15} {'dx':<8} {'dy':<8} {'最大距离':<10} {'原duration':<12} {'新duration':<12} {'倍数'}")
    print("-" * 80)
    
    for case in test_cases:
        dx, dy = case["dx"], case["dy"]
        max_dist = max(abs(dx), abs(dy))
        
        # 原始duration
        result = find_stick_params_for_axis(dx, dy)
        if result:
            orig_duration = result[2]
        else:
            orig_duration = 0.05
        
        # 新duration
        new_duration = calculate_duration_simple(dx, dy)
        
        # 计算倍数
        if orig_duration > 0:
            multiplier = new_duration / orig_duration
        else:
            multiplier = 0
        
        print(f"{case['name']:<15} {dx:<8} {dy:<8} {max_dist:<10} {orig_duration:<12.2f} {new_duration:<12.2f} {multiplier:.1f}x")
    
    print("\n" + "=" * 80)
    print("💡 关键发现")
    print("=" * 80)
    print("""
1. ✅ 简单直接：距离越大，duration越长
2. ✅ 易于理解：distance/247取整 * 0.25s
3. ✅ 无需分段：一次移动完成，减少迭代次数
4. ⚠️  需要注意：过长的duration可能导致过冲

示例计算：
- 距离250px: multiplier = round(250/247) = 1, duration = 0.25s
- 距离500px: multiplier = round(500/247) = 2, duration = 0.50s
- 距离750px: multiplier = round(750/247) = 3, duration = 0.75s
- 距离1920px: multiplier = round(1920/247) = 8→限制为3, duration = 0.75s
""")


if __name__ == "__main__":
    test_simple_strategy()
