# 开发指南

## 环境准备

### 1. 克隆项目

```bash
git clone https://github.com/letmebe/HKWorld.git
cd HKWorld
git submodule update --init --recursive  # 初始化 OCR 模型 submodule
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装虚拟手柄驱动

下载并安装 [ViGEmBus](https://github.com/ViGEm/ViGEmBus) 驱动。

## 项目结构

> 项目布局参考 [MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) 官方模板

```
HKWorld/
├── .github/
│   ├── workflows/
│   │   ├── check.yml            # CI 检查
│   │   └── install.yml           # CI 构建发布
│   └── cliff.toml                # git-cliff 变更日志配置
├── agent/                        # 自定义扩展
│   ├── agent_server.py           # Agent 服务注册
│   ├── custom_action.py          # 虚拟手柄控制、窗口激活
│   ├── fishing_recognition.py    # 多模板匹配识别器（核心）
│   └── fishing_action.py         # 识别结果处理动作
├── assets/
│   ├── MaaCommonAssets/          # OCR 模型 submodule
│   ├── resource/                 # 项目资源
│   │   ├── image/                # 图像模板（14个）
│   │   ├── model/
│   │   │   └── .gitignore        # 排除 ocr 目录
│   │   └── pipeline/             # Pipeline 配置
│   │       └── fishing.json
│   ├── config/                   # 运行时配置（自动生成，git忽略）
│   └── interface.json            # ProjectInterface 配置
├── tools/
│   ├── install.py                # CI 安装脚本
│   ├── configure.py              # OCR 模型配置
│   └── requirements.txt          # CI Python 依赖
├── venv/                         # Python 虚拟环境
├── .gitmodules                   # submodule 配置
├── requirements.txt              # Python 依赖
└── README.md
```

## CI/CD 配置

### GitHub Actions 工作流

| 文件 | 触发条件 | 功能 |
|------|----------|------|
| check.yml | push/PR | 代码检查、npm ci 验证 |
| install.yml | push tag `v*` | 构建发布包 |

### 发布流程

1. 确保 GitHub 仓库设置：`Settings` → `Actions` → `General` → `Read and write permissions`

2. 提交代码并推送 tag：
```bash
git add .
git commit -m "feat: 新功能"
git push
git tag v1.0.0
git push origin v1.0.0
```

3. CI 自动执行：
   - 下载 MaaFramework
   - 下载 MFAAvalonia
   - 配置 OCR 模型
   - 打包为 `MaaHKWorld-win-x86_64-*.zip`
   - 发布到 Releases

### 当前平台支持

仅支持 **Windows x86_64**，其他平台已在 `install.yml` 中禁用。

如需启用其他平台，修改 matrix 配置：
```yaml
strategy:
  matrix:
    os: [win, macos, linux, android]
    arch: [aarch64, x86_64]
```

## 核心架构

### 钓鱼循环流程

```
MFAAvalonia 启动任务
    ↓
Pipeline: 激活游戏窗口（Minimize+Restore）
    ↓
Pipeline: 初始化等待 5秒
    ↓
Pipeline: 激活手柄模式（点击两次 A）
    ↓
循环: 钓鱼主循环
    ├─ 截图（BitBlt）
    ├─ CustomRecognition.analyze()
    │   ├─ 匹配 paogan/lagan/quxiao → 选最高分
    │   ├─ 匹配 X_quick/quick_B → 选高分
    │   ├─ 匹配 X/Y/A/B_single → 选最高分
    │   ├─ 匹配 to_bag/fanui/quxiaozhunbei
    │   └─ 返回最佳匹配
    ├─ CustomAction.run()
    │   └─ 执行手柄按键
    └─ 下一轮循环
```

### 关键组件

#### 1. CustomRecognition (fishing_recognition.py)

一次截图，匹配多个模板，返回最高分：

```python
class FishingMultiMatchRecognition(CustomRecognition):
    def analyze(self, context, argv):
        image = argv.image  # 截图
        
        # 同一区域模板同时匹配，返回分数最高的
        for name in ['paogan', 'lagan', 'quxiao']:
            score = match_template(image, name)
        
        # 选最高分返回
        return AnalyzeResult(box, detail)
```

**优势**：避免原生 Pipeline 每个任务独立截图。

#### 2. CustomAction (fishing_action.py)

根据识别结果执行对应动作：

```python
class FishingMultiMatchAction(CustomAction):
    def run(self, context, argv):
        detail = argv.reco_detail.raw_detail['best']['detail']
        action = detail['action']  # tap_A, tap_X, quick_tap_X...
        
        # 执行手柄按键
        controller.tap_button('A')
```

#### 3. GamepadController (custom_action.py)

虚拟手柄控制：

```python
class GamepadController:
    def tap_button(self, button, duration=0.1)
    def quick_tap(self, button, count=2, interval=0.15)
    def long_press(self, button, duration=3.0)
```

### Pipeline 配置 (fishing.json)

```json
{
    "钓鱼主循环": {
        "recognition": "DirectHit",
        "action": "DoNothing",
        "timeout": -1,  // 无限循环
        "next": ["钓鱼多模板匹配"]
    },
    "钓鱼多模板匹配": {
        "recognition": "Custom",
        "custom_recognition": "FishingMultiMatch",
        "action": "Custom",
        "custom_action": "FishingMultiMatchAction",
        "next": ["钓鱼主循环"]
    }
}
```

## 匹配逻辑

### 同区域模板选最高分

| 模板组 | 区域 | 阈值 | 逻辑 |
|--------|------|------|------|
| paogan/lagan/quxiao | roi_fishing | 0.6 | 同时匹配，选最高分 |
| X_quick/quick_B | roi_quick | 0.7 | 同时匹配，选高分 |
| X/Y/A/B_single | roi_quick | 0.7 | 同时匹配，选最高分 |
| to_bag | roi_bag | 0.6 | 单独匹配 |
| fanui | roi_return | 0.6 | 单独匹配 |
| quxiaozhunbei | 全屏 | 0.6 | 单独匹配 |

## 性能优化

### 1. 异步日志

```python
# 主线程只 put，不阻塞
LOG_QUEUE.put(f"{timestamp} {message}\n")

# 后台线程写入文件，I/O 释放 GIL
def _log_writer():
    with open(LOG_FILE, 'a', buffering=8192) as f:
        while running:
            msg = LOG_QUEUE.get()
            f.write(msg)
```

**效果**：日志写入不影响主线程性能。

### 2. 窗口激活

```python
# 不需要真正前台，只需恢复显示
win32gui.ShowWindow(hwnd, SW_MINIMIZE)
time.sleep(0.1)
win32gui.ShowWindow(hwnd, SW_RESTORE)
```

**效果**：窗口不必在前台，MaaFramework 可正常 BitBlt 截图。

### 3. 灰度图模板匹配（关键优化）

**问题**：彩色图模板匹配耗时过长（80ms/次），12个模板累计约960ms，错过按键时机。

**解决**：参考原项目 `template_matcher.py` 改用灰度图匹配：

```python
# _load_templates: 加载时转为灰度图
template = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# _match_template: ROI转灰度后匹配
gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
result = cv2.matchTemplate(gray_roi, template, cv2.TM_CCOEFF_NORMED)
```

**性能对比**：

| 匹配方式 | 单次耗时 | 12次累计 | 效果 |
|----------|----------|----------|------|
| 彩色图（原） | ~80ms | ~960ms | 按键错过时机 ❌ |
| 灰度图（优） | ~25ms | ~300ms | 及时响应 ✅ |

**原理**：灰度图数据量为彩色图的1/3，匹配速度提升约3倍。

## 性能数据

| 操作 | 耗时 |
|------|------|
| 识别（匹配到） | 10-50ms |
| 识别（无匹配） | 200-400ms（灰度图优化后） |
| 按键动作 | 100-450ms |
| 日志写入 | 异步，不阻塞 |

## 调试

### 查看日志

```
tools/MFAAvalonia/logs/agent.log  # 自定义日志（识别、动作）
tools/MFAAvalonia/logs/log-*.log  # MaaFramework 日志
```

### 日志格式

```
[2026-05-23 00:50:10] [Recognition] 开始识别，图像尺寸: (1080, 1920, 3)
[2026-05-23 00:50:10] [Recognition] ✓ paogan (score: 0.973) | 耗时: 13.6ms
[2026-05-23 00:50:10] [Action] paogan → tap_A | 耗时: 112.2ms
```

## 参考资料

- [MaaFramework 官方文档](https://maafw.com/)
- [Pipeline 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-任务流水线协议.md)
- [ProjectInterface 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.3-ProjectInterfaceV2协议.md)

---

## 开发复盘

### 开发过程

#### 第一阶段：基础架构搭建
1. 创建 MaaFramework 项目结构
2. 配置 MFAAvalonia 通用 UI
3. 注册自定义识别器和动作
4. 实现虚拟手柄初始化

#### 第二阶段：核心功能实现
1. **CustomRecognition 实现难点**：
   - 发现：原生 Pipeline 每个任务独立截图，n 个任务 = n 次截图
   - 解决：使用 `CustomRecognition` 一次截图，按优先级匹配多个模板
   - 关键 API：`analyze()` 返回 `AnalyzeResult(box, detail)`

2. **识别逻辑优化**：
   - 问题：初始实现"第一个超过阈值就返回"，与原程序不符
   - 原程序：同一区域模板同时匹配，返回分数最高的
   - 修正：paogan/lagan/quxiao、X_quick/quick_B、X/Y/A/B_single 都改为匹配所有后选最高分

3. **按钮映射修正**：
   - 发现：Y_single 错误映射到 tap_X
   - 修正：Y_single → tap_Y，并添加 tap_Y 处理

#### 第三阶段：性能优化
1. **日志优化**：
   - 问题：日志文件写入增加循环耗时
   - 尝试1：`atexit` 退出时写入 → 进程被杀，日志丢失
   - 解决：异步日志线程 + Queue，主线程只 `put()`，后台线程写入
   - 原理：文件 I/O 释放 GIL，不影响主线程性能

2. **窗口激活优化**：
   - 问题：SetForegroundWindow 被 Windows 前台锁定限制拒绝
   - 解决：`SW_MINIMIZE + SW_RESTORE` 让窗口恢复显示
   - 效果：窗口不必在前台，MaaFramework 可正常截图

#### 第四阶段：阈值校准
对比原程序验证所有阈值：
- paogan/lagan/quxiao: 0.6 ✓
- X_quick/quick_B: 0.7 ✓
- X/Y/A/B_single: 0.7 ✓
- to_bag/fanui/quxiaozhunbei: 0.6 ✓

### 关键发现

1. **MaaFramework Pipeline 效率问题**：
   - 原生 Pipeline 任务独立截图
   - CustomRecognition 可一次截图多次匹配

2. **窗口状态对截图的影响**：
   - 窗口最小化时 BitBlt 截图失败，改为FramePool
   - Minimize+Restore 让窗口恢复显示但不必前台
   - 框架文档中指出：FramePool 和 PrintWindow 内置了伪最小化支持：当目标窗口被最小化时，会将窗口设为透明并开启点击穿透，以不激活的方式恢复窗口，从而在不打扰用户的情况下继续截图。其他截图方式在窗口最小化后无法获取有效内容，请避免窗口最小化。这就是为什么可以在窗口最小化时进行截图的原因

3. **Python 多线程与 GIL**：
   - 文件 I/O 操作释放 GIL
   - 日志线程不影响主线程性能

---

## 传送功能实现（2026-06-09）

### 功能概述

实现通用的传送到指定地点功能，支持传送到"派遣小屋"、"培养箱"等地点。

### 技术方案

#### 1. Pipeline流程设计

```
激活游戏窗口 → 激活手柄 → 打开菜单(START) 
→ 方向键导航到居所(下-下-下-右) → 确认(A) 
→ 切换管理Tab(RB) → OCR识别目标位置 
→ 晃动摇杆激活准星 → MoveStick循环瞄准 → 点击确认 → 传送
```

#### 2. 自定义动作实现

**TapButton** - 点击手柄按钮
```python
# 支持的按钮
A, B, X, Y, START, BACK, LB, RB
DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT
LEFT_THUMB, RIGHT_THUMB
```

**ExtractOCRTarget** - 提取OCR目标位置
- 从OCR识别结果提取目标位置（box中心点）
- 通过`context.override_pipeline()`动态设置MoveStick参数
- 不需要自己截图，使用MaaFramework的截图

**WiggleStick** - 晃动摇杆激活准星
- 使用左摇杆左右晃动激活准星显示
- 参数：stick_value（默认10000），duration（默认0.1s）

#### 3. 关键技术点

**双重JSON编码问题**：
- MaaFramework传递的custom_action_param被双重JSON编码
- 解决方案：
```python
parsed = json.loads(param_str)
if isinstance(parsed, str):
    params = json.loads(parsed)  # 第二次解析
