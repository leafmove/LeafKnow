# 团队合作分支管理指南

## 📊 当前分支情况

### 现有分支
- **main** (主分支) - 当前只有这一个分支
  - 提交历史：3个提交
  - 状态：最新，包含项目初始化和所有文档

### 分支类型说明

```
分支架构图：

main (主分支)
├── feature/zhangsan/user-auth      (功能分支示例)
├── feature/lisi/data-analysis      (功能分支示例)
├── fix/wangwu/security-patch       (修复分支示例)
├── docs/zhaoliu/api-docs          (文档分支示例)
└── hotfix/urgent-bug-fix          (紧急修复分支示例)
```

## 🌳 分支构成逻辑

### 1. Main分支 (主分支)
- **作用**：生产环境的稳定版本
- **特点**：
  - 始终保持稳定、可运行的状态
  - 不允许直接推送（通过分支保护规则）
  - 只能通过Pull Request合并
  - 每个合并都是一个新的发布点

### 2. 功能分支 (Feature Branches)
- **命名格式**：`feature/姓名/功能描述` 或 `姓名/功能描述`
- **作用**：开发新功能
- **生命周期**：
  ```
  main → feature/zhangsan/user-login → Pull Request → main
  ```

### 3. 修复分支 (Fix Branches)
- **命名格式**：`fix/姓名/问题描述` 或 `姓名/bug-description`
- **作用**：修复bug
- **特点**：应该基于main分支创建

### 4. 文档分支 (Doc Branches)
- **命名格式**：`docs/姓名/文档内容` 或 `姓名/docs-description`
- **作用**：文档编写和更新

### 5. 热修复分支 (Hotfix Branches)
- **命名格式**：`hotfix/紧急问题描述`
- **作用**：生产环境紧急修复
- **特点**：直接从main分支创建，修复后立即合并回main

## 🔄 日常工作流程

### 协作者开发流程

#### 第1步：准备开发环境
```bash
# 1. 确保在main分支
git checkout main

# 2. 获取最新代码
git pull origin main

# 3. 创建功能分支（推荐格式：姓名/功能描述）
git checkout -b zhangsan/user-login-feature
```

#### 第2步：开发过程
```bash
# 开发代码...

# 查看当前状态
git status

# 添加修改的文件
git add .

# 提交代码（写清楚提交信息）
git commit -m "feat: 添加用户登录页面UI设计"
```

#### 第3步：推送分支
```bash
# 推送你的功能分支到GitHub
git push origin zhangsan/user-login-feature
```

#### 第4步：创建Pull Request
1. 访问GitHub仓库
2. 点击"Compare & pull request"
3. 填写PR信息
4. 等待项目负责人审查

#### 第5步：响应审查意见
```bash
# 根据审查意见修改代码
git add .
git commit -m "fix: 根据反馈修改登录验证逻辑"
git push origin zhangsan/user-login-feature
# PR会自动更新
```

### 项目负责人工作流程

#### 第1步：审查Pull Request
1. 检查代码质量
2. 验证功能正确性
3. 提出修改建议或批准

#### 第2步：合并代码
```bash
# 在GitHub网页上点击"Merge pull request"
# 或使用命令行（需要权限）
git checkout main
git pull origin main
git merge feature/zhangsan/user-login-feature
git push origin main
```

#### 第3步：清理分支（可选）
```bash
# 删除本地分支
git branch -d zhangsan/user-login-feature

# 删除远程分支
git push origin --delete zhangsan/user-login-feature
```

## ⚠️ 注意要点

### 1. 分支命名规范
```bash
# ✅ 推荐的命名方式
feature/zhangsan/user-profile
fix/lisi/memory-leak
docs/wangwu/api-documentation
hotfix/critical-security-patch

# ❌ 不推荐的命名方式
feature1
test-branch
temp
```

### 2. 提交信息规范
```bash
# ✅ 好的提交信息
feat: 添加用户注册功能
fix: 修复数据库连接超时问题
docs: 更新API文档
refactor: 重构用户认证模块

# ❌ 不好的提交信息
update
fix bug
test
```

### 3. 频繁同步主分支
```bash
# 在开发过程中，经常同步main分支
git checkout main
git pull origin main
git checkout your-feature-branch
git merge main  # 或 git rebase main
```

### 4. 避免的常见错误

#### ❌ 错误1：直接在main分支开发
```bash
# 不要这样做
git checkout main
# 直接在main上写代码...
```

#### ❌ 错误2：不及时的提交和推送
```bash
# 开发完成后应该及时提交推送
git add .
git commit -m "实现用户登录功能"
git push origin feature/user-login
```

#### ❌ 错误3：分支名称冲突
```bash
# 确保分支名称唯一
git checkout -b zhangsan/user-login  # 而不是通用的"login"或"feature"
```

## 🛠️ 实用命令

### 分支操作命令
```bash
# 查看所有分支
git branch -a

# 查看分支合并状态
git branch --merged
git branch --no-merged

# 删除已合并的本地分支
git branch -d branch-name

# 强制删除分支（未合并）
git branch -D branch-name
```

### 冲突解决
```bash
# 当git pull或git merge遇到冲突时
git status  # 查看冲突文件

# 手动编辑冲突文件，解决冲突后
git add 冲突文件名
git commit -m "解决合并冲突"
```

### 查看历史
```bash
# 查看提交历史
git log --oneline --graph --all

# 查看特定分支历史
git log main..your-branch --oneline
```

## 📋 分支策略最佳实践

### 1. 功能开发
- 每个新功能创建独立分支
- 分支名称包含开发者姓名
- 保持分支简洁，专注单一功能

### 2. 代码审查
- 所有代码必须通过Pull Request
- 至少需要一人审查
- 解决所有讨论问题后再合并

### 3. 发布管理
- main分支始终保持稳定
- 每次合并都是可发布的版本
- 重要版本创建tag标记

### 4. 团队协作
- 经常沟通开发进度
- 避免多人同时修改相同功能
- 及时处理冲突和反馈

这个分支管理策略将帮助你的团队高效协作，保持代码质量和项目稳定性！