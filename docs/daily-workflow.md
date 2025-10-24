# 日常协作工作流程指南

## 快速开始指南

### 对于协作者（朋友们）

#### 1. 第一次设置

```bash
# 克隆仓库
git clone https://github.com/leafmove/LeafKnow.git
cd LeafKnow

# 设置个人信息（只需设置一次）
git config user.name "你的GitHub用户名"
git config user.email "你的GitHub邮箱"

# 查看所有分支
git branch -a
```

#### 2. 开始新功能开发

```bash
# 切换到主分支并获取最新代码
git checkout main
git pull origin main

# 创建你的功能分支（推荐格式：你的名字/功能描述）
git checkout -b zhangsan/user-login-feature

# 在这个分支上开发...
# 编写代码，测试，提交
git add .
git commit -m "feat: 添加用户登录功能"

# 推送你的分支到GitHub
git push origin zhangsan/user-login-feature
```

#### 3. 日常开发和编译

bun run dev
bun run build
bun tauri dev
bun tauri build

#### 4. 创建Pull Request

1. 访问：[https://github.com/leafmove/LeafKnow](https://github.com/leafmove/LeafKnow)
2. 你会看到一个黄色的横幅，点击"Compare & pull request"
3. 填写PR标题和描述：
   - 标题：简要说明你做了什么
   - 描述：详细说明功能实现、测试情况等
4. 点击"Create pull request"

#### 5. 等待审查和修改

- 项目负责人会审查你的代码
- 如果需要修改，在PR中会看到评论
- 修改代码后，再次推送到你的分支：

  ```bash
  # 修改代码
  git add .
  git commit -m "fix: 修复登录验证问题"
  git push origin zhangsan/user-login-feature
  ```

- PR会自动更新

### 对于项目负责人（你）

#### 1. 审查Pull Request

1. 访问GitHub仓库的"Pull requests"页面
2. 点击进入具体的PR
3. 检查：
   - 代码质量和规范性
   - 功能是否正确实现
   - 是否有潜在问题
4. 可以：
   - 留下评论或建议
   - 直接修改代码
   - 请求更改
   - 批准PR

#### 2. 合并Pull Request

1. 审查通过后，在PR页面点击"Merge pull request"
2. 选择合并方式：
   - **Create a merge commit**（推荐）：保留完整历史
   - **Squash and merge**：将多个提交合并为一个
   - **Rebase and merge**：变基合并
3. 点击"Confirm merge"

#### 3. 清理分支

```bash
# 删除已合并的分支（可选）
git branch -d zhangsan/user-login-feature
git push origin --delete zhangsan/user-login-feature
```

## 常用Git命令参考

### 基本操作

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline

# 查看分支
git branch -a

# 切换分支
git checkout 分支名
```

### 提交和推送

```bash
# 添加所有修改
git add .

# 添加特定文件
git add 文件名

# 提交（写清楚提交信息）
git commit -m "提交类型: 简要描述"

# 推送到远程仓库
git push origin 分支名
```

### 与远程仓库同步

```bash
# 获取远程仓库更新
git fetch origin

# 拉取并合并
git pull origin main

# 查看远程仓库
git remote -v
```

## 提交信息规范

使用以下前缀来描述提交类型：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建或辅助工具的变动

## 问题排查

### 冲突解决

```bash
# 如果pull时遇到冲突
git pull origin main
# 解决冲突文件中的问题
git add .
git commit -m "解决合并冲突"
git push
```

### 撤销操作

```bash
# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销工作区的修改
git checkout -- 文件名
```

## 最佳实践

1. **经常同步主分支**：开发前先拉取最新代码
2. **小步提交**：一个功能分成多个小提交，便于审查
3. **清晰的提交信息**：让其他人容易理解你的修改
4. **及时沟通**：遇到问题及时在PR中讨论
5. **测试代码**：确保提交的代码经过测试