else:
    params = parsed
```

**OCR结果传递给MoveStick**：
- 使用ExtractOCRTarget提取目标位置
- 通过`context.override_pipeline()`动态修改下一个任务的参数
- MoveStick从参数获取目标坐标

**准星激活问题**：
- 打开菜单后准星默认不显示
- 使用WiggleStick晃动左摇杆激活准星
- 晃动流程：右(10000, 0) 0.1s → 左(-10000, 0) 0.1s

### 文件结构

**新增文件**：
- `assets/resource/pipeline/teleport.json` - 传送任务Pipeline
- `agent/extract_ocr_target.py` - 提取OCR目标位置
- `agent/wiggle_stick.py` - 晃动摇杆激活准星

**修改文件**：
- `agent/custom_action.py` - 添加TapButton动作，支持更多按钮
- `agent/agent_server.py` - 注册新的自定义动作
- `assets/interface.json` - 添加传送任务配置

### 测试验证

**测试流程**：
1. 激活游戏窗口 ✓
2. 激活手柄模式 ✓
3. 打开菜单（START键）✓
4. 方向键导航到居所 ✓
5. 切换管理Tab（RB键）✓
6. OCR识别目标位置 ✓
7. 晃动准星激活显示 ✓（使用WiggleStick）
8. MoveStick循环瞄准 ✓（使用左摇杆，最小值10000，持续时间0.15s）
9. 点击确认传送 ✓

### 注意事项

1. **游戏内按键映射**：
   - 菜单键：START（不是BACK）
   - 方向键：DPAD_UP/DOWN/LEFT/RIGHT
   - 确认键：A
   - 切换Tab：RB

2. **准星显示问题**：
   - 菜单界面默认不显示准星
   - 需要先晃动摇杆激活准星显示
   - 使用WiggleStick动作实现

3. **OCR识别**：
   - 使用OCR识别目标地点（如"派遣小屋"）
   - 从box计算中心点作为目标位置
   - 通过context传递给MoveStick
 4. **灰度图 vs 彩色图匹配性能**：
    - 彩色图：80ms/次，12模板累计960ms
    - 灰度图：25ms/次，12模板累计300ms
    - 关键：识别耗时直接影响按键及时性

---

## FramePool 截图技术详解

### 技术背景

FramePool 是 Windows Graphics Capture API 的核心组件，基于 DirectX 11 和 WinRT API，是 Windows 10 1903+ 引入的现代截图技术。

### 为什么支持后台截图（窗口最小化时仍可截图）

**传统 GDI 截图的限制**：
```
窗口 → GDI 表面 → CPU 内存拷贝 → 应用缓冲区
      (窗口不可见时表面无效)
```

**FramePool 的实现原理**：
```
窗口 → GPU SwapChain → GPU 纹理共享 → 应用读取
      (窗口不可见时 GPU 纹理仍存在)
```

**关键机制**：
1. **GPU 层面捕获**：不依赖 GDI 绘图表面，直接从 GPU 的 SwapChain 复制纹理
2. **内核态支持**：Windows Graphics Capture Driver 拦截 DirectX Present 调用
3. **纹理共享**：通过 DirectX 共享纹理机制，窗口不可见时 GPU 纹理仍然存在
4. **事件驱动**：监听窗口的 Present 事件，每次渲染时自动捕获

### 为什么支持点击穿透（不影响用户操作）

**实现机制**：
```
用户在其他窗口操作
    ↓
FramePool 持续截图（不需要窗口前台）
    ↓
自动化程序后台运行（识别 + SendMessage 输入）
    ↓
用户无感知
```

**关键配置**：
```json
{
    "screencap": "FramePool",    // 后台截图
    "mouse": "SendMessage",      // 后台输入
    "keyboard": "SendMessage"    // 后台输入
}
```

### 与传统 GDI 截图的对比

| 特性 | FramePool | GDI (BitBlt) |
|------|-----------|--------------|
| **底层机制** | DirectX GPU 纹理复制 | GDI 表面复制 |
| **窗口最小化** | ✅ 支持 | ❌ 失败或空白 |
| **窗口被遮挡** | ✅ 支持 | ❌ 被遮挡部分黑色 |
| **性能** | 极快（GPU 零拷贝） | 较慢（CPU 拷贝） |
| **CPU 占用** | 低（GPU 加速） | 高（CPU 拷贝） |
| **系统要求** | Win10 1903+ | WinXP+ |

### 性能优势的原因

1. **GPU 加速**：利用 GPU 并行处理能力
2. **零拷贝架构**：避免 CPU-GPU 数据传输
3. **纹理共享**：目标窗口和捕获程序共享同一 GPU 纹理
4. **预分配帧池**：避免运行时内存分配
5. **事件驱动**：窗口每次 Present 时自动触发捕获

**性能数据**：

| 操作 | GDI (BitBlt) | FramePool |
|------|--------------|-----------|
| 1080p 截图 | 5-15ms | 1-3ms |
| CPU 占用 | 5-10% | <1% |
| 窗口最小化 | 失败 | 正常 |
| 60fps 捕获 | 高 CPU | 低 CPU |

### 系统要求

| Windows 版本 | 支持 FramePool |
|--------------|----------------|
| Windows 10 1903 (Build 18362) | ✅ 首次引入 |
| Windows 10 2004+ | ✅ 性能改进 |
| Windows 11 | ✅ 完全支持 |
| Windows 10 1809 及更早 | ❌ 不支持 |
| Windows 7/8 | ❌ 不支持 |

### 技术栈

```
应用层: FramePool (MaaFramework 封装)
    ↓
API 层: Windows.Graphics.Capture (WinRT API)
    ├─ GraphicsCaptureItem (捕获项目)
    ├─ Direct3D11CaptureFramePool (帧池)
    └─ GraphicsCaptureSession (捕获会话)
    ↓
图形层: DirectX 11 (ID3D11Device, ID3D11Texture2D)
    ↓
内核层: Windows Graphics Capture Driver
```

### 项目配置

```json
// assets/interface.json
{
    "screencap": "FramePool",  // 使用最先进的截图技术
    "mouse": "SendMessage",    // 配合后台输入
    "keyboard": "SendMessage"  // 实现完全后台运行
}
```

**效果**：窗口可最小化，完全后台运行，不影响用户操作
   - 关键：识别耗时直接影响按键及时性

---

## 近期开发交互总结（2026-05-24）

### 项目初始化与迁移

1. **从模板项目迁移**：
   - 源：`C:\Users\yinwe\CodeBuddy\myfisher\maa-fisher`（排除 tools/）
   - 目标：`D:\Qsync\Development\HKWorld`
   - 合并 `.gitignore` 和 `README.md` 而非覆盖

2. **Git 配置**：
   - 更新全局用户配置为 GitHub 用户 `letmebe`
   - 确保提交正确关联到 GitHub 账户

### CI/CD 配置与调试

1. **GitHub Actions 问题修复**：
   - `package-lock.json` 同步问题 → 重新 `npm install`
   - `interface.json` 验证失败 → 修正 controller 配置为有效值
   - 缺少 OCR 模型 → 添加 `MaaCommonAssets` submodule
   - 缺少 `opencv-python` 依赖 → 更新 `requirements.txt`

2. **发布包配置**：
   - 修改 release 包名为 `MaaHKWorld`
   - 限制构建平台为 `Windows x86_64`
   - 添加 `contents: write` 权限

### 路径适配

1. **开发环境 vs 发布包**：
   - `interface.json` 使用开发环境路径（相对于 `tools/MFAAvalonia/`）
   - `install.py` 自动修正发布包路径
   - 启动脚本自动复制 `interface.json` 到 `tools/MFAAvalonia/`

2. **Agent 路径自动检测**：
   - `fishing_recognition.py` 模板目录自动检测
   - 启动脚本自动查找 `MFAAvalonia.exe`

### 运行时问题修复

1. **CustomAction 返回值问题**：
   - 问题：返回 `False` 导致 Pipeline 停止
   - 解决：所有分支返回 `True` 以保持循环

2. **任务入口错误**：
   - 问题：`entry: "钓鱼主循环"` 跳过初始化
   - 解决：改为 `entry: "激活游戏窗口"`

3. **日志统一**：
   - `ActivateGameWindow` 和 `ActivateGamepad` 改用 `logger.log()`
   - 日志按日期轮转，自动清理超过1天的旧日志

### 性能优化（关键）

1. **灰度图模板匹配**：
   - 问题：彩色图匹配耗时80ms/次，累计960ms，错过按键时机
   - 解决：参考原项目改用灰度图匹配
   - 效果：耗时降至25ms/次，累计300ms，**量级提升**

### 文档与规范

1. **更新文档**：
   - `README.md`：项目名称、快速开始、配置说明
   - `DEVELOPMENT.md`：性能优化、开发复盘
   - `.gitignore`：添加 `.codeartsdoer/`

    2. **启动脚本**：
       - 自动检测 Python 环境
       - 自动创建虚拟环境并安装依赖
       - 自动配置 `interface.json`

---

## 摇杆瞄准功能（2026-06-03 新增）

### 功能概述

新增使用摇杆实现准星瞄准到指定屏幕坐标的功能，支持：
- 摇杆校准测试
- 多尺度模板匹配（适配准星呼吸效果）
- 智能瞄准算法（防止移动过头）

### 核心组件

#### 1. GamepadController 扩展

```python
controller = GamepadController()

# 设置左摇杆（-32768 ~ 32767）
controller.set_left_stick(x=16384, y=0)  # 向右偏移 50%

# 设置右摇杆
controller.set_right_stick(x=0, y=16384)  # 向下偏移 50%

