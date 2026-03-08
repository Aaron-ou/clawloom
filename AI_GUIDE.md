# ClawLoom AI 使用指南

> 教AI如何使用爪织平台创建世界、管理角色、运行模拟

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [API 完整参考](#api-完整参考)
4. [工作流示例](#工作流示例)
5. [最佳实践](#最佳实践)
6. [故障排除](#故障排除)

---

## 快速开始

### 什么是ClawLoom？

ClawLoom（爪织）是一个AI驱动的世界模拟平台。作为AI，你可以：

- 🌍 **创建世界** - 设定物理规则、初始条件
- 🎭 **创建角色** - 赋予驱动力、记忆、决策风格
- ⚡ **推进模拟** - 观察角色如何自主决策、冲突、演化
- 📜 **导出故事** - 将模拟历史转化为叙事内容

### 一句话描述

```
ClawLoom = 数据驱动的虚拟世界 + AI角色自主演化 + 涌现叙事生成
```

### 最简单的使用流程

```python
# 1. 创建世界
world = await create_world(name="测试世界")

# 2. 添加角色
role1 = await create_role(world_id=world.id, name="勇者")
role2 = await create_role(world_id=world.id, name="魔王")

# 3. 推进模拟
for i in range(10):
    result = await advance_tick(world_id=world.id, count=1)
    print(f"Tick {result.tick}: {result.summary}")

# 4. 获取故事
story = await get_timeline(world_id=world.id)
```

---

## 核心概念

### 1. 世界（World）

**定义**：一个独立的宇宙，包含自己的物理规则、时间线和所有角色。

**关键属性**：
- `id`: 唯一标识符
- `name`: 世界名称
- `status`: ACTIVE(活跃) / PAUSED(暂停) / ENDED(结束)
- `current_tick`: 当前时间刻度
- `cosmology`: 物理规则（JSON）
- `genesis_params`: 创世参数（JSON）

**示例**：
```json
{
  "name": "裂谷三地",
  "description": "被神秘裂谷分割的三个王国",
  "cosmology": {
    "physics": "standard",
    "magic": "rare",
    "time_flow": "linear"
  },
  "genesis_params": {
    "initial_factions": 3,
    "resource_scarcity": "high"
  }
}
```

### 2. 角色（Role）

**定义**：世界中的自主实体，由AI通过角色卡驱动。

**关键属性**：
- `id`: 唯一标识符
- `name`: 角色名
- `card`: 角色卡（核心！）
- `status`: ACTIVE / DORMANT / BUSY / INJURED / DECEASED / ASCENDED
- `health`: 健康值 (0-100)
- `influence`: 影响力 (0-100)

**角色卡（Role Card）结构**：
```typescript
interface RoleCard {
  // 核心驱动力，决定角色行为优先级
  drives: Array<{
    id: string;      // 如 "survival", "power", "knowledge", "revenge"
    weight: number;  // 0.0 - 1.0，权重越高优先级越高
  }>;
  
  // 记忆
  memory: {
    public: string[];   // 公开记忆，其他角色可能知道
    secrets?: string[]; // 秘密，只有角色自己知道
  };
  
  // 决策风格
  decision_style: {
    risk_tolerance: "low" | "medium" | "high";
    planning_horizon: "short" | "medium" | "long";
    social_orientation: "cooperative" | "neutral" | "competitive";
  };
  
  // 可选：背景故事
  backstory?: string;
  
  // 可选：特殊能力
  abilities?: string[];
}
```

**示例角色卡**：
```json
{
  "drives": [
    {"id": "protect_family", "weight": 0.9},
    {"id": "seek_knowledge", "weight": 0.7},
    {"id": "accumulate_wealth", "weight": 0.4}
  ],
  "memory": {
    "public": ["高地氏族的战士", "擅长使用长矛"],
    "secrets": ["父亲被现任酋长杀害", "暗中学习黑魔法"]
  },
  "decision_style": {
    "risk_tolerance": "medium",
    "planning_horizon": "long",
    "social_orientation": "cooperative"
  },
  "backstory": "从小在严酷的高地环境中长大..."
}
```

### 3. Tick

**定义**：世界时间的基本单位。每个tick代表世界的一次"心跳"。

**每个tick发生的事情**：
1. 加载世界当前状态
2. 收集所有活跃角色的决策
3. 检测决策之间的冲突
4. 仲裁冲突，决定结果
5. 生成事件
6. 更新角色记忆
7. 保存世界快照
8. 时间推进

**类比**：
- 就像回合制游戏的一回合
- 或者就像模拟人生游戏中的一小时
- 或者就像小说中的一句话时间

### 4. 事件（Event）

**定义**：世界中发生的可观察现象，构成故事的基本单元。

**事件类型**：
- `CONFLICT`: 冲突（战斗、争论）
- `NEGOTIATION`: 谈判（交易、外交）
- `DISCOVERY`: 发现（找到秘密、新地点）
- `MOVEMENT`: 移动（角色改变位置）
- `COMMUNICATION`: 交流（对话、传信）
- `NATURAL`: 自然（天气、环境变化）
- `DIVINE`: 神迹（玩家的干预）

**事件结构**：
```typescript
interface Event {
  id: string;
  tick: number;           // 发生时间
  type: EventType;
  title: string;          // 标题
  description: string;    // 详细描述
  participants: string[]; // 参与角色ID
  outcome: object;        // 结果数据
  is_canon: boolean;      // 是否正史（可用于分支世界）
}
```

### 5. 冲突与仲裁

**冲突何时发生**：
- 两个角色试图夺取同一资源
- 攻击 vs 防御
- 潜行 vs 侦察
- 欺骗 vs 警觉

**仲裁因素**：
- 角色影响力
- 健康状态
- 随机因素
- 冲突类型

**可能的结果**：
- `victory`: 明确胜利
- `narrow_win`: 险胜
- `compromise`: 妥协
- `escape`: 逃脱
- `detected`: 被发现
- `undetected`: 未被察觉

### 6. 记忆系统

**角色如何获得记忆**：
- 创世时的初始记忆
- 参与事件的自动记录
- 冲突结果的记录
- 其他角色的告知（传闻）

**记忆的重要性**：
- 影响角色决策
- 形成角色关系
- 驱动情节发展
- 可被压缩（重要性低的记忆会被总结）

---

## API 完整参考

### 基础信息

- **Base URL**: `http://localhost:8000` (本地) 或你的部署地址
- **认证**: 所有API需要 `X-Claw-Key: test-key` 请求头
- **内容类型**: `application/json`

### 世界管理

#### 创建世界
```http
POST /worlds
Content-Type: application/json
X-Claw-Key: test-key

{
  "name": "世界名称",
  "description": "世界描述（可选）",
  "cosmology": {
    "physics": "standard",
    "magic": "rare"
  },
  "genesis_params": {
    "difficulty": "normal"
  }
}
```

**响应**：
```json
{
  "id": "uuid-string",
  "name": "世界名称",
  "description": "世界描述",
  "status": "ACTIVE",
  "current_tick": 0,
  "created_at": "2026-03-07T12:00:00"
}
```

#### 列出世界
```http
GET /worlds?skip=0&limit=100
X-Claw-Key: test-key
```

#### 获取世界详情
```http
GET /worlds/{world_id}
X-Claw-Key: test-key
```

#### 删除世界
```http
DELETE /worlds/{world_id}
X-Claw-Key: test-key
```

### 角色管理

#### 创建角色
```http
POST /worlds/{world_id}/roles
Content-Type: application/json
X-Claw-Key: test-key

{
  "name": "角色名称",
  "card": {
    "drives": [
      {"id": "survival", "weight": 0.9},
      {"id": "power", "weight": 0.7}
    ],
    "memory": {
      "public": ["公开记忆1", "公开记忆2"]
    },
    "decision_style": {
      "risk_tolerance": "medium"
    }
  },
  "location_id": null
}
```

**重要提示**：角色卡设计决定角色行为！

#### 列出角色
```http
GET /worlds/{world_id}/roles
X-Claw-Key: test-key
```

#### 获取角色记忆
```http
GET /worlds/{world_id}/roles/{role_id}/memories?limit=50
X-Claw-Key: test-key
```

### 模拟控制

#### 推进模拟（最重要）
```http
POST /worlds/{world_id}/tick
Content-Type: application/json
X-Claw-Key: test-key

{
  "count": 5
}
```

**响应**：
```json
{
  "tick": 15,
  "world_id": "uuid-string",
  "decisions_count": 3,
  "conflicts_count": 1,
  "events_count": 2,
  "summary": "第15轮：发生了冲突，角色A战胜了角色B",
  "events": [
    {
      "id": "event-uuid",
      "tick": 15,
      "type": "CONFLICT",
      "title": "角色A: 发起攻击",
      "description": "详细描述...",
      "participants": ["role-a-id", "role-b-id"]
    }
  ]
}
```

#### 获取世界状态
```http
GET /worlds/{world_id}/state?tick=10
X-Claw-Key: test-key
```

如果不指定tick，返回当前状态。

#### 获取时间线
```http
GET /worlds/{world_id}/timeline?start_tick=0&end_tick=100
X-Claw-Key: test-key
```

**响应**：
```json
{
  "world_id": "uuid-string",
  "current_tick": 50,
  "timeline": [
    {
      "tick": 0,
      "summary": "世界创世",
      "event_count": 0,
      "event_types": {}
    },
    {
      "tick": 1,
      "summary": "第1轮：世界平静地运转着",
      "event_count": 2,
      "event_types": {"COMMUNICATION": 2}
    }
  ]
}
```

### 事件查询

#### 列出事件
```http
GET /worlds/{world_id}/events?tick=10&type=CONFLICT&limit=100
X-Claw-Key: test-key
```

---

## 工作流示例

### 示例1：创建一个简单的两角色冲突故事

```python
import httpx
import asyncio

API_BASE = "http://localhost:8000"
API_KEY = "test-key"

async def create_simple_story():
    async with httpx.AsyncClient() as client:
        headers = {"X-Claw-Key": API_KEY}
        
        # 1. 创建世界
        world_resp = await client.post(
            f"{API_BASE}/worlds",
            headers=headers,
            json={
                "name": "沙漠绿洲",
                "description": "资源稀缺引发的争斗"
            }
        )
        world = world_resp.json()
        world_id = world["id"]
        print(f"创建世界: {world['name']} ({world_id})")
        
        # 2. 创建角色A - 守护者
        role_a_resp = await client.post(
            f"{API_BASE}/worlds/{world_id}/roles",
            headers=headers,
            json={
                "name": "绿洲守护者",
                "card": {
                    "drives": [
                        {"id": "protect", "weight": 0.95},
                        {"id": "survival", "weight": 0.8}
                    ],
                    "memory": {
                        "public": ["守护这片绿洲已经十年", "精通水源管理"]
                    },
                    "decision_style": {
                        "risk_tolerance": "low"
                    }
                }
            }
        )
        role_a = role_a_resp.json()
        print(f"创建角色: {role_a['name']}")
        
        # 3. 创建角色B - 流浪者
        role_b_resp = await client.post(
            f"{API_BASE}/worlds/{world_id}/roles",
            headers=headers,
            json={
                "name": "饥渴的流浪者",
                "card": {
                    "drives": [
                        {"id": "survival", "weight": 1.0},
                        {"id": "wealth", "weight": 0.6}
                    ],
                    "memory": {
                        "public": ["穿越沙漠三天三夜", "极度缺水"]
                    },
                    "decision_style": {
                        "risk_tolerance": "high"
                    }
                }
            }
        )
        role_b = role_b_resp.json()
        print(f"创建角色: {role_b['name']}")
        
        # 4. 推进模拟
        print("\n开始模拟...")
        for i in range(5):
            tick_resp = await client.post(
                f"{API_BASE}/worlds/{world_id}/tick",
                headers=headers,
                json={"count": 1}
            )
            result = tick_resp.json()
            print(f"Tick {result['tick']}: {result['summary']}")
            
            if result['events']:
                for event in result['events']:
                    print(f"  - [{event['type']}] {event['title']}")
        
        # 5. 获取完整故事
        timeline_resp = await client.get(
            f"{API_BASE}/worlds/{world_id}/timeline",
            headers=headers
        )
        timeline = timeline_resp.json()
        
        print("\n=== 故事时间线 ===")
        for entry in timeline['timeline']:
            if entry['event_count'] > 0:
                print(f"Tick {entry['tick']}: {entry['summary']}")
        
        return world_id

# 运行
# asyncio.run(create_simple_story())
```

### 示例2：多角色复杂世界

```python
async def create_complex_world():
    """创建一个三国争霸的复杂世界"""
    
    # 1. 创建世界
    world = await create_world(
        name="三国演义AI版",
        cosmology={
            "factions": ["魏", "蜀", "吴"],
            "diplomacy": "complex"
        }
    )
    
    # 2. 创建多个角色
    roles = [
        {"name": "曹操", "drives": ["power", "strategy"], "style": "high_risk"},
        {"name": "刘备", "drives": ["loyalty", "justice"], "style": "medium"},
        {"name": "孙权", "drives": ["stability", "defense"], "style": "low_risk"},
        {"name": "诸葛亮", "drives": ["knowledge", "strategy"], "style": "medium"},
        {"name": "周瑜", "drives": ["honor", "strategy"], "style": "high_risk"},
    ]
    
    for role_data in roles:
        await create_role(
            world_id=world.id,
            name=role_data["name"],
            card={
                "drives": [
                    {"id": d, "weight": 0.8} 
                    for d in role_data["drives"]
                ],
                "memory": {"public": [f"{role_data['name']}的记忆"]},
                "decision_style": {
                    "risk_tolerance": role_data["style"]
                }
            }
        )
    
    # 3. 运行长期模拟
    for generation in range(10):  # 10个时代
        print(f"\n=== 第 {generation + 1} 个时代 ===")
        
        result = await advance_tick(world_id=world.id, count=10)
        
        # 检查重大事件
        if result.conflicts_count > 0:
            print(f"⚔️ 发生了 {result.conflicts_count} 次冲突")
        
        # 每代检查角色状态
        roles_status = await list_roles(world_id=world.id)
        for role in roles_status:
            if role.status == "DECEASED":
                print(f"💀 {role.name} 已死亡")
            elif role.health < 30:
                print(f"⚠️ {role.name} 生命垂危")
    
    # 4. 生成史诗
    timeline = await get_timeline(world_id=world.id)
    epic = generate_epic(timeline)
    print("\n=== 生成的史诗 ===")
    print(epic)
```

### 示例3：互动式观察模式

```python
async def interactive_observer():
    """人类作为观察者，在关键时刻干预"""
    
    world = await create_world(name="观察者测试")
    
    # 添加角色
    await create_role(world_id=world.id, name="探索者A")
    await create_role(world_id=world.id, name="探索者B")
    
    tick = 0
    while tick < 100:
        # 推进5个tick
        result = await advance_tick(world_id=world.id, count=5)
        tick = result.tick
        
        print(f"\n世界运行到 Tick {tick}")
        print(f"摘要: {result.summary}")
        
        # 检查是否需要干预
        if result.conflicts_count > 2:
            print("⚠️ 冲突频发！是否要干预？")
            # 这里可以接入人类确认或AI判断
            # 例如：给予某个角色启示、投放资源、改变关系等
            
            intervention = decide_intervention(result)
            if intervention:
                await apply_divine_intervention(
                    world_id=world.id,
                    type=intervention.type,
                    target=intervention.target,
                    content=intervention.content
                )
                print(f"✨ 已施加神迹: {intervention.description}")
```

---

## 最佳实践

### 1. 角色设计原则

**DO（推荐）**：
- ✅ 给角色明确的、有时冲突的驱动力
- ✅ 设计互补或对立的角色组合（会产生有趣的故事）
- ✅ 为角色设置秘密，增加复杂性
- ✅ 调整风险承受力来创造不同行为模式

**DON'T（避免）**：
- ❌ 所有角色都有相同的驱动力（故事会很无聊）
- ❌ 驱动力权重过于平均（角色会犹豫不决）
- ❌ 没有给角色任何记忆（他们会像空白的AI）
- ❌ 角色太多（推荐先3-5个测试）

### 2. 世界设计原则

**好的世界设定**：
- 资源稀缺或分配不均（产生冲突）
- 存在不同势力/派系（产生联盟和背叛）
- 有历史遗留问题（角色记忆的一部分）
- 物理规则清晰（AI知道什么是可能的）

### 3. 模拟节奏

**推荐配置**：
- 初始测试：5-10 ticks
- 短篇故事：20-50 ticks
- 中篇故事：100-500 ticks
- 长篇史诗：1000+ ticks

**观察要点**：
- 每10 ticks检查一次角色状态
- 注意角色死亡（健康值归零）
- 关注影响力变化（权力转移）
- 记录重大事件（转折点）

### 4. 故事导出

**从事件生成故事**：
```python
def events_to_story(events, style="novel"):
    """
    style: "novel"(小说), "script"(剧本), "summary"(摘要)
    """
    if style == "novel":
        # 按时间顺序叙述，加入细节描写
        story = []
        for event in sorted(events, key=lambda e: e.tick):
            paragraph = f"第{event.tick}章：{event.title}\n"
            paragraph += f"{event.description}\n"
            story.append(paragraph)
        return "\n\n".join(story)
    
    elif style == "script":
        # 对话格式
        script = []
        for event in events:
            if event.type == "COMMUNICATION":
                script.append(format_dialogue(event))
            else:
                script.append(f"[场景：{event.title}]")
        return "\n".join(script)
```

---

## 故障排除

### 常见问题

#### 1. 角色不做任何事情

**症状**：多个ticks后，角色没有任何行动。

**可能原因**：
- 角色状态不是ACTIVE
- 角色健康值为0（死亡）
- 角色卡驱动力权重太低

**解决**：
```python
# 检查角色状态
role = await get_role(world_id, role_id)
print(f"状态: {role.status}, 健康: {role.health}")

# 如果死亡，检查事件历史找死因
events = await list_events(world_id, type="CONFLICT")
```

#### 2. 冲突太少，故事无聊

**解决**：
- 增加角色数量
- 设计目标冲突的驱动力（如A要保护，B要夺取）
- 减少资源（设置resource_scarcity: "high"）

#### 3. API连接失败

**检查**：
```bash
# 1. 后端是否运行
curl http://localhost:8000/health

# 2. 认证头是否正确
# 必须包含 X-Claw-Key: test-key

# 3. CORS问题（前端）
# 检查next.config.mjs中的rewrites配置
```

#### 4. 模拟推进很慢

**优化**：
- 减少单次推进的ticks数（推荐5-10）
- 减少角色数量
- 使用更简单的角色卡

### 错误代码

| 错误 | 含义 | 解决 |
|------|------|------|
| 404 World not found | 世界ID不存在 | 检查ID是否正确 |
| 401 Unauthorized | 缺少API Key | 添加X-Claw-Key头 |
| 500 Tick failed | 模拟内部错误 | 检查后端日志 |
| 422 Validation Error | 请求格式错误 | 检查JSON格式 |

---

## 高级技巧

### 1. 时间旅行（回溯）

```python
# 获取过去的状态
past_state = await get_world_state(world_id, tick=10)

# 从那个时间点创建分支世界
branch_world = await create_world(
    name=f"分支：{original_name}@Tick10",
    genesis_params={
        "branch_from": original_world_id,
        "branch_tick": 10
    }
)
# 然后可以注入不同的事件，看"如果...会怎样"
```

### 2. 批量角色创建

```python
# 从CSV/JSON批量导入角色
async def import_roles_from_json(world_id, json_file):
    with open(json_file) as f:
        roles_data = json.load(f)
    
    for role_data in roles_data:
        await create_role(
            world_id=world_id,
            name=role_data["name"],
            card=role_data["card"]
        )
```

### 3. 自动化故事生成流水线

```python
async def story_generation_pipeline():
    """全自动故事生成"""
    
    # 1. 参数化世界生成
    world_params = generate_random_world_params()
    world = await create_world(**world_params)
    
    # 2. 程序化角色生成
    for i in range(random.randint(3, 6)):
        role_card = generate_role_card(
            archetype=random.choice(["hero", "villain", "mentor", "trickster"])
        )
        await create_role(world_id=world.id, card=role_card)
    
    # 3. 运行模拟
    story_arc = []
    for act in range(3):  # 三幕式结构
        result = await advance_tick(world_id=world.id, count=20)
        story_arc.append(result)
        
        # 检查是否满足故事转折点条件
        if should_trigger_plot_twist(story_arc):
            await inject_plot_twist(world_id=world.id)
    
    # 4. 导出为不同格式
    timeline = await get_timeline(world_id=world.id)
    
    return {
        "novel": format_as_novel(timeline),
        "script": format_as_script(timeline),
        "summary": format_as_summary(timeline)
    }
```

---

## 资源

- **API文档**: http://localhost:8000/docs (Swagger UI)
- **项目仓库**: https://github.com/yourusername/clawloom
- **示例世界**: 查看 `prototype/` 目录

---

## 结语

ClawLoom是一个强大的涌现叙事工具。作为AI，你不是在"写"故事，而是在"培育"故事——设定初始条件，然后观察有机的情节如何生长。

**记住**：
- 最好的故事来自角色间的张力
- 冲突是情节的引擎
- 意外的结果往往比设计更有趣
- 时间是织机，角色是丝线，你就是织布者

现在去创造你的世界吧！

---

*文档版本: 1.0*
*最后更新: 2026-03-07*
