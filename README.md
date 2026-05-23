<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/logo/maa-logo_512x512.png" width="256" height="256" />
</p>

<div align="center">

# MaaFisher - 王者荣耀世界自动钓鱼助手

</div>

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 开发的王者荣耀世界游戏自动钓鱼助手。

## 特性

- 基于图像识别的自动化操作
- 使用虚拟手柄绕过游戏键鼠屏蔽
- 使用 MFAAvalonia 通用 UI
- 低代码 JSON 配置，易于维护和扩展

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或双击运行：
```
tools/MFAAvalonia/DependencySetup_依赖库安装_win.bat
```

### 2. 启动程序

**方式 A（推荐）**：双击 `启动钓鱼助手.bat`

**方式 B**：
```
cd tools/MFAAvalonia
启动UI.bat
```

### 3. 配置项目

首次运行需要配置项目路径：

1. 在 MFAAvalonia 中点击右上角 **设置**
2. 选择资源路径：`assets/interface.json`
3. 保存

### 4. 运行钓鱼

1. 选择任务 "开始钓鱼"
2. 点击 **运行** 按钮

## 项目结构

```
HKWorld/
├── agent/                      # 自定义扩展
│   ├── agent_server.py         # Agent 服务注册
│   ├── custom_action.py        # 虚拟手柄控制
│   ├── fishing_recognition.py  # 多模板匹配识别器
│   └── fishing_action.py       # 识别结果处理
├── assets/
│   └── resource/
│       ├── image/              # 图像模板(14个)
│       ├── model/ocr/          # OCR 模型
│       └── pipeline/           # Pipeline 配置
├── tools/
│   └── MFAAvalonia/            # 通用 UI
│       ├── MFAAvalonia.exe     # 主程序
│       ├── 启动UI.bat          # 启动脚本
│       └── start_agent.py      # Agent 启动
├── venv/                       # Python 虚拟环境
├── assets/interface.json       # 项目配置
├── 启动钓鱼助手.bat            # 快速启动
└── requirements.txt            # Python 依赖
```

## 前置要求

### 1. ViGEmBus 驱动

虚拟手柄需要 ViGEmBus 驱动：

- 下载：https://github.com/ViGEm/ViGEmBus
- 安装后重启电脑

### 2. OCR 模型

从 [MaaCommonAssets/OCR](https://github.com/MaaXYZ/MaaCommonAssets/tree/main/OCR) 下载：

- `det.onnx` - 文字检测模型
- `rec.onnx` - 文字识别模型
- `keys.txt` - 字符字典

放置到 `assets/resource/model/ocr/`

## 常见问题

### Q: 找不到游戏窗口
A: 确保游戏已启动，窗口标题包含 "王者荣耀世界"

### Q: Agent 连接失败
A:
1. Agent 由 interface.json 自动启动
2. 检查 Python 环境：`venv/Scripts/python.exe`

### Q: 虚拟手柄不工作
A: 需要安装 ViGEmBus 驱动并重启

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
- [如何开发](./docs/zh_cn/develop/how_to_develop.md) - MaaFramework 开发指南

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本项目作出的贡献：

[![Contributors](https://contrib.rocks/image?repo=MaaXYZ/MaaFramework&max=1000)](https://github.com/MaaXYZ/MaaFramework/graphs/contributors)

## 许可证

MIT License
