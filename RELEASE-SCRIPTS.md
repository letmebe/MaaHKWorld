# 发布脚本使用说明

## 概述

本项目的Git工作流采用**单分支策略**：
- **本地main分支**：保留完整开发历史（250+提交），方便回溯、调试
- **GitHub main分支**：干净历史，只有版本发布提交（通过临时orphan分支推送）
- **Tag管理**：tag只在GitHub上存在，本地不保留

## 使用方式

```powershell
# 发布新版本
.\release.ps1 push v2.1.0 "新增好友浇水功能"
```

## 发布新版本

```powershell
.\release.ps1 push v2.1.0 "新增好友浇水功能"
```

执行后会：
1. 检查当前分支，如果不是main则切换到main
2. 创建临时orphan分支（`release-temp-随机数`）
3. **清空索引**（使用`--cached`保留工作目录文件，包括.gitignore）
4. 添加.gitignore（使其忽略规则生效）
5. 添加.gitmodules和submodule引用（使用`git update-index --cacheinfo 160000`）
6. 添加所有文件（排除DEVELOPMENT.md和submodule路径）
7. 提交新版本
8. 强制推送到GitHub的main分支
9. 删除GitHub上的旧tag（如果存在）
10. 在GitHub创建新tag v2.1.0（本地创建后立即删除）
11. 切回原分支
12. 删除临时orphan分支（本地不保留release分支）
13. 触发CI流程

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
└── main分支（完整历史）
    ├── 开发提交1
    ├── 开发提交2
    └── ... (250+提交)

GitHub仓库：
├── main分支（干净历史）
│   ├── v2.0.0
│   ├── v2.1.0
│   └── ...
└── tags
    ├── v2.0.0（触发CI）
    ├── v2.1.0（触发CI）
    └── ...
```

## 关键技术细节

### 1. 临时orphan分支

- 使用`git checkout --orphan`创建无父提交的临时分支
- 分支名格式：`release-temp-随机数`
- 推送后立即删除，本地不保留release分支

### 2. 索引清空（--cached）

```powershell
git rm -rf . --cached
```

- `--cached`参数：只清空索引，保留工作目录文件
- 保留.gitignore文件，确保后续`git add --all`遵循忽略规则
- 避免venv/、tools/MFAAvalonia/等被错误提交

### 3. Submodule处理

```powershell
# 添加.gitmodules
git add .gitmodules

# 添加submodule gitlink引用
git update-index --add --cacheinfo "160000,$submoduleCommit,$submodulePath"
```

- 使用`git update-index --cacheinfo 160000`添加submodule引用（而非目录内容）
- 从`git add --all`中排除submodule路径
- 确保GitHub CI能正确初始化submodule（`actions/checkout@v4` with `submodules: true`）

### 4. 文件排除

- DEVELOPMENT.md：排除开发过程记录
- submodule路径：已作为gitlink添加，不再作为普通目录

## Tag管理策略

- ✅ **本地不保留tag**：避免指向旧内容，防止覆盖文件修改
- ✅ **tag只在GitHub上存在**：用于版本发布和CI触发
- ✅ **强制覆盖旧tag**：删除GitHub上的旧tag后重新创建，确保CI触发
- ✅ **参数格式**：`.\release.ps1 push <version> <message>`

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
✅ **Submodule支持**：正确处理submodule引用，CI能正确初始化

## 注意事项

1. **无需初始化**：直接使用`push`命令即可，无需先init
2. **只在main分支开发**：不要在其他分支开发
3. **本地无release分支**：使用临时orphan分支，用完即删
4. **推送失败**：检查网络连接和GitHub权限
5. **重复发布**：可以重复发布同一版本号，会强制覆盖GitHub上的tag
6. **本地无tag**：本地不保留tag，tag只在GitHub上存在
7. **文件清理**：使用`--cached`清空索引，保留工作目录文件
8. **强制推送**：使用`--force`推送到GitHub，确保远程完全同步本地状态
9. **Submodule处理**：脚本自动处理submodule引用，无需手动干预

## 常见问题

### Q: 为什么GitHub上还有本地已删除的文件？

A: 已修复！现在的release.ps1使用`git rm -rf . --cached`清空索引，保留工作目录文件（包括.gitignore），确保.gitignore规则生效，删除的文件不会残留在GitHub。

### Q: 为什么本地main分支和origin/main分支分叉了？

A: 这是正常的！
- **本地main**：保留完整开发历史（便于开发、调试、回溯）
- **远程origin/main**：干净的发布历史（便于用户查看）
- 两者用途不同，不需要同步

### Q: 未修改的文件为什么显示旧的tag信息？

A: 这是git的正常行为。Git只追踪文件的修改，未修改的文件会保留之前的提交信息，但文件内容是最新的，不影响使用。

### Q: 为什么CI install失败，提示找不到submodule文件？

A: 已修复！之前的脚本使用`git add submodule路径`会添加目录内容而非gitlink引用。现在使用`git update-index --cacheinfo 160000`正确添加submodule引用，GitHub CI的`actions/checkout@v4` with `submodules: true`能正确初始化submodule。

### Q: 本地有release分支吗？

A: 没有。脚本使用临时orphan分支（`release-temp-随机数`），推送完成后立即删除，本地不保留release分支。
