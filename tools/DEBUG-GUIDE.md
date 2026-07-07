# MaaFramework调试指南

## 问题

使用 `tools/MFAAvalonia` 调试时：
- ❌ 日志只到任务级别
- ❌ 不显示Pipeline节点执行细节
- ❌ 不显示识别命中/未命中

## 正确的调试方式

### 1. 使用任务调试工具（推荐）

```bash
# 列出所有可用任务
python tools/debug_task.py --list

# 调试任务（自动应用interface.json中的参数）
python tools/debug_task.py FarmPlant

# 调试任务并指定选项
python tools/debug_task.py FarmPlant --option crop_name=冰魄辣椒

# 调试好友浇水
python tools/debug_task.py FriendWatering --option friend_list_json='{"friend_list": ["Trueman"]}'

# 调试探险派遣
python tools/debug_task.py Dispatch --option dispatch_config='{"locations": ["春溪原"], "persons": {"春溪原": ["阿噗", "啾啾", "哆哆"]}}'
```

**优势**：
- ✅ 自动读取interface.json中的任务配置
- ✅ 自动应用pipeline_override参数
- ✅ 支持选项参数覆盖
- ✅ 无需手动指定复杂的参数结构

### 2. 使用Pipeline调试工具（高级）

```bash
# 列出Pipeline节点
python tools/debug_pipeline.py list --pipeline assets/resource/pipeline/farm.json

# 运行Pipeline（无参数）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farm.json \
  --task "农场种植_开始"

# 运行Pipeline（带参数）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farmforfriends.json \
  --task "好友浇水_好友列表循环" \
  --param tools/example_params/friend_watering.json
```

```bash
# 运行农田种植（无参数）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farm.json \
  --task "农场种植_开始"

# 运行好友浇水（带参数 - JSON字符串）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farmforfriends.json \
  --task "好友浇水_好友列表循环" \
  --param '{"custom_action_param": "{\"friend_list\": [\"Trueman\"]}"}'

# 运行探险派遣（带参数 - JSON文件）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/dispatch_loop.json \
  --task "探险派遣循环版_初始化循环" \
  --param dispatch_config.json
```

**参数格式**：

1. **JSON字符串**（直接在命令行）：
   ```bash
   --param '{"custom_action_param": "..."}'
   ```

2. **JSON文件**（复杂参数推荐）：
   ```bash
   --param tools/example_params/friend_watering.json
   ```
   
   项目已提供示例参数文件：
   - `tools/example_params/friend_watering.json` - 好友浇水
   - `tools/example_params/dispatch.json` - 探险派遣
   - `tools/example_params/farm_plant.json` - 农田种植

### 3. 常见任务参数示例

#### 好友浇水
```bash
# 使用JSON字符串
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farmforfriends.json \
  --task "好友浇水_好友列表循环" \
  --param '{"custom_action_param": "{\"friend_list\": [\"Trueman\"]}"}'

# 使用参数文件（推荐）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farmforfriends.json \
  --task "好友浇水_好友列表循环" \
  --param tools/example_params/friend_watering.json
```

#### 探险派遣
```bash
# 使用参数文件（推荐）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/dispatch_loop.json \
  --task "探险派遣循环版_初始化循环" \
  --param tools/example_params/dispatch.json
```

#### 农田种植（选择作物）
```bash
# 使用参数文件（推荐）
python tools/debug_pipeline.py run \
  --pipeline assets/resource/pipeline/farm.json \
  --task "农场种植_开始" \
  --param tools/example_params/farm_plant.json
```

### 3. 输出示例

#### 任务调试输出
```
============================================================
任务调试工具
任务: FarmPlant - 农田种植
入口: 农场种植_开始
============================================================

Pipeline参数覆盖:
{
  "通用_传送_查找目标位置": {
    "recognition": {
      "type": "OCR",
      "param": {
        "expected": ["农贸作物"]
      }
    }
  },
  "通用_传送_等待加载": {
    "next": ["农场种植_传送完成等待"]
  }
}

[OK] 资源加载成功
[OK] 调试模式已启用
[OK] 已应用参数覆盖

============================================================
开始执行任务...
============================================================

[Task Start] 农场种植_开始
  [Recognition] DirectHit: 命中 ✓
  [Action] DoNothing
[Task End] 农场种植_开始

[Task Start] 通用_传送_查找目标位置
  [Recognition] OCR: 命中 ✓
  [Action] ExtractOCRTarget
[Task End] 通用_传送_查找目标位置

...

============================================================
任务执行完成
============================================================
```

#### Pipeline调试输出
```
============================================================
Pipeline调试工具
Pipeline文件: assets/resource/pipeline/farm.json
入口任务: 农场种植_开始
============================================================
[OK] 资源加载成功
[OK] 调试模式已启用

============================================================
开始执行Pipeline...
============================================================

[Task Start] 农场种植_开始
  [Recognition] DirectHit: 命中 ✓
  [Action] DoNothing
[Task End] 农场种植_开始

...

============================================================
Pipeline执行完成
============================================================
```

## 工具对比

| 工具 | 用途 | 优势 | 适用场景 |
|------|------|------|---------|
| `debug_task.py` | 调试interface任务 | 自动应用参数配置 | 调试完整任务流程 |
| `debug_pipeline.py` | 调试Pipeline节点 | 灵活指定参数 | 调试特定Pipeline或节点 |
| MFAAvalonia | 实际运行任务 | 完整UI界面 | 生产环境使用 |

## 其他调试工具

### 1. 查看自定义Action日志

```bash
# 查看agent日志（自定义Action输出）
tail -f agent/logs/agent-YYYYMMDD.log
```

### 2. 查看MaaFramework日志

```bash
# 查看框架日志
tail -f tools/MFAAvalonia/logs/log-YYYYMMDD.log
```

### 3. 单元测试

```bash
# 测试摇杆校准
python test/test_stick_calibration.py

# 测试瞄准功能
python test/test_aim_with_calibration.py
```

## 调试技巧

### 1. 单独测试识别器

```python
from crosshair_recognition import FindCrosshairRecognition
import cv2

# 加载测试图片
image = cv2.imread('test_image.png')

# 创建识别器
recognition = FindCrosshairRecognition()

# 测试识别
result = recognition.analyze(None, MockArgv(image, {'threshold': 0.8}))
print(f"识别结果: {result}")
```

### 2. 单独测试动作

```python
from custom_action import TapButton

# 创建动作
action = TapButton()

# 测试执行
action.run(None, MockArgv(button='A', duration=0.1))
```

### 3. 查看Pipeline配置

```python
import json

with open('assets/resource/pipeline/farm.json', 'r', encoding='utf-8') as f:
    pipeline = json.load(f)

# 查看特定节点
node = pipeline['农场种植_开始']
print(json.dumps(node, indent=2, ensure_ascii=False))
```

## 常见问题

### Q: 为什么MFAAvalonia日志不够详细？

A: MFAAvalonia是UI界面，只输出任务级别的日志。要查看节点执行细节，需要使用调试工具或直接调用MaaFramework API。

### Q: 如何查看识别是否命中？

A: 使用 `debug_pipeline.py run` 命令，会输出每个识别器的命中状态。

### Q: 如何调试自定义识别器/动作？

A: 查看 `agent/logs/agent-YYYYMMDD.log`，所有自定义组件都会输出详细日志。