# 重置摇杆到中心
controller.reset_sticks()
```

#### 2. CalibrateStick - 摇杆校准

**功能**：测量摇杆灵敏度、最小和最大模拟量对应移动的距离

**Pipeline 配置**：
```json
{
    "摇杆校准": {
        "recognition": "DirectHit",
        "action": "Custom",
        "custom_action": "CalibrateStick",
        "custom_action_param": {
            "crosshair_image": "crosshair.png",
            "stick": "right",
            "test_values": [5000, 10000, 16384, 20000, 25000, 30000, 32767],
            "test_duration": 0.1,
            "threshold": 0.8,
            "save_report": true
        }
    }
}
```

**输出示例**：
```
[Calibrate] === 测试 X 轴（向右）===
[Calibrate] 摇杆值  5000 -> 移动   15.3 像素, 灵敏度 0.003060 像素/单位
[Calibrate] 摇杆值 32767 -> 移动  105.8 像素, 灵敏度 0.003228 像素/单位

============================================================
[Calibrate] 摇杆校准测试报告
============================================================
摇杆: right

X 轴统计:
  平均灵敏度: 0.003150 像素/单位
  最小模拟量 (5000) 移动: 15.8 像素
  最大模拟量 (32767) 移动: 103.3 像素

推荐参数:
  x_sensitivity = 0.003150
  y_sensitivity = 0.002980
============================================================
```

#### 3. AimToTarget - 智能瞄准

**功能**：使用摇杆将准星移动到指定屏幕坐标

**Pipeline 配置**：
```json
{
    "瞄准目标": {
        "recognition": "DirectHit",
        "action": "Custom",
        "custom_action": "AimToTarget",
        "custom_action_param": {
            "target_x": 1200,
            "target_y": 400,
            "crosshair_image": "crosshair.png",
            "max_iterations": 20,
            "threshold": 0.8,
            "tolerance": 10,
            "stick": "right",
            "use_partial_capture": true,
            "x_sensitivity": 0.003,
            "y_sensitivity": 0.003
        }
    }
}
```

**参数说明**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `target_x` | 960 | 目标屏幕 X 坐标 |
| `target_y` | 540 | 目标屏幕 Y 坐标 |
| `crosshair_image` | crosshair.png | 准星模板图片文件名 |
| `max_iterations` | 20 | 最大迭代次数 |
| `threshold` | 0.8 | 模板匹配置信度阈值 |
| `tolerance` | 10 | 允许的误差范围（像素） |
| `stick` | right | 使用的摇杆（left/right） |
| `use_partial_capture` | true | 是否使用局部截图优化 |
| `x_sensitivity` | 0.003 | X 轴灵敏度（从校准获取） |
| `y_sensitivity` | 0.003 | Y 轴灵敏度（从校准获取） |

### 算法优化

#### 1. 多尺度模板匹配

**问题**：准星有呼吸效果，大小会变化（85% ~ 115%）

**解决**：
```python
# 多尺度匹配
scales = [0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15]

for scale in scales:
    resized_template = cv2.resize(template, None, fx=scale, fy=scale)
    result = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
    # 选择最佳匹配
```

**效果**：适配准星呼吸效果，提高匹配准确率

#### 2. 智能瞄准算法

**防止移动过头的机制**：

| 机制 | 说明 | 公式 |
|------|------|------|
| 刹车机制 | 平滑减速 | `√(distance/100)` |
| 预测因子 | 保守估计 | `0.9` |
| 近距离保护 | 距离 < 30px 时减速 | `stick *= 0.5` |
| 迭代衰减 | 每次迭代减速 | `1 - iteration/max_iterations * 0.6` |

**速度计算**：
```python
base_speed = min(1.0, distance / 200.0)
brake_factor = sqrt(min(1.0, distance / 100.0))
iteration_decay = 1.0 - (iteration / max_iterations) * 0.6
predict_factor = 0.9

speed = base_speed * brake_factor * iteration_decay * predict_factor
```

#### 3. 性能优化

| 优化措施 | 说明 | 性能提升 |
|---------|------|---------|
| 灰度图 | 模板和截图都转灰度 | ~3x |
| 多尺度匹配 | 7 个尺度遍历 | 适配呼吸效果 |
| 局部截图 | 只截取准星到目标方向区域 | ~2-5x |
| 归一化匹配 | TM_CCOEFF_NORMED | 对亮度变化鲁棒 |

### 使用流程

1. **准备准星模板**：
   - 在准星最大或平均尺寸时截图
   - 保存为 `assets/resource/image/crosshair.png`

2. **运行校准**：
   - 在 Pipeline 中配置 `CalibrateStick`
   - 运行一次获取灵敏度参数
   - 查看日志或 `stick_calibration_report.json`

3. **配置瞄准**：
   - 将校准得到的灵敏度填入 `AimToTarget` 配置
   - 设置目标坐标
   - 运行瞄准任务

### 性能数据

| 操作 | 耗时 | 说明 |
|------|------|------|
| 单尺度匹配 | ~25ms | 固定大小准星 |
| 多尺度匹配 (7个) | ~175ms | 呼吸效果准星 |
| 单次瞄准迭代 | ~200ms | 匹配+移动 |
| 完整瞄准 | 1-4秒 | 5-20次迭代 |

### 注意事项

1. **准星模板要求**：
   - 清晰、特征明显
   - 在最大或平均尺寸时截图
   - 避免在最小尺寸时截图

2. **游戏内设置**：
   - 摇杆灵敏度会影响校准结果
   - 建议固定游戏内摇杆灵敏度后再校准

3. **环境要求**：
   - 光线稳定的场景
   - 准星区域无干扰

### 技术原理

#### 摇杆控制

MaaFramework 的手柄控制基于 ViGEm 驱动，摇杆采用直接的模拟值输入：

| Contact | 控制目标 | x/y 范围 |
|---------|---------|----------|
| 0 | 左摇杆 | -32768 ~ 32767 |
| 1 | 右摇杆 | -32768 ~ 32767 |

- 负值：向左/向上
- 正值：向右/向下
- 0：中心位置

#### 模板匹配

使用 OpenCV 的 `matchTemplate` 函数：

```python
result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
```

- `TM_CCOEFF_NORMED`：归一化相关系数
- 结果范围：[-1, 1]
- 对亮度变化不敏感

---

## 摇杆校准映射表（2026-06-08 新增）

### 问题背景

原有的摇杆瞄准算法使用固定灵敏度参数，存在以下问题：
1. 近距离移动太慢：摇杆值随距离减小而减小，导致卡在最后几十像素
2. 无法精确控制：不同距离需要不同的摇杆值和持续时间组合
3. 迭代次数过多：需要10-20次迭代才能到达目标

### 解决方案：摇杆校准映射表

通过实际测试生成摇杆值-移动距离的二维映射表，实现精确控制。

#### 1. 测试生成映射表

**测试脚本**：`test/test_stick_calibration.py`

**测试参数**：
- 摇杆值：14个档位（1000 ~ 32767）
- 持续时间：7个档位（0.05s ~ 0.25s）
- 总测试数：98组

**测试流程**：
```
1. 激活游戏窗口
2. 激活手柄模式
3. 检测准星位置
4. 遍历摇杆值和持续时间组合
   - 记录移动前准星位置
   - 移动摇杆指定值和持续时间
   - 记录移动后准星位置
   - 计算移动距离
5. 生成映射表
```

**测试结果示例**：
```
持续时间 0.1s:
  摇杆10000:    8.0px (速度:   80.0px/s)
  摇杆12000:   15.0px (速度:  150.0px/s)
  摇杆15000:   23.0px (速度:  230.0px/s)
  摇杆20000:   44.0px (速度:  440.0px/s)
  摇杆25000:   63.0px (速度:  630.0px/s)
  摇杆30000:   69.0px (速度:  690.0px/s)
  摇杆32767:   79.0px (速度:  790.0px/s)
```

#### 2. 映射表实现

**文件**：`agent/stick_calibration_map.py`

**数据结构**：
```python
STICK_DURATION_MAP = {
    0.05: {  # 持续时间 0.05s
        10000: 4.0,
        12000: 6.0,
        15000: 15.0,
        20000: 19.0,
        25000: 26.0,
        30000: 35.0,
    },
    0.1: {   # 持续时间 0.1s
        10000: 8.0,
        12000: 15.0,
        15000: 23.0,
        20000: 44.0,
        25000: 63.0,
        30000: 69.0,
        32767: 79.0,
    },
    # ... 其他持续时间
}
```

**查询函数**：
```python
def find_stick_params_for_axis(dx, dy, preferred_duration=None):
    """
    根据X/Y偏移查找最优摇杆参数
    
    Args:
        dx, dy: 目标偏移量（像素）
        preferred_duration: 首选持续时间（秒）
    
    Returns:
        (stick_x, stick_y, duration, actual_distance)
    """
    distance = (dx*dx + dy*dy) ** 0.5
    
    # 在映射表中查找最接近的距离
    best_result = None
    best_diff = float('inf')
    
    for duration, duration_map in STICK_DURATION_MAP.items():
        for stick, dist in duration_map.items():
            diff = abs(dist - distance)
            if diff < best_diff:
                best_diff = diff
                best_result = (stick, duration, dist)
    
    # 分解到X/Y轴
    stick_x = int(stick * dx / distance)
    stick_y = int(stick * dy / distance)
    
    return (stick_x, stick_y, duration, actual_dist)
```

#### 3. 集成到摇杆移动动作

**修改文件**：`agent/move_stick_action.py`

**核心改动**：
```python
from stick_calibration_map import find_stick_params_for_axis

def _calculate_stick_values(self, dx, dy, distance, ...):
    # 根据距离选择首选持续时间
    if distance > 200:
        preferred_duration = 0.15
    elif distance > 100:
        preferred_duration = 0.12
    elif distance > 50:
        preferred_duration = 0.10
    else:
        preferred_duration = 0.08
    
    # 查询映射表获取最优参数
    result = find_stick_params_for_axis(dx, dy, preferred_duration)
    
    if result:
        stick_x, stick_y, duration, actual_dist = result
        return stick_x, stick_y, duration
    
    # 备用：固定参数（映射表未覆盖的情况）
    # ...
