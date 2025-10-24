# 分支保护规则设置指南

## 为什么要设置分支保护规则？

分支保护规则可以：
- 防止直接推送到主分支
- 确保所有代码都经过Pull Request审查
- 要求代码审查通过后才能合并
- 保持主分支的稳定性

## 设置步骤

### 1. 进入分支设置页面
- 访问：https://github.com/leafmove/LeafKnow
- 点击 "Settings" 选项卡
- 在左侧菜单中点击 "Branches"

### 2. 添加分支保护规则
- 在 "Branch protection rules" 部分，点击 "Add rule"

### 3. 配置保护规则
按照以下设置进行配置：

#### 基本设置：
- **Branch name pattern**: 输入 `main` （保护主分支）
- **Require pull request reviews before merging** ✓（勾选）
  - **Number of required reviewers**: 选择 1（至少需要1人审查）
- **Require status checks to pass before merging** □（暂时不勾选，等有CI/CD再设置）
- **Require branches to be up to date before merging** □（暂时不勾选）

#### 其他设置：
- **Do not allow bypassing the above settings** □（暂时不勾选）
- **Require conversation resolution before merging** ✓（推荐勾选，要求解决所有讨论）
- **Require signed commits** □（暂时不勾选）
- **Restrict who can dismiss pull request reviews** □（暂时不勾选）

### 4. 保存设置
- 点击 "Create" 或 "Save changes" 保存规则

## 设置完成后有什么效果？

1. **禁止直接推送**
   - 任何人（包括你自己）都不能直接推送到main分支
   - 必须通过Pull Request合并代码

2. **强制代码审查**
   - 每个Pull Request至少需要1个审查者批准
   - 审查者可以提出修改建议

3. **讨论解决机制**
   - 如果勾选了"Require conversation resolution"，所有讨论必须解决才能合并

## 日常工作流程

### 协作者工作流程：
1. 从main分支创建功能分支
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/新功能名称
   ```

2. 在功能分支上开发
   ```bash
   # 进行代码修改
   git add .
   git commit -m "添加新功能"
   git push origin feature/新功能名称
   ```

3. 创建Pull Request
   - 在GitHub上点击"Compare & pull request"
   - 填写PR描述
   - 等待项目负责人的审查

### 项目负责人工作流程：
1. **审查Pull Request**
   - 检查代码质量和功能正确性
   - 可以提出修改建议或要求修改
   - 批准或拒绝PR

2. **合并代码**
   - 审查通过后，可以点击"Merge pull request"
   - 选择合并方式（推荐"Create a merge commit"）

## 紧急情况处理

如果遇到紧急情况需要直接修改main分支：
1. 可以暂时关闭分支保护规则
2. 进行紧急修复
3. 重新开启保护规则
4. 考虑设置更灵活的规则以平衡安全性和便利性