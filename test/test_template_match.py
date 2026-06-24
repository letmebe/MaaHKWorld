"""
临时测试脚本 - 测试模板匹配
"""
import cv2
import numpy as np
from pathlib import Path

# 路径 - 自动检测
dev_path = Path(__file__).parent.parent / 'assets' / 'resource' / 'image'
release_path = Path(__file__).parent.parent / 'resource' / 'image'
image_dir = dev_path if dev_path.exists() else release_path

test_image_path = image_dir / 'test.png'
template_path = image_dir / 'bozhongyaocai.png'

# 读取图片
print(f"测试图片: {test_image_path}")
print(f"模板图片: {template_path}")

test_img = cv2.imread(str(test_image_path))
template_img = cv2.imread(str(template_path))

if test_img is None:
    print("❌ 无法读取测试图片")
    exit(1)

if template_img is None:
    print("❌ 无法读取模板图片")
    exit(1)

print(f"✓ 测试图片尺寸: {test_img.shape}")
print(f"✓ 模板图片尺寸: {template_img.shape}")

# ROI区域
roi = [1750, 950, 170, 130]
x, y, w, h = roi

# 提取ROI区域
roi_img = test_img[y:y+h, x:x+w]
print(f"✓ ROI区域: {roi}")
print(f"✓ ROI图片尺寸: {roi_img.shape}")

# 模板匹配
result = cv2.matchTemplate(roi_img, template_img, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

print(f"\n=== 匹配结果 ===")
print(f"最大匹配分数: {max_val:.4f}")
print(f"匹配位置: {max_loc}")
print(f"阈值0.6: {'✓ 命中' if max_val >= 0.6 else '✗ 未命中'}")
print(f"阈值0.7: {'✓ 命中' if max_val >= 0.7 else '✗ 未命中'}")

# 在ROI上绘制匹配结果
result_img = test_img.copy()

# 绘制ROI框（绿色）
cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
cv2.putText(result_img, f"ROI", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# 如果匹配成功，绘制匹配位置（红色）
if max_val >= 0.6:
    match_x = x + max_loc[0]
    match_y = y + max_loc[1]
    th, tw = template_img.shape[:2]
    cv2.rectangle(result_img, (match_x, match_y), (match_x+tw, match_y+th), (0, 0, 255), 2)
    cv2.putText(result_img, f"Match: {max_val:.3f}", (match_x, match_y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

# 保存结果图片
output_path = image_dir / 'test_result.png'
cv2.imwrite(str(output_path), result_img)
print(f"\n✓ 结果已保存: {output_path}")

# 显示ROI区域和模板
cv2.imwrite(str(image_dir / 'roi_area.png'), roi_img)
cv2.imwrite(str(image_dir / 'template.png'), template_img)
print(f"✓ ROI区域已保存: {image_dir / 'roi_area.png'}")
print(f"✓ 模板已保存: {image_dir / 'template.png'}")