```

### 性能对比

#### 原算法（固定灵敏度）

| 测试目标 | 迭代次数 | 最终误差 | 问题 |
|---------|---------|---------|------|
| 左上角 (640, 360) | 15-20次 | 20-50px | 近距离移动慢 |
| 右上角 (1280, 360) | 15-20次 | 20-50px | 容易移动过头 |
| 中心 (960, 540) | 15-20次 | 20-50px | 迭代次数多 |

#### 新算法（校准映射表）

| 测试目标 | 迭代次数 | 最终误差 | 改进 |
|---------|---------|---------|------|
| 左上角 (640, 360) | **7次** | **7.1px** | 迭代减少50%+ |
| 右上角 (1280, 360) | **6次** | **6.4px** | 精度提升3倍 |
| 中心 (960, 540) | **9次** | **8.5px** | 稳定可靠 |

**关键改进**：
- ✅ 迭代次数：从15-20次降至**6-9次**
- ✅ 最终误差：从20-50px降至**6-9px**
- ✅ 稳定性：不再出现移动过头或卡住的情况

### 数据验证

#### 单调性检查

所有数据满足单调递增：
- 同一持续时间下，摇杆值越大，移动距离越大
- 同一摇杆值下，持续时间越长，移动距离越大

#### 速度范围

| 摇杆值 | 速度范围 (px/s) | 合理性 |
|--------|----------------|--------|
| 10000 | 65-87 | ✓ 低速稳定 |
| 15000 | 208-253 | ✓ 中速线性 |
| 20000 | 380-440 | ✓ 高速可控 |
| 32767 | 790-1100 | ✓ 极速准确 |

#### 异常值处理

测试中发现异常值：
- **0.05s + 摇杆30000 = 906px**（异常）
- 原因：准星靠近边界，测试时跳到屏幕另一侧
- 修正：**906px → 35px**（符合其他数据趋势）

### 测试文件整理

所有测试脚本统一放置在 `test/` 目录：

```
test/
├── test_aim_with_calibration.py    # 瞄准功能测试（使用映射表）
├── test_stick_calibration.py       # 摇杆校准测试（生成映射表）
└── test_stick_continuous.py        # 连续摇杆测试
```

### 使用流程

1. **生成映射表**（首次或游戏设置改变时）：
   ```bash
   cd test
   python test_stick_calibration.py
   ```
   
2. **验证映射表**：
   ```bash
   python -c "from agent.stick_calibration_map import find_stick_params_for_axis; \
              print(find_stick_params_for_axis(100, 0))"
   # 输出: (32767, 0, 0.12, 103.0)
   ```

3. **测试瞄准功能**：
   ```bash
   python test/test_aim_with_calibration.py
   ```

### 技术要点

#### 1. 摇杆值范围

游戏对摇杆值的响应：
- **< 8000**：游戏不响应（死区）
- **8000-10000**：勉强移动（1-2px）
- **10000-15000**：低速稳定移动
- **15000-25000**：中速线性移动
- **25000-32767**：高速移动

#### 2. 持续时间选择策略

```python
if distance > 200:
    duration = 0.15-0.25s  # 远距离：长持续时间，大摇杆值
elif distance > 100:
    duration = 0.12s       # 中距离
elif distance > 50:
    duration = 0.10s       # 近距离
else:
    duration = 0.05-0.08s  # 很近：短持续时间，小摇杆值
```

#### 3. Y轴方向反转

vgamepad的Y轴正值向上，屏幕坐标系Y轴向下为正，需要反转：

```python
stick_y = -stick_y  # 反转Y轴
```

### 注意事项

1. **游戏设置影响**：
   - 游戏内摇杆灵敏度改变需要重新校准
   - 建议固定游戏设置后再生成映射表

2. **环境要求**：
   - 测试时准星不能靠近屏幕边界（留150px缓冲）
   - 确保准星可见且稳定

3. **映射表更新**：
   - 游戏版本更新后建议重新校准
   - 发现异常数据时需修正映射表

---

## 探险派遣功能实现（2026-06-10）

### 功能概述

实现王者荣耀世界的探险派遣自动化，包括：
- 传送到派遣小屋
- 打开派遣画面
- 选择地点（春溪原、秘禁之地、稷下学院）
- 查找并派遣人员（阿噗、啾啾、哆哆、卫宁、堂听虎、小红、学典鹅、酷酷、聪聪）
- 滚动菜单查找未显示的人员

### MaaFramework Pipeline协议深入理解

#### 1. timeout的正确理解

**错误理解**（初期）：
- timeout控制当前节点的识别超时时间
- 当前节点识别失败后等待timeout才进入on_error

**正确理解**（修正后）：
- **timeout控制当前节点next列表的识别超时时间**
- 节点A的timeout → 控制节点A的next列表（节点B、C...）的识别超时
- 节点B的识别等待时间 → 由前置节点（节点A）的timeout控制

**示例**：
```json
{
    "节点A": {
        "recognition": "DirectHit",
        "action": "DoNothing",
        "timeout": 30000,  // 控制next列表中节点B的识别超时
        "next": ["节点B"]
    },
    "节点B": {
        "recognition": "OCR",
        "expected": "目标文本"
        // 识别等待时间由节点A的timeout控制
    }
}
```

#### 2. 节点执行顺序

**关键理解**：
```
前置节点识别命中当前节点
    ↓
执行当前节点的action
    ↓
识别当前节点的next列表
    ↓
第一个命中的节点执行
```

**重要结论**：
- 能执行当前节点的action，是因为在前置节点已经命中了当前节点的recognition
- 当前节点执行完action后，才识别next列表

#### 3. next列表机制

**顺序识别，第一个命中即执行**：
```
next: [节点A, 节点B, 节点C]
    ↓
识别节点A：
  - 命中 → 执行节点A，不再识别节点B、C
  - 未命中 → 继续识别节点B
    ↓
识别节点B：
  - 命中 → 执行节点B，不再识别节点C
  - 未命中 → 继续识别节点C
    ↓
识别节点C：
  - 命中 → 执行节点C
  - 未命中 → 等待rate_limit后重新识别next列表
    ↓
超时 → 进入当前节点的on_error
```

#### 4. DirectHit特性

**立即命中，无需等待**：
- recognition: DirectHit → 直接命中，不进行实际识别
- 不会等待rate_limit
- 不会等待timeout
- 立即执行action

**应用场景**：
- 入口节点（不需要识别）
- 立即执行的动作节点（如滚动菜单）

#### 5. JumpBack机制

**触发条件**：
- 节点的next为空数组 `[]`
- 节点执行完成后，返回上级节点（设置JumpBack标记的节点）

**应用场景**：
- 循环查找：OCR未找到 → 滚动菜单 → JumpBack → 继续OCR查找

### 滚动菜单循环逻辑优化

#### 问题演进

**阶段1：错误理解timeout**
```json
{
    "查找人员": {
        "recognition": "OCR",
        "next": ["移动准星"],
        "on_error": ["滚动菜单"],  // 错误：等待timeout才滚动
        "timeout": 60000
    }
}
```
**问题**：OCR未识别到会等待rate_limit继续识别，直到60秒超时才进入on_error

**阶段2：错误使用next列表**
```json
{
    "查找人员": {
        "recognition": "OCR",
        "next": ["移动准星", "滚动菜单"]  // 错误：OCR命中后next包含滚动菜单
    },
    "滚动菜单": {
        "next": ["查找人员"]  // 错误：滚动后重新查找
    }
}
```
**问题**：逻辑混乱，OCR命中后next包含滚动菜单不合理

**阶段3：正确方案（最终）**
```json
{
    "查找人员": {
        "recognition": "OCR",
        "next": ["移动准星"]  // 正确：只包含移动准星
    },
    "滚动菜单": {
        "recognition": "DirectHit",
        "next": []  // 正确：空数组触发JumpBack
    },
    "选择人员": {
        "action": "TapButton(A)",
        "next": ["查找人员", "[JumpBack]滚动菜单"]  // 正确：OCR未找到立即滚动
    }
}
```

#### 正确的执行流程

```
选择人员节点（按A键）
    ↓
执行action: TapButton(A)
    ↓
识别next列表: [查找人员, JumpBack滚动菜单]
    ↓
识别"查找人员"节点（OCR）：
  - 找到 → 执行ExtractOCRTarget → next: [移动准星] → 移动准星 → 选择人员
  - 未找到 → 继续识别下一个节点
    ↓
识别"滚动菜单"节点（DirectHit）：
  - 立即命中（无需等待）
  - 执行MoveStickOnce（滚动菜单）
  - next为空 → JumpBack返回"选择人员"节点
    ↓
重新识别next列表 → 循环直到OCR找到人员
```

#### 关键要点

1. **查找人员节点**：
   - next只包含移动准星节点
   - 不包含滚动菜单节点

2. **滚动菜单节点**：
   - recognition: DirectHit（立即命中）
   - next: []（空数组，触发JumpBack）

3. **选择人员节点**：
   - next包含[查找人员, [JumpBack]滚动菜单]
   - OCR未找到 → 立即滚动 → JumpBack → 继续查找

### 点击地点节点优化

#### 原方案（单节点）
```json
{
    "点击地点": {
        "action": "TapButton(X)",  // 直接按X键
        "next": ["移动准星到菜单顶部"]
    }
}
```

#### 优化方案（双节点）
```json
{
    "点击地点": {
        "action": "TapButton(A)",  // 先按A键选定
        "next": ["打开菜单"]
    },
    "打开菜单": {
        "action": "TapButton(X)",  // 再按X键打开菜单
        "next": ["移动准星到菜单顶部"]
    },
    "移动准星到菜单顶部": {
        "next": ["查找人员", "[JumpBack]滚动菜单"]  // 支持循环查找
    }
}
```

**优化原因**：
- 游戏机制：需要先按A键选定地点，再按X键打开菜单
- 支持滚动菜单循环查找人员

### Pipeline配置结构

#### 完整流程

```
开始
  ↓
传送到派遣小屋
  ↓
打开派遣画面（Y键）
  ↓
晃动准星（激活显示）
  ↓
【地点循环：春溪原 → 秘禁之地 → 稷下学院】
  ├─ 查找地点（OCR）
  ├─ 移动准星到地点
  ├─ 点击地点（A键）
  ├─ 打开菜单（X键）
  ├─ 移动准星到菜单顶部
  └─ 【人员循环】
      ├─ 查找人员（OCR）
      ├─ 移动准星到人员
      ├─ 选择人员（A键）
      └─ 滚动菜单（DirectHit + JumpBack）
  ↓
确认派遣（X键）
  ↓
退出派遣画面（B键）
```

#### 节点统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 入口节点 | 1 | 开始节点 |
| 传送节点 | 3 | 传送到派遣小屋、等待加载、向前移动 |
| 打开画面节点 | 2 | 打开派遣画面、晃动准星 |
| 地点节点 | 9 | 查找、移动、点击、打开菜单、移动到顶部（3个地点） |
| 人员节点 | 27 | 查找、移动、选择、滚动（9个人员） |
| 确认节点 | 3 | 确认派遣（3个地点） |
| 退出节点 | 1 | 退出派遣画面 |
| **总计** | **46** | - |

### 关键技术实现

#### 1. MoveStick - 摇杆移动准星

**核心逻辑**：
```python
def run(self, context, argv):
    # 获取目标坐标
    target_x = params.get('target_x', 960)
    target_y = params.get('target_y', 540)
    
    # 循环移动
    for i in range(max_iterations):
        # 检测准星位置
        crosshair_pos = self._find_crosshair(image)
        
        # 计算偏移
        dx = target_x - crosshair_pos[0]
        dy = target_y - crosshair_pos[1]
        distance = (dx*dx + dy*dy) ** 0.5
        
        # 判断是否到达
        if distance < tolerance:
            return True
        
        # 查询校准映射表获取最优参数
        stick_x, stick_y, duration = find_stick_params_for_axis(dx, dy)
        
        # 执行移动
        controller.set_stick(stick, stick_x, stick_y)
        time.sleep(duration)
        controller.reset_stick(stick)
```

#### 2. MoveStickOnce - 一次性摇杆推动

**用于滚动菜单**：
```python
def run(self, context, argv):
    stick = params['stick']  # "right"
    x = params['x']          # 10000
    y = params['y']          # -30000（向上）
    duration = params['duration']  # 0.1
    
    controller.set_stick(stick, x, y)
    time.sleep(duration)
    controller.reset_stick(stick)
