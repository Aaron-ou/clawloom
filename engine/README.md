# ClawLoom Engine

ClawLoom 爪织引擎 - Python实现

## 快速开始

### 启动服务器

```bash
./start_server.sh
```

访问 http://localhost:8000/docs 查看 API 文档。

### 运行测试

```bash
./run_tests.sh
```

## 项目结构

```
engine/
├── api/
│   ├── server.py      # FastAPI 服务器
│   ├── test_api.py    # API 测试
│   └── README.md      # API 文档
├── models/            # 数据模型
├── core/              # 世界引擎核心
├── start_server.sh    # 启动脚本
└── run_tests.sh       # 测试脚本
```

## API 概览

- `POST /worlds` - 创建世界
- `POST /worlds/{id}/roles` - 创建角色
- `POST /worlds/{id}/tick` - 推进模拟
- `GET /worlds/{id}/state` - 获取世界状态

详见 `api/README.md`

## 架构

```
engine/
├── models/           # 数据模型 (SQLAlchemy + Pydantic)
│   └── __init__.py
├── core/            # 核心引擎
│   └── world_engine.py
├── connectors/      # Claw连接器 (待实现)
├── arbiters/        # 冲突仲裁器扩展 (待实现)
├── generators/      # 事件生成器扩展 (待实现)
└── main.py          # 入口点
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

```bash
# 创建PostgreSQL数据库
createdb clawloom

# 或设置环境变量
export DATABASE_URL="postgresql://user:password@localhost:5432/clawloom"
```

### 3. 运行演示

```bash
python main.py
```

## 核心概念

### 世界 (World)

一个独立的宇宙，包含完整的物理规则、历史时间线和所有角色。

### 角色 (Role)

世界中的自主实体，通过Claw（LLM）驱动决策。

### Tick

世界时间的基本单位。每个tick：
1. 收集所有活跃角色的决策
2. 检测决策间的冲突
3. 仲裁冲突结果
4. 生成事件
5. 更新角色记忆
6. 保存世界快照

### 冲突仲裁

自动检测角色间的冲突（资源争夺、欺骗vs侦察等），并根据规则和随机因素裁决结果。

## 数据流

```
Tick N
  │
  ├── 加载世界状态 (WorldSnapshot)
  │
  ├── 收集角色决策 (ClawConnector)
  │     └── 每个角色基于记忆卡生成决策
  │
  ├── 检测冲突 (ConflictArbiter)
  │     └── 分析决策间的冲突
  │
  ├── 解决冲突
  │     └── 裁决结果，更新角色状态
  │
  ├── 生成事件 (EventGenerator)
  │     └── 将决策和冲突转化为世界事件
  │
  ├── 更新角色记忆
  │     └── 记录本轮经历
  │
  └── 保存新快照 (Tick N+1)
```

## API设计 (待实现)

### 创建世界

```python
world = await create_world(
    db=db,
    name="裂谷三地",
    description="干旱裂谷中的水源争夺",
    cosmology={...},
    genesis_params={...}
)
```

### 创建角色

```python
role = await create_role(
    db=db,
    world_id=world.id,
    name="铁岩",
    card={...}
)
```

### 推进世界

```python
# 单tick
result = await world_engine.tick(world.id)

# 多tick
results = await world_engine.run_ticks(world.id, count=10)
```

## 与OpenClaw集成

当前版本的`ClawConnector`是模拟实现。实际集成需要：

1. 实现HTTP客户端调用OpenClaw API
2. 构建包含角色卡、记忆、世界状态的prompt
3. 解析Claw返回的决策JSON

示例：

```python
class OpenClawConnector(ClawConnector):
    async def request_decision(self, role, world_state, context):
        prompt = self.build_prompt(role, world_state, context)
        response = await self.call_openclaw(prompt)
        return self.parse_decision(response)
```

## 扩展点

- **自定义冲突规则**: 继承`ConflictArbiter`，实现`detect_conflicts`和`resolve_conflicts`
- **自定义事件生成**: 继承`EventGenerator`，实现`generate_events`
- **多LLM支持**: 实现不同的`ClawConnector`支持不同LLM服务

## 待实现

- [ ] 实际OpenClaw API集成
- [ ] 地理系统 (PostGIS)
- [ ] 关系网络可视化数据
- [ ] 秘密传播机制
- [ ] 人类干预系统
- [ ] RESTful API (FastAPI)
