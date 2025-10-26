# Phase 1 完成后的行动计划

## 🎉 当前状态

### ✅ MLX-VLM Phase 1 已完成
- 后端下载 API + Bridge Events
- 优先级队列 + 懒加载
- Splash 模型下载集成
- 权限延后优化
- **测试结果**：首次下载流程完全正常 ✅

### 📊 测试场景覆盖
- ✅ 删除模型文件（首次下载）
- ✅ 清理 Python 环境（uv sync）
- ✅ 清理缓存（全新安装）
- ✅ 良好网络条件（HuggingFace 直连）

---

## 🎯 三个优化方向

### 方向 A：完成 MLX-VLM 功能闭环
**目标**：将 MLX-VLM 集成打磨到生产级别

**任务清单**：
1. **智能卸载逻辑**（2小时）
   - 实现 `check_and_unload_if_unused()`
   - 查询 CapabilityAssignment 表
   - 4个能力全部切换时自动卸载
   - 在能力分配 API 添加钩子

2. **端到端测试**（1小时）
   - 下载失败 + 镜像切换测试
   - 优先级队列测试（HIGH vs LOW）
   - 智能卸载测试
   - 懒加载 + 空闲超时测试

3. **删除旧代码**（30分钟）
   - models_builtin.py 旧子进程管理代码
   - models_api.py 废弃端点
   - UI 旧组件（useBuiltinModels, BuiltinModelsTab）

**总时间**：3.5小时  
**收益**：MLX-VLM 功能完整，可投入生产

---

### 方向 B：优化启动体验
**目标**：将首次启动白屏时间从 3秒降低到 <500ms

**任务清单**：
1. **EarlySplash 实现**（30分钟）
   - 创建轻量级 EarlySplash 组件
   - 修改 main.tsx 立即渲染
   - 后台完成初始化后平滑切换

2. **清理调试日志**（15分钟）
   - 移除 Splash 中的 console.log
   - 保留关键错误日志
   - 优化日志格式

3. **日志迁移到 RAG 观察窗**（1小时）
   - 将 api-log 事件显示在主界面
   - 与 RAG 检索事件并列显示
   - 为后续多页签设计做准备

**总时间**：1.75小时  
**收益**：用户体验显著提升（白屏时间降低 83%）

---

### 方向 C：增强 RAG 数据观察窗
**目标**：打造强大的数据观察和调试工具

**任务清单**：
1. **多页签架构**（1小时）
   - RAG 检索页签（已有）
   - API 日志页签（新增）
   - 模型状态页签（新增）
   - 向量化进度页签（已有部分）

2. **API 日志集成**（1小时）
   - 监听 api-log 和 api-error 事件
   - 按时间倒序显示
   - 支持日志级别过滤（INFO/WARN/ERROR）
   - 支持关键词搜索

3. **基础过滤功能**（1小时）
   - 时间范围筛选（最近5分钟/1小时/全部）
   - 事件类型过滤（多选）
   - 关键词高亮
   - 清空历史按钮

**总时间**：3小时  
**收益**：强大的调试能力，用户对数据更有掌控感

---

## 🚀 推荐实施顺序

### 第一阶段（今天，2小时）✨
```
1. 方向 B - EarlySplash 实现（30分钟）
2. 方向 B - 清理调试日志（15分钟）
3. 方向 A - 智能卸载逻辑（2小时）
```

**理由**：
- EarlySplash 快速见效，用户体验立即提升
- 清理调试日志，让代码更干净
- 智能卸载是 MLX-VLM 的核心功能

**当天成果**：
- ✅ 白屏时间降低 83%
- ✅ 代码更整洁
- ✅ MLX-VLM 智能管理内存

---

### 第二阶段（明天上午，1.5小时）✨
```
1. 方向 A - 端到端测试（1小时）
2. 方向 A - 删除旧代码（30分钟）
```

**理由**：
- 完整测试确保功能稳定
- 删除旧代码减少维护负担

**里程碑**：🎉 **MLX-VLM 集成完全完成**

---

### 第三阶段（明天下午/后天，4小时）✨
```
1. 方向 B - 日志迁移到 RAG 观察窗（1小时）
2. 方向 C - 多页签架构（1小时）
3. 方向 C - API 日志集成（1小时）
4. 方向 C - 基础过滤功能（1小时）
```

**理由**：
- RAG 观察窗是你的独特设计
- 多页签架构为未来扩展打基础
- 强大的调试能力

**里程碑**：🎉 **数据观察窗完整实现**

---

## 📝 详细实施指南

### 今天第一步：EarlySplash（30分钟）

#### 1. 创建 EarlySplash 组件
```bash
# 创建新文件
touch tauri-app/src/EarlySplash.tsx
```

#### 2. 实现代码（见 EARLY_SPLASH_OPTIMIZATION.md）

#### 3. 测试验证
```bash
cd tauri-app
./dev.sh
# 观察：白屏时间应该 <500ms
```

---

### 今天第二步：清理调试日志（15分钟）