```

#### 3. ExtractOCRTarget - 提取OCR目标

**动态设置MoveStick参数**：
```python
def run(self, context, argv):
    # 获取OCR识别结果
    box = argv.box  # [x, y, w, h]
    
    # 计算中心点
    target_x = box[0] + box[2] // 2
    target_y = box[1] + box[3] // 2
    
    # 动态修改下一个任务的参数
    next_task = params['next_task']
    context.override_pipeline(next_task, {
        "custom_action_param": json.dumps({
            "target_x": target_x,
            "target_y": target_y,
            # ... 其他参数
        })
    })
```

### 文件结构

**新增文件**：
- `assets/resource/pipeline/dispatch.json` - 探险派遣流水线（46个节点）
- `assets/resource/pipeline/teleport_common.json` - 通用传送流水线
- `assets/resource/pipeline/teleport_to_target.json` - 传送到目标流水线
- `agent/move_stick_action.py` - 摇杆移动动作
- `agent/move_stick_once.py` - 一次性摇杆推动
- `agent/extract_ocr_target.py` - 提取OCR目标位置
- `agent/stick_calibration_map.py` - 摇杆校准映射表

**修改文件**：
- `agent/custom_action.py` - 添加更多手柄按钮支持
- `agent/agent_server.py` - 注册新的自定义动作
- `assets/interface.json` - 添加探险派遣任务配置

### 测试验证

**测试流程**：
1. 传送到派遣小屋 ✓
2. 打开派遣画面 ✓
3. 选择春溪原 ✓
4. 查找并派遣阿噗、啾啾、哆哆 ✓
5. 选择秘禁之地 ✓
6. 查找并派遣卫宁、堂听虎、小红 ✓
7. 选择稷下学院 ✓
8. 查找并派遣学典鹅、酷酷、聪聪 ✓
9. 退出派遣画面 ✓

### 性能数据

| 操作 | 耗时 | 说明 |
|------|------|------|
| 传送 | 3-5秒 | 包括加载等待 |
| 打开画面 | 1-2秒 | 晃动准星激活 |
| 查找地点 | 0.5-1秒 | OCR识别 |
| 移动准星 | 1-3秒 | 5-10次迭代 |
| 查找人员 | 0.5-2秒 | OCR + 滚动菜单 |
| 完整流程 | 2-3分钟 | 3个地点 × 3个人员 |

### 开发过程总结

#### 第一阶段：基础传送功能
1. 实现传送到派遣小屋
2. 实现打开派遣画面
3. 实现摇杆移动准星

#### 第二阶段：地点选择
1. OCR识别地点名称
2. MoveStick瞄准到地点
3. 点击确认

#### 第三阶段：人员选择（核心难点）
1. **理解Pipeline协议**：
   - timeout的正确含义
   - next列表机制
   - DirectHit特性
   - JumpBack机制

2. **滚动菜单循环逻辑优化**：
   - 错误方案1：使用on_error（等待timeout）
   - 错误方案2：next列表混乱
   - 正确方案：JumpBack + DirectHit

3. **点击地点优化**：
   - 改为双节点：先A键选定，再X键打开
   - 支持滚动菜单循环查找

#### 第四阶段：完整流程
1. 统一三个地点的流程
2. 完善所有人员节点
3. 测试验证完整流程

### 关键发现

1. **Pipeline协议理解至关重要**：
   - 错误理解会导致逻辑混乱
   - timeout、next、on_error的含义需要准确把握

2. **DirectHit + JumpBack是循环利器**：
   - DirectHit立即命中，无需等待
   - JumpBack实现循环返回
   - 组合使用实现高效的循环查找

3. **节点设计需要符合游戏逻辑**：
   - 先A键选定，再X键打开菜单
   - OCR查找失败立即滚动，不等待timeout
   - 滚动菜单next为空触发JumpBack

4. **摇杆校准映射表大幅提升精度**：
   - 迭代次数从15-20次降至6-9次
   - 最终误差从20-50px降至6-9px

### 注意事项

1. **游戏内按键映射**：
   - 菜单键：Y（打开派遣画面）
   - 确认键：A（选定、选择人员）
   - 打开菜单：X（打开地点菜单、确认派遣）
   - 退出键：B（退出派遣画面）

2. **准星显示问题**：
   - 菜单界面默认不显示准星
   - 需要先晃动摇杆激活准星显示

3. **滚动菜单方向**：
   - 右摇杆向下滚动（y: -30000）
   - 持续时间：0.1秒

4. **OCR识别区域**：
   - 地点：左侧区域 [380, 0, 1060, 1080]
   - 人员：右侧区域 [1290, 0, 630, 1080]

---

## 探险派遣循环版实现（2026-06-13）

### 功能概述

将探险派遣从硬编码的46节点Pipeline改为循环版本，支持用户通过interface.json自定义配置地点和人员，无需修改Pipeline配置。

### 设计思路

#### 循环 vs 固定节点

| 方案 | 优点 | 缺点 |
|------|------|------|
| 固定节点（原方案） | 逻辑简单，调试直观 | 46个节点，修改需改Pipeline |
| 循环版本 | 节点少，用户可自定义配置 | 需要CustomAction/Recognition控制状态 |

选择循环版本，使用`DispatchLoopController`单例管理循环状态。

#### 循环退出机制

利用MaaFramework的next列表顺序执行特性：
- 退出条件节点放在next列表第一位
- 循环节点放在后面
- 退出条件命中则跳出循环，未命中则继续循环

```
初始化循环节点:
  next: [退出派遣画面, [JumpBack]下一个地点]
  → 退出条件(CheckLocationCount)命中 → 退出
  → 未命中 → JumpBack到下一个地点 → 继续循环
```

#### 索引判断条件

**当前代码使用`==`判断**：

```python
# CheckLocationCount (dispatch_loop_controller.py:213)
if controller.current_location_index == len(controller.locations):
    return (960, 540, 100, 100)  # 命中

# CheckPersonCount (dispatch_loop_controller.py:249)
if controller.current_person_index == len(persons):
    return (960, 540, 100, 100)  # 命中
```

**完整流程推演（3个地点，每个地点3个人员）**：

| 阶段 | CheckLocationCount | _next_location | _next_person | CheckPersonCount | location_index | person_index |
|------|-------------------|----------------|--------------|------------------|----------------|--------------|
| 初始化 | - | - | - | - | 0 | 0 |
| 地点1开始 | 第1次(0≠3,未命中) | 第1次(处理0) | - | - | 0 | 0 |
| 人员1 | - | - | 第1次 | 第1次(0≠3,未命中) | 0 | 1 |
| 人员2 | - | - | 第2次 | 第2次(1≠3,未命中) | 0 | 2 |
| 人员3 | - | - | 第3次 | 第3次(2≠3,未命中)→第4次(3==3,命中) | 1 | 3 |
| 地点2开始 | 第2次(1≠3,未命中) | 第2次(处理1) | - | - | 1 | 0(重置) |
| 人员1-3 | - | - | 第1-3次 | 第1-4次(最后命中) | 2 | 3 |
| 地点3开始 | 第3次(2≠3,未命中) | 第3次(处理2) | - | - | 2 | 0(重置) |
| 人员1-3 | - | - | 第1-3次 | 第1-4次(最后命中) | 3 | 3 |
| 退出 | 第4次(3==3,命中) | - | - | - | 3 | 3 |

**关键理解**：
- `_next_person`先递增person_index（第182-183行），再判断是否==len（第185行）
- person_index从0开始，处理3个人员后变为3，此时==len命中
- 命中时同时递增location_index（第188行）
- 最终location_index=3，person_index=3

### 核心组件

#### 1. DispatchLoopController - 循环控制器

单例模式，管理地点/人员索引和状态：

```python
class DispatchLoopController(CustomAction):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.locations = []
            instance.persons = {}
            instance.current_location_index = 0
            instance.current_person_index = 0
            instance.initialized = False
            cls._instance = instance
        return cls._instance
    
    def run(self, context, argv):
        action = param.get('action', 'init')
        if action == 'init':
            return self._init_config(context, config_str)
        elif action == 'next_location':
            return self._next_location(context)
        elif action == 'next_person':
            return self._next_person(context)
```

**关键设计**：
- `_init_config`：每次任务开始重置所有状态，支持多次运行
- `_next_location`：递增地点索引，通过`context.override_pipeline`动态修改OCR识别参数
- `_next_person`：递增人员索引，同样动态修改OCR参数

#### 2. CheckLocationCount / CheckPersonCount - 循环退出识别器

```python
class CheckLocationCount(CustomRecognition):
    def analyze(self, context, argv):
        controller = DispatchLoopController()
        if controller.current_location_index == len(controller.locations):
            return (960, 540, 100, 100)  # 命中→退出循环
        return None  # 未命中→继续循环
```

### 配置传递机制

#### interface.json配置

```json
{
    "dispatch_config": {
        "type": "input",
        "inputs": [{
            "name": "config_json",
            "default": "{\"locations\": [...], \"persons\": {...}}",
            "pipeline_type": "string"
        }],
        "pipeline_override": {
            "探险派遣循环版_初始化循环": {
                "custom_action_param": "{\"action\": \"init\", \"config\": {config_json}}"
            }
        }
    }
}
```

#### 配置传递问题与修复

**问题1**：嵌套JSON字符串转义错误

原始配置使用`"{config_json}"`（字符串嵌套），导致MaaFramework传递时引号未正确转义，JSON解析失败。

```
原始param: {"action": "init", "config": "{"locations": ...}"}  ← 引号冲突
解析结果: {}  ← 解析失败
```

**修复**：改为`{config_json}`（直接嵌入JSON对象），MaaFramework会正确替换：

```
原始param: {"action": "init", "config": {"locations": ...}}  ← 正确
解析结果: {'action': 'init', 'config': {'locations': [...]}}  ← 解析成功
```

**问题2**：`_init_config`只接受JSON字符串，收到dict后解析失败

```
config_str: {'locations': [...]}  ← dict类型
json.loads() 报错: the JSON object must be str, bytes or bytearray, not dict
```

**修复**：`_init_config`增加类型判断，同时支持dict和JSON字符串：

```python
if isinstance(config_str, dict):
    config = config_str
else:
    config = json.loads(config_str)
```

### Pipeline配置（dispatch_loop.json）

#### 循环结构

```
初始化循环
  next: [退出派遣画面, [JumpBack]下一个地点]
  ↓
下一个地点（DispatchLoopController: next_location）
  next: [查找地点]
  ↓
查找地点 → 移动准星 → 点击地点 → 打开菜单 → 移动到菜单顶部
  ↓
查找人员循环
  next: [确认派遣, [JumpBack]开始查找人员]
  ↓
开始查找人员（DispatchLoopController: next_person）
  next: [查找人员, [JumpBack]滚动菜单]
  ↓
查找人员 → 移动准星 → 选择人员（next为空→JumpBack回查找人员循环）
  ↓
确认派遣（CheckPersonCount命中→按X确认，next为空→JumpBack回初始化循环）
  ↓
退出派遣画面（CheckLocationCount命中→按B退出）
```

### 开发过程中的Bug修复

#### Bug1：CheckPersonCount使用未定义变量

```python
# 错误：persons在if分支未定义
if controller.current_person_index + 1 == len(persons):  # NameError!
    ...

# 修复：先获取persons
location = controller.locations[controller.current_location_index]
persons = controller.persons.get(location, [])
if controller.current_person_index > len(persons):
    ...
