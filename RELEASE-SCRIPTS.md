# 发布脚本使用说明

## 概述

本项目的Git工作流采用**双分支策略**：
- **本地main分支**：保留完整开发历史（250+提交），方便回溯、调试
- **本地release分支**：干净历史，只有版本发布提交
- **GitHub main分支**：= 本地release分支，保持整洁

## 初始化（首次使用）

```powershell
# 初始化release分支并推送到GitHub
.\init-release.ps1 "v2.0.0 - 初始版本"
```

执行后会：
1. 创建孤立分支`release`（没有父提交）
2. 添加所有文件（排除DEVELOPMENT.md）
3. 提交初始版本
4. 推送到GitHub的main分支
5. 切回原分支继续开发

## 发布新版本

```powershell
# 发布新版本到GitHub
.\push-release.ps1 "v2.1.0 - 新增好友浇水功能"
```

执行后会：
1. 切换到release分支
2. 从main分支获取最新代码（不合并历史）
3. 添加所有文件（排除DEVELOPMENT.md）
4. 提交新版本
5. 推送到GitHub的main分支
6. 切回原分支继续开发

## 日常开发流程

```powershell
# 1. 在main分支正常开发（保留所有历史）
git add -A
git commit -m "修复XXX问题"
git commit -m "新增YYY功能"
# ... 很多提交 ...

# 2. 准备发布时
.\push-release.ps1 "v2.1.0 - 新功能描述"

# 3. 继续开发
git add -A
git commit -m "继续开发..."
```

## 目录结构

```
本地仓库：
├── main分支（完整历史）
│   ├── 开发提交1
│   ├── 开发提交2
│   └── ... (250+提交)
└── release分支（干净历史）
    ├── v2.0.0
    ├── v2.1.0
    └── ...

GitHub仓库：
└── main分支（= 本地release分支）
    ├── v2.0.0
    ├── v2.1.0
    └── ...
```

## 为什么排除DEVELOPMENT.md？

DEVELOPMENT.md包含详细的开发过程记录，包括：
- 问题演进
- 调试过程
- 失败尝试
- 技术细节

这些对开发者有价值，但对用户无意义，所以发布时排除。

## 优势

✅ **本地**：完整历史，方便回溯、调试、撤销
✅ **GitHub**：干净整洁，只显示版本发布
✅ **简单**：一个命令完成发布
✅ **安全**：本地历史永远不会丢失

## 注意事项

1. **首次使用**：先运行`init-release.ps1`初始化
2. **后续发布**：使用`push-release.ps1`发布新版本
3. **不要在release分支开发**：只在main分支开发
4. **推送失败**：检查网络连接和GitHub权限