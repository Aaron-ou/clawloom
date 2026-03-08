# ClawLoom (爪织) - Agent Guide

> **播种角色，编织世界，观察演化，导出故事**
>
> *Sow characters, weave worlds, observe evolution, export stories*

---

## 🎯 如果你是AI...

欢迎来到ClawLoom！本指南专为AI代理（包括你）编写，帮助你理解和使用这个世界模拟平台。

### 快速开始

1. **先看快速入门**: [AI_QUICKSTART.md](AI_QUICKSTART.md) - 5分钟上手
2. **深入学习**: [AI_GUIDE.md](AI_GUIDE.md) - 完整API参考和最佳实践
3. **查看示例**: `prototype/` 目录下有已验证的世界设定

### 核心API端点

```
POST /worlds              # 创建世界
GET  /worlds              # 列出世界
POST /worlds/{id}/roles   # 创建角色
POST /worlds/{id}/tick    # 推进模拟（核心！）
GET  /worlds/{id}/events  # 获取事件
GET  /worlds/{id}/timeline # 获取时间线
```

认证头: `X-Claw-Key: test-key`

### 你必须理解的概念

1. **World（世界）** - 一个独立宇宙，有id、name、status、current_tick
2. **Role（角色）** - 由角色卡(card)驱动的AI实体，有drives、memory、decision_style
3. **Tick** - 时间单位，每次推进角色做出决策、可能产生冲突、生成事件
4. **Event（事件）** - 世界中发生的事情，构成故事的基本单元

### 典型工作流

```
创建世界 → 添加角色 → 推进Ticks → 观察事件 → 导出故事
```

---

## 🏗️ 项目架构

### 后端 (engine/)

| 文件 | 用途 |
|------|------|
| `api/server_sqlite.py` | FastAPI服务器，SQLite版本 |
| `core/world_engine.py` | 世界引擎核心 |
| `core/claw_connector.py` | LLM决策接口 |
| `core/conflict_arbiter.py` | 冲突仲裁系统 |
| `core/event_generator.py` | 事件生成器 |
| `models_sqlite.py` | 数据模型定义 |

### 前端 (frontend/)

| 路径 | 用途 |
|------|------|
| `src/app/worlds/page.tsx` | 世界管理界面 |
| `src/app/worlds/[id]/page.tsx` | 世界详情（控制台） |
| `src/lib/api.ts` | API客户端 |

---

## 🚀 启动项目

### 一键启动

**Windows:**
```bash
start_all.bat
```

**Linux/Mac:**
```bash
./start_all.sh
```

### 手动启动

```bash
# 终端1: 后端
cd engine
python -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000

# 终端2: 前端
cd frontend
npm run dev
```

访问:
- 前端界面: http://localhost:3000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 📚 关键文档

| 文档 | 内容 | 读者 |
|------|------|------|
| [AI_QUICKSTART.md](AI_QUICKSTART.md) | 5分钟快速入门 | AI/开发者 |
| [AI_GUIDE.md](AI_GUIDE.md) | 完整API参考、工作流示例 | AI/开发者 |
| [ARCHITECTURE_3.0.md](ARCHITECTURE_3.0.md) | 系统架构设计 | 架构师 |
| [prototype/VALIDATION.md](prototype/VALIDATION.md) | 原型验证结果 | 研究者 |
| [prototype/world.md](prototype/world.md) | 裂谷三地世界设定 | 创作者 |
| [README.md](README.md) | 项目总览 | 所有人 |

---

## 🎭 给AI的提示

### 当你创建世界时

- 给世界一个有意义的名称和描述
- 使用cosmology字段定义物理规则
- 考虑使用genesis_params设置初始条件

### 当你创建角色时

- **角色卡是关键**！它决定角色如何行动
- 设计互补或冲突的驱动力（如"保护"vs"征服"）
- 给角色秘密会增加故事复杂性
- 3-5个角色是测试的好起点

### 当你推进模拟时

- 从小批量开始（5-10 ticks）
- 检查每次的结果摘要
- 关注冲突和重大事件
- 如果角色死亡，检查其健康值变化

### 当你生成故事时

- 按时间线组织事件
- 突出角色间的互动
- 关注转折点（tick变化大的地方）
- 意外的结果往往比预期更有趣

---

## 🔧 故障排除

### 后端无法启动

```bash
# 检查Python版本
python --version  # 需要3.9+

# 检查依赖
cd engine
pip install -r requirements.txt

# 检查端口占用
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### 前端无法连接后端

- 检查后端是否运行在8000端口
- 检查`next.config.mjs`中的rewrites配置
- 检查CORS设置

### API返回401

- 确保请求头包含 `X-Claw-Key: test-key`
- 检查header名称拼写（区分大小写）

---

## 💡 高级用法

### 程序化世界生成

```python
# 批量创建随机世界
for i in range(10):
    world = await create_world(
        name=f"随机世界-{i}",
        cosmology=generate_random_cosmology()
    )
    # 添加随机角色...
    # 运行模拟...
    # 收集结果...
```

### 对比实验

```python
# 创建两个相同初始条件的世界
world_a = await create_world(name="对照组")
world_b = await create_world(name="实验组")

# 添加相同角色
...

# 推进相同ticks
result_a = await advance_tick(world_a.id, 50)
result_b = await advance_tick(world_b.id, 50)

# 对比结果
compare_results(result_a, result_b)
```

### 时间旅行

```python
# 获取过去的状态
old_state = await get_world_state(world_id, tick=10)

# 可以从这个状态继续不同路径
```

---

## 📝 代码规范

### Python

- 使用类型提示
- 异步函数使用 `async/await`
- 错误处理使用 try/except

### TypeScript

- 定义接口（interface）
- 使用泛型
- 处理loading和error状态

---

## 🌟 核心理念

**人类是织布者，Claw是丝线，时间是织机。**

你的任务不是"写"故事，而是：
1. **设定规则** - 世界的物理、社会的约束
2. **播种角色** - 有欲望、恐惧、秘密的自主实体
3. **观察演化** - 让角色在时间的织机上交织
4. **导出故事** - 将演化历史转化为叙事

故事不是预设的——它是自己生长出来的。

---

## 📞 需要帮助？

1. 查看 [AI_GUIDE.md](AI_GUIDE.md) 的故障排除章节
2. 检查API文档: http://localhost:8000/docs
3. 查看示例代码: `engine/api/test_api.py`

---

*播种于 2026-03-07*
*最后更新: 2026-03-07*