```

#### Bug2：单例模式状态未重置

两次任务运行之间状态互相影响，需要在`_init_config`中重置所有状态：

```python
def _init_config(self, context, config_str):
    self.locations = []
    self.persons = {}
    self.current_location_index = 0
    self.current_person_index = 0
    self.initialized = False
    # ... 然后重新初始化
```

### 文件结构

**新增文件**：
- `assets/resource/pipeline/dispatch_loop.json` - 循环版Pipeline配置
- `agent/dispatch_loop_controller.py` - 循环控制器和识别器

**修改文件**：
- `agent/agent_server.py` - 注册DispatchLoopController、CheckLocationCount、CheckPersonCount
- `assets/interface.json` - 添加dispatch_config选项

---

## 领取派遣奖励功能实现（2026-06-14）

### 功能概述

实现自动领取已完成的探险派遣奖励。OCR识别"完成派遣"文本，依次对每个结果执行：移动准星→选定→确认→返回。

### 设计辨析：固定顺序 vs 循环

| 方案 | 优点 | 缺点 |
|------|------|------|
| 固定顺序（3组节点） | 逻辑简单，调试直观 | 节点重复3次 |
| 循环版本 | 节点少 | 需要额外循环控制器 |

**选择固定顺序**，理由：
1. 结果数量固定为3，不会变化
2. MaaFramework OCR的`index`参数可直接指定第几个结果
3. 调试更直观，出问题容易定位

### 设计辨析：on_error循环 vs JumpBack循环

#### on_error方式（错误）

```json
{
    "移动准星到结果1": {
        "on_error": ["领取派遣_移动准星到结果1"]
    }
}
```

**问题**：虽然实现了循环功能，但破坏了`on_error`的设计目的和语义。`on_error`应只用于真正的错误处理。

#### JumpBack方式（正确）

```json
{
    "查找完成派遣1": {
        "next": ["选定结果1", "[JumpBack]移动准星到结果1"]
    },
    "移动准星到结果1": {
        "next": []
    },
    "选定结果1": {
        "recognition": "Custom",
        "custom_recognition": "FindCrosshairNearTarget"
    }
}
```

**原理**：
- `查找完成派遣1`的next列表：先检查`选定结果1`（FindCrosshairNearTarget），命中则继续，未命中则JumpBack到`移动准星到结果1`
- `移动准星到结果1`的next为空，执行后JumpBack回上级next列表重新检查
- 循环直到准星到达目标

### 核心组件

#### 1. FindCrosshairNearTargetRecognition - 准星接近目标识别器

调用FindCrosshair识别准星位置，再判断准星与目标坐标的距离是否小于容差：

```python
class FindCrosshairNearTargetRecognition(CustomRecognition):
    def __init__(self):
        self._finder = FindCrosshairRecognition()
    
    def analyze(self, context, argv):
        # 从参数获取目标坐标
        target_x = param.get('target_x')
        target_y = param.get('target_y')
        tolerance = param.get('tolerance', 10)
        
        # 调用FindCrosshair识别准星
        result = self._finder.analyze(context, argv)
        if result is None:
            return None
        
        # 判断距离
        cx, cy = result.detail['center_x'], result.detail['center_y']
        distance = ((target_x - cx)**2 + (target_y - cy)**2) ** 0.5
        
        if distance < tolerance:
            return AnalyzeResult(box=(cx, cy, 1, 1), detail={...})
        return None  # 未命中→JumpBack继续移动
```

#### 2. ExtractOCRTarget扩展 - 支持多节点参数传递

新增`next_tasks`参数，同时向move和near_target类型节点传递目标坐标：

```python
# 原有方式（单节点）
"custom_action_param": "{\"next_task\": \"移动准星到结果1\"}"

# 新增方式（多节点）
"custom_action_param": "{\"next_tasks\": [[\"移动准星到结果1\", \"move\"], [\"选定结果1\", \"near_target\"]]}"
```

**类型说明**：
- `"move"`：传递`custom_action_param`（target_x, target_y, tolerance等给MoveStick）
- `"near_target"`：传递`custom_recognition_param`（target_x, target_y, tolerance给FindCrosshairNearTarget）

兼容原有`next_task`参数，不影响现有Pipeline。

### OCR多结果选择

使用MaaFramework的`order_by`和`index`参数：

```json
{
    "recognition": {
        "type": "OCR",
        "param": {
            "roi": [380, 0, 1060, 1080],
            "expected": ["完成派遣"],
            "order_by": "Vertical",
            "index": 0
        }
    }
}
```

- `order_by: "Vertical"`：按纵向排序（"完成派遣"文本纵向排列）
- `index: 0/1/2`：选择第1/2/3个结果

### Pipeline流程（dispatch_result.json）

```
开始 → 传送 → 移动 → 打开画面 → 晃动准星
  ↓
查找完成派遣1 (index=0)
  next: [选定结果1, [JumpBack]移动准星到结果1]
  ↓
移动准星到结果1 (next为空→JumpBack)
  ↓
选定结果1 (FindCrosshairNearTarget命中→A键)
  → 确认结果1 (X键) → 返回1 (A键)
  ↓
查找完成派遣2 (index=1) → ... → 返回2
  ↓
查找完成派遣3 (index=2) → ... → 返回3
  ↓
退出派遣画面 (B键) → 完成
```

### 文件结构

**新增文件**：
- `assets/resource/pipeline/dispatch_result.json` - 领取派遣奖励Pipeline
- `agent/crosshair_recognition.py` 中新增 `FindCrosshairNearTargetRecognition`

**修改文件**：
- `agent/extract_ocr_target.py` - 新增`next_tasks`参数支持
- `agent/agent_server.py` - 注册FindCrosshairNearTarget识别器
- `assets/interface.json` - 添加"领取派遣奖励"任务入口

---

## 循环模式统一与Bug修复（2026-06-15）

### FindCrosshairNearTargetRecognition缺少_handle属性

**问题**：注册识别器时报错 `AttributeError: 'FindCrosshairNearTargetRecognition' object has no attribute '_handle'`

**原因**：自定义识别器需要调用 `super().__init__()` 初始化父类的 `_handle` 属性

**修复**：
```python
class FindCrosshairNearTargetRecognition(CustomRecognition):
    def __init__(self):
        super().__init__()  # 必须调用父类初始化
        self._finder = FindCrosshairRecognition()
```

### JSON解析双重编码问题

**问题**：`FindCrosshairNearTarget` 收到的参数是字符串 `"{"target_x": 210, ...}"`，解析后仍是字符串

**原因**：MaaFramework传递参数时可能进行双重JSON编码

**修复**：支持双重编码解析
```python
if isinstance(param, str):
    parsed = json.loads(param)
    if isinstance(parsed, str):
        param = json.loads(parsed)  # 第二次解析
    else:
        param = parsed
```

### 循环模式统一：从on_error改为JumpBack

**背景**：`MoveStick` 返回 `False` 用于 `on_error` 循环模式，但 `dispatch_result.json` 使用 JumpBack 循环模式

**辨析**：
- `on_error` 循环：返回 `False` → 触发 `on_error` → 循环
- JumpBack 循环：返回 `True` → 节点完成 → `next` 为空 → JumpBack 回上级

**修改**：
1. **MoveStick返回值**：改为返回 `True`
2. **dispatch_loop.json**：将所有 `on_error` 循环改为 JumpBack 循环

**修改的节点**：
- `探险派遣循环版_移动准星到地点`：移除 `on_error`，`next` 改为 `[]`
- `探险派遣循环版_移动准星到菜单顶部`：移除 `on_error`，`next` 改为 `[]`
- `探险派遣循环版_移动准星到人员`：移除 `on_error`，`next` 改为 `[]`

**新增检查节点**：
- `探险派遣循环版_点击地点`：改用 `FindCrosshairNearTarget` 检查准星是否到达
- `探险派遣循环版_检查菜单顶部`：新增节点，检查准星是否到达菜单顶部
- `探险派遣循环版_选择人员`：改用 `FindCrosshairNearTarget` 检查准星是否到达

### JumpBack循环模式总结

**正确模式**：
```json
{
    "查找目标": {
        "action": "ExtractOCRTarget",
        "next": ["选定目标", "[JumpBack]移动准星"]
    },
    "移动准星": {
        "recognition": "FindCrosshair",
        "action": "MoveStick",
        "next": []  // 空数组触发JumpBack
    },
    "选定目标": {
        "recognition": "FindCrosshairNearTarget",  // 检查是否到达
        "action": "TapButton",
        "next": ["下一步"]
    }
}
```

**执行流程**：
1. `查找目标` → 设置参数 → next列表：`[选定目标, JumpBack移动准星]`
2. 识别 `选定目标`（FindCrosshairNearTarget）
   - 命中（准星已到达）→ 执行 `选定目标` → 继续
   - 未命中 → 识别下一个节点 `移动准星`
3. 执行 `移动准星` → MoveStick返回 `True` → next为空 → JumpBack回第1步
4. 循环直到 `FindCrosshairNearTarget` 命中

---

## 光标控制功能实现（2026-06-15）

### 功能概述

发现游戏内准星与系统全局鼠标光标位置同步一致，可通过操作系统光标控制游戏内准星。

### 核心组件

#### 1. MoveCursor - 瞬时移动光标

```python
class MoveCursor(CustomAction):
    def run(self, context, argv):
        target_x = param.get('x', 960)
        target_y = param.get('y', 540)
        win32api.SetCursorPos((target_x, target_y))
```

**问题**：瞬时大距离移动可能被反作弊系统检测

#### 2. MoveCursorSmooth - 平滑移动光标

**目的**：模拟真实鼠标移动轨迹，避免被反作弊检测

**实现**：
```python
class MoveCursorSmooth(CustomAction):
    def run(self, context, argv):
        current_x, current_y = win32api.GetCursorPos()
        target_x, target_y = param['x'], param['y']
        duration = param.get('duration', 0.3)  # 移动总时间
        steps = param.get('steps', 30)         # 移动步数
        
        for i in range(1, steps + 1):
            # 计算当前步的目标位置（线性插值）
            progress = i / steps
            next_x = int(current_x + (target_x - current_x) * progress)
            next_y = int(current_y + (target_y - current_y) * progress)
            
            # 获取实际光标位置（避免累积误差）
            actual_x, actual_y = win32api.GetCursorPos()
            
            # 计算相对移动量
            move_x = next_x - actual_x
            move_y = next_y - actual_y
            
            # 执行相对移动
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
            time.sleep(duration / steps)
```

**参数**：
- `x`, `y`：目标坐标
- `duration`：移动总时间（默认0.3秒）
- `steps`：移动步数（默认30步）

### 累积误差问题与修复

**问题**：轨迹不够平滑，总是超出目标方向后最后又瞬间拉回

**原因**：`mouse_event(MOUSEEVENTF_MOVE)` 相对移动存在累积误差，理论计算位置和实际光标位置逐渐偏离

**修复**：每步移动前获取实际光标位置，计算到当前步目标位置的相对移动量

```python
# 错误：使用理论位置计算
prev_x = int(current_x + dx * (i - 1))
move_x = next_x - prev_x

