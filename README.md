<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/logo/maa-logo_512x512.png" width="256" height="256" />
</p>

<div align="center">

# MaaHKWorld - 王者荣耀世界游戏助手

</div>

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 开发的王者荣耀世界游戏助手，目前仅支持自动钓鱼，之后准备添加自动浇水、收菜、派遣等辅助功能。

## 特性

- 基于图像识别的自动化操作
- 使用虚拟手柄绕过游戏键鼠屏蔽
- 支持后台运行（窗口可最小化）
- 使用 MFAAvalonia 通用 UI


## 快速开始

### 前置要求

1. **Python 3.8+** - [下载地址](https://www.python.org/downloads/)
2. **ViGEmBus 驱动** - [下载地址](https://github.com/ViGEm/ViGEmBus)（安装后重启电脑）

### 下载与启动

1. 从 [Releases](https://github.com/letmebe/HKWorld/releases) 下载最新版本 `MaaHKWorld-win-x86_64-*.zip`

2. 解压后双击 **`启动钓鱼助手.bat`**

3. 首次运行会自动：
   - 创建虚拟环境 `venv/`
   - 安装 `maafw`, `vgamepad`, `pywin32`等依赖

4. 启动游戏，启用鱼竿后进入钓鱼场景，注意确保鱼饵充足，水面背景干净文字清晰，尤其要保证右下角的抛竿等指令区域不能有干扰（类似下图所示）：
![示例场景](./assets/resource/image/example.png)

5. 在 MFAAvalonia 中选择任务 "开始钓鱼"，点击 **开始任务**

## 项目结构

```
MaaHKWorld/
├── agent/                      # 自定义扩展
│   ├── agent_server.py         # Agent 服务注册
│   ├── custom_action.py        # 虚拟手柄控制、窗口激活
│   ├── fishing_recognition.py  # 多模板匹配识别器（灰度图优化）
│   ├── fishing_action.py       # 识别结果处理动作
│   ├── logger.py               # 统一日志模块（按日期轮转）
│   └── logs/                   # 运行日志（自动清理）
├── assets/
│   ├── resource/
│   │   ├── image/              # 图像模板
│   │   ├── model/ocr/          # OCR 模型（由CI自动配置）
│   │   └── pipeline/           # Pipeline 配置
│   ├── MaaCommonAssets/        # OCR 模型 submodule
│   └── interface.json          # 项目配置
├── tools/                      # CI/CD 工具
│   └── install.py              # CI 安装脚本（路径自动适配）
├── venv/                       # Python 虚拟环境（自动创建）
├── 启动钓鱼助手.bat            # 启动脚本（自动配置环境）
└── requirements.txt            # Python 依赖
```

## 配置说明

### 控制器配置 (interface.json)

当前配置支持后台运行：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| screencap | FramePool | 极快，支持后台截图 (Win10 1903+) |
| mouse | SendMessage | 支持后台输入 |
| keyboard | SendMessage | 支持后台输入 |

### 平台支持

当前仅支持 **Windows x86_64**，其他平台构建已禁用。

## 开发

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化 submodule
git submodule update --init --recursive
```

### 发布版本

```bash
# 提交代码
git add .
git commit -m "feat: 新功能"
git push

# 创建 tag 触发 CI 构建
git tag v1.0.0
git push origin v1.0.0
```

CI 会自动打包 MFAAvalonia + 项目资源并发布到 Releases。

## 常见问题

### Q: 找不到游戏窗口
A: 确保游戏已启动，窗口标题包含 "王者荣耀世界"

### Q: Agent 连接失败
A:
1. Agent 由 interface.json 自动启动
2. 检查 Python 环境：`venv/Scripts/python.exe`

### Q: 虚拟手柄不工作
A: 需要安装 ViGEmBus 驱动并重启，正常情况下MFAAvalonia开始任务后，右下角托盘区域会出现Xbox360控制器图标，听到设备连接的提示声。

### Q: 识别失败
A:
1. 检查图像模板是否正确
2. 查看日志：`tools/MFAAvalonia/logs/agent.log`

## 技术栈

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework) - 自动化框架
- [vgamepad](https://github.com/yshrd/vgamepad) - 虚拟手柄
- [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia) - 通用 UI

## 文档

- [开发指南](DEVELOPMENT.md) - 开发环境、架构说明、开发复盘

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本项目作出的贡献：

[![Contributors](https://contrib.rocks/image?repo=MaaXYZ/MaaFramework&max=1000)](https://github.com/MaaXYZ/MaaFramework/graphs/contributors)

## 许可证

MIT License
