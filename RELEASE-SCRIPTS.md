# 发布脚本使用说明

## 概述

本项目的Git工作流采用**双分支策略**：
- **本地main分支**：保留完整开发历史（250+提交），方便回溯、调试
- **本地release分支**：干净历史，只有版本发布提交
- **GitHub main分支**：= 本地release分支，保持整洁
- **Tag管理**：tag只在GitHub上存在，本地不保留

## 使用方式

### 统一脚本（推荐）

```powershell
# 初始化release分支
.\release.ps1 init v2.0.0 "初始版本"

# 发布新版本
.\release.ps1 push v2.1.0 "新增好友浇水功能"
```

### 兼容旧脚本（已废弃）

```powershell
# 旧方式（仍可用，但建议迁移到新方式）
.\init-release.ps1 v2.0.0 "初始版本"
.\push-release.ps1 v2.1.0 "新增好友浇水功能"
```

## 初始化（首次使用）

```powershell
.\release.ps1 init v2.0.0 "初始版本"
```

执行后会：
1. 创建孤立分支`release`（没有父提交）
2. 添加所有文件（排除DEVELOPMENT.md）
3. 提交初始版本
4. 推送到GitHub的main分支
5. 在GitHub创建tag v2.0.0（本地不保留）
6. 切回原分支继续开发

## 发布新版本

```powershell
.\release.ps1 push v2.1.0 "新增好友浇水功能"
```

执行后会：
1. 切换到release分支
2. **清空release分支所有文件**（确保删除的文件不会残留在GitHub）
3. 从main分支获取最新代码（不合并历史）
4. 添加所有文件（排除DEVELOPMENT.md）
5. 提交新版本
6. 强制推送到GitHub的main分支
7. 删除GitHub上的旧tag（如果存在）
8. 在GitHub创建新tag v2.1.0（本地不保留）
9. 触发CI流程
10. 切回原分支继续开发

## 日常开发流程

```powershell
# 1. 在main分支正常开发（保留所有历史）
git add -A
git commit -m "修复XXX问题"
git commit -m "新增YYY功能"
# ... 很多提交 ...

# 2. 准备发布时
.\release.ps1 push v2.1.0 "新功能描述"

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
├── main分支（= 本地release分支）
│   ├── v2.0.0
│   ├── v2.1.0
│   └── ...
└── tags
    ├── v2.0.0（触发CI）
    ├── v2.1.0（触发CI）
    └── ...
```

## Tag管理策略

- ✅ **本地不保留tag**：避免指向旧内容，防止覆盖文件修改
- ✅ **tag只在GitHub上存在**：用于版本发布和CI触发
- ✅ **强制覆盖旧tag**：删除GitHub上的旧tag后重新创建，确保CI触发
- ✅ **参数格式**：`.\push-release.ps1 <version> <message>`

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
✅ **CI触发**：强制覆盖tag确保CI流程触发

## 注意事项

1. **首次使用**：先运行 `.\release.ps1 init` 初始化
2. **后续发布**：使用 `.\release.ps1 push` 发布新版本
3. **不要在release分支开发**：只在main分支开发
4. **推送失败**：检查网络连接和GitHub权限
5. **重复发布**：可以重复发布同一版本号，会强制覆盖GitHub上的tag
6. **本地无tag**：本地不保留tag，tag只在GitHub上存在
7. **脚本合并**：`init-release.ps1` 和 `push-release.ps1` 已废弃，建议使用统一的 `release.ps1`
8. **文件清理**：推送前会清空release分支，确保本地已删除的文件不会残留在GitHub
9. **强制推送**：使用`--force`推送到GitHub，确保远程完全同步本地状态

## 常见问题

### Q: 为什么GitHub上还有本地已删除的文件？

A: 已修复！现在的release.ps1会在推送前先清空release分支所有文件（`git rm -rf .`），然后再从main分支获取文件，确保删除的文件不会残留在GitHub。

### Q: 为什么本地main分支和origin/main分支分叉了？

A: 这是正常的！
- **本地main**：保留完整开发历史（便于开发、调试、回溯）
- **远程origin/main**：干净的发布历史（便于用户查看）
- 两者用途不同，不需要同步

### Q: 未修改的文件为什么显示旧的tag信息？

A: 这是git的正常行为。Git只追踪文件的修改，未修改的文件会保留之前的提交信息，但文件内容是最新的，不影响使用。