# 正确：获取实际位置计算
actual_x, actual_y = win32api.GetCursorPos()
move_x = next_x - actual_x
```

### 测试验证

**测试Pipeline**：`cursor_test.json`
- 依次移动到：左上角(640,360) → 右上角(1280,360) → 右下角(1280,720) → 左下角(640,720) → 中心(960,540)

**验证结果**：
- ✅ 系统光标能控制游戏内准星
- ✅ 平滑移动轨迹流畅，无瞬间拉回

### 文件结构

**新增文件**：
- `agent/move_cursor.py` - MoveCursor和MoveCursorSmooth动作
- `assets/resource/pipeline/cursor_test.json` - 光标测试Pipeline

**修改文件**：
- `agent/agent_server.py` - 注册MoveCursor和MoveCursorSmooth
- `assets/interface.json` - 添加"测试光标移动"任务入口

---

## 药草种植功能优化与农场种植实现（2026-06-16）

### 功能概述

修复药草种植功能的OCR识别问题，并新增农场种植功能。

### OCR识别问题修复

#### 问题1：CheckWateringTimeText无法识别时间文本

**现象**：OCR识别到"1小时11分钟后可浇水"，但返回`hit=False`

**原因**：`JOCR`的`expected`参数用于精确匹配，无法部分匹配"小时"、"分"等关键字

**修复**：
```python
# 错误：使用expected精确匹配
ocr_param = JOCR(roi=roi, expected=["小时", "分"])

# 正确：不使用expected，获取所有文本后在代码中检查
ocr_param = JOCR(roi=roi)
for r in result.all_results:
    if '小时' in r.text or '分' in r.text:
        hit = True
        text = r.text
        break
```

#### 问题2：OCRResult文本属性访问错误

**现象**：访问`r.detail`无法获取OCR识别的文本

**原因**：`OCRResult`的识别文本在`text`属性中，而不是`detail`属性

**修复**：
```python
# 错误：访问detail属性
text = r.detail if hasattr(r, 'detail') else ''

# 正确：访问text属性
text = r.text if hasattr(r, 'text') else ''
```

### CheckTilledField重构

#### 原设计问题

使用`expected`过滤，只能识别特定文本，无法处理其他情况。

#### 新设计

**CheckTilledField**：
- 移除`expected`过滤，获取ROI内所有文本
- 返回`{'texts': [所有识别到的文本]}`

**IncrementPlantCountIfHit**：
- 未识别到文本：保持计数不变
- 识别到"需要在已开垦田地上播种"：计数加一
- 识别到其他文本：计数清零

```python
if not texts:
    # 未识别到文本，啥也不做
    log(f"保持计数: {controller.plant_count}")
elif any("需要在已开垦田地上播种" in t for t in texts):
    # 识别到目标文本，次数加一
    controller.increment_count()
else:
    # 识别到其他文本，次数清零
    controller.plant_count = 0
    log(f"识别到其他文本{texts}，计数清零")
```

### 传送准星移动逻辑重构

#### 原设计问题

使用`on_error`循环机制，逻辑复杂：
```
查找目标位置 → 晃动准星 → 移动准星循环(on_error) → 点击目标
```

#### 新设计

使用`MoveCursorSmooth`平滑移动，简化流程：
```
查找目标位置 → 移动准星到目标(MoveCursorSmooth) → 点击目标
```

**修改内容**：
- 移除"通用_传送_晃动准星"任务
- 移除"通用_传送_移动准星循环"任务
- 新增"通用_传送_移动准星到目标"任务，使用`MoveCursorSmooth`

### MoveCursorSmooth参数名修复

#### 问题

`ExtractOCRTarget`传递`target_x/target_y`，但`MoveCursorSmooth`读取`x/y`，导致坐标丢失。

#### 修复

兼容两种参数名：
```python
target_x = param.get('x', param.get('target_x', 960))
target_y = param.get('y', param.get('target_y', 540))
```

### 农场种植功能实现

#### 功能概述

基于药草种植功能，新增农场种植功能，支持种植作物：
- 胭纱云棉
- 冰魄辣椒
- 旭日辣椒
- 魔露冰桃

#### 与药草种植的差异

| 功能 | 药草种植 | 农场种植 |
|------|---------|---------|
| 传送目标 | 培养箱 | 农贸作物 |
| 左移一步 | 有（左摇杆向左） | 无 |
| 翻页查找 | TapButton(RB) | MoveStickOnce(右摇杆向下) |
| 物品名称 | 药材（东方笙、铜碎薇等） | 作物（胭纱云棉、冰魄辣椒等） |

#### Pipeline配置

**farm.json**（基于herb.json修改）：
- 传送目标改为农贸作物
- 移除"左移一步"节点
- 所有"药材"改为"作物"
- 翻页查找使用右摇杆向下推动

```json
{
    "农场种植_翻页查找作物": {
        "recognition": "DirectHit",
        "action": "Custom",
        "custom_action": "MoveStickOnce",
        "custom_action_param": "{\"stick\": \"right\", \"x\": 0, \"y\": 30000, \"duration\": 0.2}",
        "post_delay": 500,
        "next": []
    }
}
```

#### interface.json配置

**新增任务**：
```json
{
    "name": "FarmPlant",
    "label": "农场种植",
    "entry": "农场种植_开始",
    "option": ["crop_name"],
    "pipeline_override": {
        "通用_传送_查找目标位置": {
            "recognition": {
                "type": "OCR",
                "param": {"expected": ["农贸作物"]}
            }
        },
        "通用_传送_等待加载": {
            "next": ["农场种植_传送完成等待"]
        }
    }
}
```

**新增选项**：
```json
{
    "crop_name": {
        "type": "select",
        "label": "作物名称",
        "cases": [
            {"name": "胭纱云棉", "label": "胭纱云棉"},
            {"name": "冰魄辣椒", "label": "冰魄辣椒"},
            {"name": "旭日辣椒", "label": "旭日辣椒"},
            {"name": "魔露冰桃", "label": "魔露冰桃"}
        ],
        "default_case": "胭纱云棉"
    }
}
```

### 文件结构

**新增文件**：
- `assets/resource/pipeline/farm.json` - 农场种植Pipeline配置

**修改文件**：
- `agent/herb_controller.py` - 修复OCR识别逻辑，重构CheckTilledField
- `agent/move_cursor.py` - 修复参数名兼容性
- `assets/resource/pipeline/teleport_common.json` - 重构准星移动逻辑
- `assets/interface.json` - 新增农场种植任务和作物选项

### 技术要点总结

1. **OCR识别**：
   - `JOCR`的`expected`用于精确匹配，不适合部分匹配场景
   - `OCRResult`的文本在`text`属性中
   - 不使用`expected`时需要遍历`all_results`检查

2. **自定义识别器返回值**：
   - `detail`需要是JSON字符串（`json.dumps()`）
   - 始终返回命中确保action执行和next列表扫描

3. **参数传递**：
   - 不同组件间参数名需要统一
   - 使用`get()`的默认值实现兼容

   4. **Pipeline设计**：
    - `MoveCursorSmooth`比摇杆移动更简单可靠
    - 右摇杆用于菜单滚动，左摇杆用于角色移动

---

## 光标平滑移动优化与牧场管理实现（2026-06-17~2026-06-18）

### 功能概述

优化光标平滑移动算法，解决光标环绕问题，并新增牧场管理功能。

### 光标平滑移动问题演进

#### 问题1：光标环绕现象

**现象**：长距离移动时光标在屏幕边缘(1919, 0)和(0, 1079)反复跳跃

**原因**：`mouse_event(MOUSEEVENTF_MOVE)`相对移动在移动量过大时触发环绕

**尝试方案1**：增加步数，每步移动不超过50像素
- 结果：仍有环绕问题

**尝试方案2**：改用绝对位置移动（`SetCursorPos`）
- 结果：高频调用更容易被检测

**最终方案**：固定帧率 + 缓动函数

#### 最终实现：固定帧率 + 缓动函数

**核心设计**：
```python
class MoveCursorSmooth(CustomAction):
    def __init__(self):
        self.fps = 60  # 固定60帧
        self.frame_delay = 1.0 / self.fps  # 每帧16.6ms
    
    def run(self, context, argv):
        # 步数基于时间计算
        total_steps = max(1, int(duration * self.fps))
        
        for step in range(1, total_steps + 1):
            progress = step / total_steps
            
            # 缓动函数：开始慢、中间快、结束慢
            progress = progress * progress * (3 - 2 * progress)
            
            # 线性插值
            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress
            
            # 绝对位置移动
            self.set_cursor_pos(current_x, current_y)
            time.sleep(self.frame_delay)
        
        # 最终位置保底
        self.set_cursor_pos(target_x, target_y)
```

**优势**：
- ✅ 时间控制精确：duration=0.3s → 18步，耗时精确0.3秒
- ✅ 性能稳定：每帧固定16.6ms
- ✅ 缓动函数自然：符合人类移动习惯
- ✅ 使用ctypes直接调用user32.dll，更底层

**缓动函数**：
```
f(t) = t² * (3 - 2t)
```
- t=0.0 → f(t)=0.0（开始）
- t=0.5 → f(t)=0.5（中点）
- t=1.0 → f(t)=1.0（结束）
- 导数：f'(t) = 6t(1-t)，在t=0和t=1时为0（平滑）

### 领取派遣功能优化

#### 循环模式重构

**原设计**：
- 固定选择index 0/1/2
- 当日派遣当日领取，完成派遣的索引号不变
- 特殊情况（当天派遣，第二天领取）时，点击后文本变为"空闲中"

**新设计（循环实现）**：
- 循环模式，index自增
- 通过index控制器动态修改OCR的index参数
- OCR未命中说明已全部处理，退出派遣画面
- 简化实现，避免重复节点

#### index控制器实现

**新增文件**：`agent/dispatch_result_controller.py`

**核心类**：
```python
class DispatchResultController:
    _instance = None  # 单例模式
    
    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.current_index = 0
            instance.initialized = False
            cls._instance = instance
        return cls._instance

class SetDispatchResultIndex(CustomAction):
    """动态修改OCR的index参数"""
    def run(self, context, argv):
        controller = DispatchResultController()
        override_data = {
            "领取派遣_查找完成派遣": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "expected": ["完成派遣"],
                        "index": controller.current_index
                    }
                }
            }
        }
        context.override_pipeline(override_data)

class IncrementDispatchResultIndex(CustomAction):
    """递增index计数"""
    def run(self, context, argv):
        controller = DispatchResultController()
        controller.increment()
```

**流程**：
```
开始循环 → SetDispatchResultIndex(index=0)
  → 查找完成派遣(index=0) → 命中 → 处理 → IncrementDispatchResultIndex
  → 查找完成派遣(index=1) → 命中 → 处理 → IncrementDispatchResultIndex
  → 查找完成派遣(index=2) → 命中 → 处理 → IncrementDispatchResultIndex
  → 查找完成派遣(index=3) → 未命中 → 退出派遣画面
```

### 牧场管理功能实现

#### 功能概述

自动管理牧场多个区域，包括：
- 召集动物（Y键）
- 收集产物（点击RB识别收获图像）
- 添加饲料（点击RB打开对话框，X确认）
- 边界检测（OCR识别"当前位置无法操作"）

#### Pipeline设计

**JumpBack循环机制**：
```
向前到栏杆
  ↓