#### 要清理的文件
- `tauri-app/src/splash.tsx`
  - 移除所有 `console.log('[Splash] ...')`
  - 保留错误日志（`console.error`）

#### 命令
```bash
# 查找所有调试日志
grep -n "console.log.*Splash" tauri-app/src/splash.tsx

# 逐个删除或注释掉
```

---

### 今天第三步：智能卸载逻辑（2小时）

#### 1. 数据库查询方法
```python
# api/models_mgr.py
async def get_builtin_vlm_assignments(db: AsyncSession) -> List[CapabilityAssignment]:
    """获取内置VLM模型的4个能力分配"""
    result = await db.execute(
        select(CapabilityAssignment).where(
            and_(
                CapabilityAssignment.provider_type == 'builtin',
                CapabilityAssignment.capability.in_([
                    'VISION', 'TEXT', 'STRUCTURED_OUTPUT', 'TOOL_USE'
                ])
            )
        )
    )
    return result.scalars().all()
```

#### 2. 卸载检查方法
```python
# api/models_mgr.py (MLXVLMModelManager)
async def check_and_unload_if_unused(self, db: AsyncSession):
    """检查内置VLM是否被使用，如果全部切换到其他模型则自动卸载"""
    assignments = await get_builtin_vlm_assignments(db)
    
    # 检查是否有任何能力仍在使用内置VLM
    for assignment in assignments:
        if assignment.model_id == 'mlx-vlm-qwen2-vl-2b':
            logger.info(f"内置VLM仍被 {assignment.capability} 能力使用，保持加载")
            return
    
    # 全部切换到其他模型，可以卸载
    logger.info("内置VLM所有能力均已切换，自动卸载模型")
    await self.unload_model()
```

#### 3. 在能力分配 API 添加钩子
```python
# api/models_api.py
@router.post("/capabilities/{capability}/assign")
async def assign_capability(...):
    # ... 原有逻辑 ...
    
    # 分配成功后检查是否需要卸载内置VLM
    from api.models_mgr import mlx_vlm_manager
    await mlx_vlm_manager.check_and_unload_if_unused(db)
    
    return {...}
```

---

## 🧪 测试检查清单

### MLX-VLM 完整测试

#### Test 1: 首次下载（已通过 ✅）
```bash
rm -rf ~/Library/Application\ Support/knowledge-focus.huozhong.in/mlx-vlm
./dev.sh
```

#### Test 2: 下载失败 + 镜像切换
```bash
# 模拟 HuggingFace 超时
# 修改 models_builtin.py 降低超时时间
# 观察：应该显示镜像选择 + 重试按钮
```

#### Test 3: 优先级队列
```bash
# 终端1：发送高优先级请求（聊天）
curl -X POST http://localhost:60315/v1/chat/completions ...

# 终端2：发送低优先级请求（批量任务）
curl -X POST http://localhost:60315/models/builtin/inference ...

# 观察：高优先级应该先处理
```

#### Test 4: 智能卸载
```bash
# 1. 打开 AI Models 设置
# 2. 将 VISION/TEXT/STRUCTURED_OUTPUT/TOOL_USE 全部切换到其他模型
# 3. 观察日志：应该看到 "自动卸载模型" 消息
# 4. 查看内存：应该释放 ~4GB
```

#### Test 5: 懒加载 + 空闲超时
```bash
# 1. 启动 App（模型未加载）
# 2. 发送一条带图片的消息（触发加载）
# 3. 等待 60 秒不使用
# 4. 观察日志：应该看到 "空闲超时，卸载模型" 消息
```

---

## 📊 预期成果对比

| 指标 | Phase 0 | Phase 1 完成后 |
|------|---------|---------------|
| 首次启动白屏时间 | 3000ms | <500ms ⬆️ 83% |
| 模型下载流程 | 手动/复杂 | 自动/流畅 ✅ |
| 内存管理 | 手动 | 智能卸载 ✅ |
| 调试能力 | 终端日志 | 可视化观察窗 ✅ |
| 代码质量 | 旧代码混杂 | 整洁 ✅ |
| 用户体验 | 6/10 | 9/10 ⬆️ 50% |

---

## 💡 后续可选方向

### 短期（本周）
- [ ] 添加模型下载取消功能
- [ ] 优化下载进度显示（显示速度、预计时间）
- [ ] 添加离线模式（跳过模型下载）

### 中期（下周）
- [ ] 支持其他内置模型（选择不同的 VLM）
- [ ] 模型版本管理（检查更新）
- [ ] 多模型并行加载

### 长期（未来）
- [ ] 模型热切换（无需卸载）
- [ ] 模型性能监控仪表盘
- [ ] A/B 测试不同模型效果

---

## 🎯 立即开始

**现在就可以开始第一步：EarlySplash 实现！**

我可以帮你：
1. 创建 `EarlySplash.tsx` 文件
2. 修改 `main.tsx` 实现立即渲染
3. 测试验证白屏时间优化

**你准备好了吗？** 🚀
