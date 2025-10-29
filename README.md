# LeafKnow

## 项目简介
LeafKnow是一个知识管理与学习平台项目。

## 项目结构
```
LeafKnow/
├── docs/           # 项目文档
├── src/            # 源代码
├── tests/          # 测试文件
├── .gitignore      # Git忽略文件
├── README.md       # 项目说明
└── CLAUDE.md       # Claude Code 指导文档
```

## 开发团队
- 项目负责人：你
- 维护者：你的朋友们

## 协作流程
1. 每个维护者在自己的分支上开发
2. 通过Pull Request向主分支提交代码
3. 由项目负责人进行代码审查和合并

## 📚 重要文档

### 协作者必读
- [📖 日常协作工作流程](./docs/daily-workflow.md) - 协作者的完整开发指南
- [👥 协作者邀请指南](./docs/collaboration-guide.md) - 如何邀请朋友加入项目
- [🔒 分支保护设置](./docs/branch-protection-setup.md) - 主分支保护规则配置

### 项目文档
- [📁 项目结构说明](./docs/project-structure.md) - 项目目录和文件说明
- [🌳 分支管理指南](./docs/branch-management-guide.md) - 团队分支策略和操作流程
- [🤖 CLAUDE.md](./CLAUDE.md) - Claude Code AI助手工作指导

## 🚀 快速开始

### 📖 如何启动项目？
详细的启动指南请参考：[🔧 项目启动指南](./docs/startup-guide.md)

### 对于协作者：
1. 克隆仓库：`git clone https://github.com/leafmove/LeafKnow.git`
2. 阅读启动指南：[项目启动指南](./docs/startup-guide.md)
3. 阅读协作文档：[日常协作工作流程](./docs/daily-workflow.md)
4. 创建你的功能分支开始开发！

### ⚡ 快速启动命令
```bash
# 1. 启动API后端 (终端1)
cd core
uv run main.py --port 60000 --host 127.0.0.1

# 2. 启动前端应用 (终端2)
cd leaf-know
bun tauri dev
```

### 对于项目负责人：
1. 邀请协作者：参考[协作者邀请指南](./docs/collaboration-guide.md)
2. 设置分支保护：参考[分支保护设置](./docs/branch-protection-setup.md)
3. 审查和合并Pull Request

## 许可证
待添加