点击RB循环 (设置JumpBack标记)
  → 识别收获图像(模板匹配)
    - 命中 → 点击RB → next=[] → JumpBack回向前到栏杆
    - 未命中 → 添加饲料 → 点击RB
      → 检查边界(OCR:当前位置无法操作)
        - 命中 → 区域完成 → StopTask
        - 未命中 → 检查对话框
      → 检查对话框(OCR:添加饲料)
        - 命中 → 关闭对话框 → 左移一步 → next=[] → JumpBack回向前到栏杆
```

**区域管理**：
- 每个区域独立Pipeline文件：ranch1.json、ranch2.json
- 区域一：向左移动（x: -30000）
- 区域二：向右移动（x: 30000）

#### 关键节点

**识别收获图像**：
```json
{
    "recognition": {
        "type": "TemplateMatch",
        "param": {
            "roi": [1750, 950, 80, 130],
            "template_name": "shouhuo.png",
            "threshold": 0.7
        }
    },
    "action": "Custom",
    "custom_action": "TapButton",
    "custom_action_param": "{\"button\": \"RB\"}"
}
```

**检查对话框**：
```json
{
    "recognition": {
        "type": "OCR",
        "param": {
            "roi": [480, 270, 125, 45],
            "expected": ["添加饲料"]
        }
    }
}
```

**检查边界**：
```json
{
    "recognition": {
        "type": "OCR",
        "param": {
            "roi": [820, 180, 280, 40],
            "expected": ["当前位置无法操作"]
        }
    }
}
```

### 文件结构

**新增文件**：
- `agent/dispatch_result_controller.py` - 领取派遣index控制器
- `assets/resource/pipeline/ranch1.json` - 牧场区域一管理
- `assets/resource/pipeline/ranch2.json` - 牧场区域二管理

**修改文件**：
- `agent/move_cursor.py` - 重构为固定帧率+缓动函数
- `agent/agent_server.py` - 注册新的action
- `assets/resource/pipeline/dispatch_result.json` - 重构为循环模式
- `assets/resource/pipeline/dispatch_loop.json` - 准星移动改用MoveCursorSmooth
- `assets/interface.json` - 新增牧场管理任务

### 技术要点总结

1. **光标移动**：
   - 固定帧率（60fps）比动态步数更稳定
   - 缓动函数让移动更自然类人
   - 最终位置保底确保准确性

2. **循环控制**：
   - 单例模式管理状态
   - `context.override_pipeline`动态修改参数
   - OCR未命中作为退出条件

3. **Pipeline设计**：
   - JumpBack循环实现重复操作
    - 多区域用多文件实现，避免复杂的参数化
    - StopTask强制终止任务

---

## 好友浇水功能实现（2026-06-20）

### 功能概述

实现为好友农场自动浇水功能，支持自定义好友列表，自动识别浇水按钮并执行浇水操作。

### 核心设计

#### 1. 两层循环结构

```
好友列表循环（外层）
  ├─ 检查更多好友（CheckMoreFriends）
  │   - 有更多好友 → 继续处理
  │   - 无更多好友 → 任务完成
  └─ 当前好友处理
      ├─ 打开好友菜单
      ├─ 查找好友名称（OCR）
      ├─ 检查浇水按钮
      │   - 找到 → 传送 → 浇水 → 回家
      │   - 未找到 → 下一个好友
      └─ 下一好友（NextFriend）
```

#### 2. JumpBack机制应用

**好友列表循环**：
```json
{
    "好友浇水_好友列表循环": {
        "next": ["好友浇水_检查更多好友", "[JumpBack]好友浇水_当前好友"]
    },
    "好友浇水_下一好友": {
        "next": []
    }
}
```

**流程**：
- 初始化 → 检查更多好友 → 当前好友处理 → 下一好友（next=[]触发JumpBack）
- JumpBack返回好友列表循环的next列表 → 重新检查更多好友

#### 3. 浇水按钮识别

**CheckWateringButtonByOCR**：
- 根据好友名称OCR结果计算ROI
- 好友名称box左上角横坐标固定为1200
- ROI范围：[box_x, box_y, 640, 100]
- 使用原生TemplateMatch匹配jiaoshui.png模板

**MoveCursorToWateringButton**：
- 目标坐标：好友名称box左上角 + (595, 40)
- 使用SetCursorPos移动准星

### 核心组件

#### 1. FriendListController - 好友列表控制器

单例模式，管理好友列表和当前索引：

```python
class FriendListController:
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
```

**关键方法**：
- `set_friend_list(friend_list)`：设置好友列表，重置索引
- `get_current_friend()`：获取当前好友名称
- `next_friend()`：移动到下一个好友，清零water_count
- `has_more()`：是否还有更多好友

#### 2. CheckWateredField - 检查已浇水田地

识别"这里不是可摘取的地方"文本，判断是否已浇水：

```python
class CheckWateredField(CustomRecognition):
    def analyze(self, context, argv):
        # OCR识别ROI内所有文本
        ocr_param = JOCR(roi=roi)
        result = context.run_recognition_direct(...)
        
        # 收集所有文本
        texts = [r.text for r in result.all_results]
        
        # 返回所有文本供后续判断
        return AnalyzeResult(detail=json.dumps({'texts': texts}))
```

#### 3. IncrementWaterCountIfHit - 更新浇水计数

根据识别结果更新计数：

```python
class IncrementWaterCountIfHit(CustomAction):
    def run(self, context, argv):
        texts = detail.get('texts', [])
        
        if not texts:
            # 未识别到文本，保持计数
            pass
        elif any("这里不是可摘取的地方" in t for t in texts):
            # 识别到目标文本，计数加一
            controller.water_count += 1
        else:
            # 识别到其他文本，计数清零
            controller.water_count = 0
```

#### 4. CheckWaterCount - 检查浇水计数

判断是否完成浇水（计数 >= 阈值）：

```python
class CheckWaterCount(CustomRecognition):
    def analyze(self, context, argv):
        threshold = param.get('threshold', 10)
        
        if controller.water_count >= threshold:
            return (960, 540, 100, 100)  # 命中，退出循环
        return None  # 未命中，继续循环
```

### Pipeline流程

```
开始 → 传送到农贸作物 → 等待加载
  ↓
好友列表循环（InitFriendList）
  ↓
检查更多好友（CheckMoreFriends）
  - 有更多好友 → 当前好友处理
  - 无更多好友 → 完成
  ↓
当前好友处理（CheckCurrentFriend设置OCR参数）
  ↓
打开好友菜单（OpenFriendMenu）
  ↓
移动准星到菜单顶部
  ↓
查找好友（OCR识别好友名称）
  ↓
检查浇水按钮（CheckWateringButtonByOCR）
  - 找到 → 移动准星 → 点击传送 → 确认传送
  - 未找到 → 关闭菜单 → 下一好友
  ↓
初始化种植循环
  ↓
种植循环（前进一步 → 点击RB → 检查已浇水田地）
  ↓
退出种植循环（CheckWaterCount计数>=3）
  ↓
下一好友（NextFriend清零water_count）
  ↓
JumpBack返回好友列表循环
```

### 关键技术点

#### 1. ExtractOCRTarget参数传递

使用`next_tasks`同时传递坐标给多个任务：

```json
{
    "custom_action_param": "{\"next_tasks\": [[\"好友浇水_检查浇水按钮\", \"near_target\"], [\"好友浇水_移动准星到浇水按钮\", \"move\"]]}"
}
```

**类型说明**：
- `"near_target"`：传递`custom_recognition_param`（给识别器）
- `"move"`：传递`custom_action_param`（给动作）

#### 2. 模板路径自动检测

支持开发环境和发布包两种路径：

```python
dev_path = Path(__file__).parent.parent / 'assets' / 'resource' / 'image'
release_path = Path(__file__).parent.parent / 'resource' / 'image'
template_dir = dev_path if dev_path.exists() else release_path
```

#### 3. NextFriend计数清零

为下一个好友准备环境：

```python
def next_friend(self):
    self.current_index += 1
    # 清零浇水计数，避免下一个好友立刻满足退出条件
    self.water_count = 0
```

#### 4. 滚动菜单使用原生方向键

避免摇杆滚动不稳定：

```json
{
    "好友浇水_滚动菜单": {
        "action": "Custom",
        "custom_action": "TapButton",
        "custom_action_param": "{\"button\": \"DPAD_DOWN\"}",
        "repeat": 4
    }
}
```

### 配置说明

#### interface.json配置

```json
{
    "name": "FriendWatering",
    "label": "好友浇水",
    "entry": "好友浇水_开始",
    "option": ["friend_list"],
    "pipeline_override": {
        "通用_传送_查找目标位置": {
            "recognition": {
                "type": "OCR",
                "param": {"expected": ["农贸作物"]}
            }
        }
    }
}
```

#### 好友列表选项

```json
{
    "friend_list": {
        "type": "input",
        "inputs": [{
            "name": "friend_list_json",
            "default": "{\"friend_list\": [\"Trueman\"]}"
        }],
        "pipeline_override": {
            "好友浇水_好友列表循环": {
                "custom_action_param": "{friend_list_json}"
            }
        }
    }
}
```

### 开发过程总结

#### 第一阶段：基础框架搭建
1. 创建friend_list_controller.py，实现好友列表管理
2. 实现InitFriendList、CheckCurrentFriend、CheckMoreFriends、NextFriend
3. 设计两层循环结构

#### 第二阶段：好友查找与浇水
1. 实现OpenFriendMenu打开好友菜单
2. 实现GoHome回家动作
3. 实现CheckWateringButtonByOCR识别浇水按钮
4. 实现MoveCursorToWateringButton移动准星

#### 第三阶段：浇水循环
1. 参考herb_controller.py实现CheckWateredField
2. 实现IncrementWaterCountIfHit和CheckWaterCount
3. 设计浇水循环退出机制

#### 第四阶段：问题修复
1. **NextFriend逻辑修正**：从循环前移到循环尾，恢复无脑加1
2. **CheckWateringButtonByOCR改为CustomRecognition**：未命中时触发next[1]
3. **ROI计算修正**：好友名称box左上角横坐标固定为1200
4. **模板路径自动检测**：支持开发和发布环境
5. **滚动菜单改用方向键**：避免摇杆不稳定
6. **计数清零**：NextFriend清零water_count

### 文件结构

**新增文件**：
- `agent/friend_list_controller.py` - 好友列表控制器和相关识别器/动作

**修改文件**：
- `agent/agent_server.py` - 注册新的识别器和动作
- `assets/resource/pipeline/farmforfriends.json` - 好友浇水Pipeline
- `assets/interface.json` - 新增好友浇水任务和选项

### 技术要点总结

1. **JumpBack循环**：
   - 空next数组触发JumpBack
   - 返回被标记节点所在的next列表
   - 理解节点上下级关系至关重要

2. **CustomRecognition vs CustomAction**：
   - CustomRecognition返回None触发next[1]
   - CustomAction返回False不触发next[1]
   - 需要根据流程选择正确的类型

3. **参数传递**：
   - ExtractOCRTarget使用next_tasks传递坐标
   - near_target类型传递给识别器
   - move类型传递给动作

4. **状态管理**：
   - 单例模式管理好友列表和计数
   - NextFriend清零计数避免状态污染
   - 每次任务开始重置状态

5. **原生方法优先**：
   - TemplateMatch比手动cv2.matchTemplate更简单
   - 方向键比摇杆滚动更稳定
   - SetCursorPos比摇杆移动更直接
