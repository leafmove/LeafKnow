# LeafKnow 前端启动指南

## 🎯 项目概览

LeafKnow前端是一个基于以下技术栈构建的桌面应用：
- **React 19.1.0** - 现代化UI框架
- **TypeScript** - 类型安全的JavaScript
- **Vite 7.1.12** - 快速构建工具
- **Tauri 2.x** - 跨平台桌面应用框架
- **Tailwind CSS** - 实用优先的CSS框架

## ✅ 当前状态

### 已完成：
- ✅ 依赖安装成功 (478个包)
- ✅ Vite开发服务器启动成功
- ✅ 运行在 http://localhost:1420/

### ⚠️ 需要解决的问题：
- ❌ Tauri需要Rust/Cargo (未安装)
- ⚠️ Node.js版本警告 (20.18.1 vs 推荐20.19+)

## 🚀 启动方式

### 方式1: Web开发模式 (当前可用)

**已成功启动！** 访问：http://localhost:1420/

```bash
cd leaf-know
npm run dev
```

**特点**：
- ✅ 可以立即使用
- ✅ 支持热重载
- ✅ 在浏览器中运行
- ⚠️ 无法访问Tauri原生功能

### 方式2: 桌面应用模式 (需要Rust)

**需要先安装Rust**：
```bash
# Windows (推荐)
winget install Rustlang.Rust.MSVC

# 验证安装
cargo --version
```

**启动命令**：
```bash
cd leaf-know
npm run tauri dev
```

**特点**：
- ✅ 原生桌面应用
- ✅ 可访问文件系统、通知等
- ✅ 完整的应用体验
- ❌ 需要Rust环境

## 🎨 项目技术特性

### UI组件库
- **Radix UI**: 高质量的React组件
- **Lucide React**: 现代图标库
- **Sonner**: 优雅的通知组件
- **React Syntax Highlighter**: 代码高亮

### 功能特性
- **AI SDK集成**: OpenAI等AI服务
- **状态管理**: Zustand
- **路由**: React Router
- **主题**: 支持暗色/亮色模式
- **响应式设计**: 移动端适配

### 开发工具
- **TypeScript**: 类型安全
- **ESLint + Prettier**: 代码规范
- **Vite**: 快速热重载
- **Tailwind CSS**: 样式开发

## 🛠️ 开发工作流

### 1. 环境检查
```bash
# 检查Node.js版本
node --version  # 推荐: 20.19+

# 检查npm版本
npm --version   # 当前: 11.6.2 ✅
```

### 2. 依赖管理
```bash
# 安装依赖
npm install

# 添加新依赖
npm add <package-name>

# 添加开发依赖
npm add -D <package-name>
```

### 3. 开发命令
```bash
# 启动Web开发服务器
npm run dev

# 构建项目
npm run build

# 预览构建结果
npm run preview

# 启动Tauri开发模式
npm run tauri dev
```

### 4. 构建桌面应用
```bash
# 开发构建
npm run tauri build

# 生产构建
npm run tauri build --release
```

## 📁 项目结构

```
leaf-know/
├── src/                    # React源代码
│   ├── components/         # 可复用组件
│   │   ├── ui/            # 基础UI组件
│   │   └── ai-elements/   # AI相关组件
│   ├── hooks/             # 自定义Hooks
│   ├── lib/               # 工具库
│   └── App.tsx            # 主应用组件
├── src-tauri/             # Tauri后端(Rust)
├── public/                # 静态资源
├── index.html             # HTML模板
├── package.json           # 项目配置
├── vite.config.ts         # Vite配置
└── tailwind.config.js     # Tailwind配置
```

## 🔧 配置说明

### Vite配置
- **端口**: 1420 (固定端口，Tauri要求)
- **别名**: @ 指向 src 目录
- **插件**: React + Tailwind CSS
- **HMR**: 支持热重载

### Tauri配置
- **应用ID**: com.leafmove.leaf-know
- **窗口**: 可调整大小的桌面窗口
- **权限**: 文件系统、网络、通知等

## 🐛 常见问题解决

### 1. Node.js版本警告
```bash
# 当前版本可用，但建议升级
winget install OpenJS.NodeJS

# 或使用nvm管理版本
nvm install 20.19.0
nvm use 20.19.0
```

### 2. Tauri启动失败
```bash
# 安装Rust
winget install Rustlang.Rust.MSVC

# 验证安装
cargo --version
rustc --version
```

### 3. 端口占用
```bash
# 查看端口占用
netstat -ano | findstr :1420

# 结束进程
taskkill /PID <进程ID> /F
```

### 4. 依赖安装失败
```bash
# 清理缓存重新安装
rm -rf node_modules package-lock.json
npm install
```

## 🎯 下一步开发

### 即可开始：
1. **访问**: http://localhost:1420/
2. **编辑代码**: 修改src目录下的文件
3. **查看变化**: 浏览器自动刷新

### 完整体验：
1. **安装Rust**: 运行桌面应用版本
2. **连接API**: 启动后端服务(需要Python 3.10+)
3. **完整功能**: AI对话、文档管理等

## 📞 技术支持

如遇到问题：
1. 检查控制台错误信息
2. 确认依赖安装完整
3. 查看网络连接状态
4. 参考官方文档：
   - [React](https://react.dev/)
   - [Vite](https://vite.dev/)
   - [Tauri](https://tauri.app/)
   - [Tailwind CSS](https://tailwindcss.com/)

---

**状态**: ✅ 前端开发服务器已成功启动，可以通过浏览器访问开发版本！