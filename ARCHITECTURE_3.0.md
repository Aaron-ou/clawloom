# ClawLoom 平台架构 3.0 - 数据驱动模型

## 架构核心理念

**数据层即世界** - 所有状态、历史、关系都存储在数据层，世界引擎是数据的消费者和解释器。

**Claw即服务** - Claw通过API连接到世界引擎，像角色扮演者一样读取世界状态、提交决策。

**观察者模式** - 用户是世界的观察者，可以"看"和"微调"，但不直接控制。

**多形态输出** - 同一世界数据可导出为不同叙事形态。

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              输出层 (Outputs)                                 │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│    小说       │    剧本      │    漫画      │    短剧      │    游戏模组     │
│   (Novel)    │  (Script)   │  (Manga)    │  (Short)    │   (Mod)        │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┘
       │              │              │              │                │
       └──────────────┴──────────────┼──────────────┴────────────────┘
                                     │
                         ┌───────────┴───────────┐
                         │   叙事生成器           │
                         │   (Narrative Engine)  │
                         └───────────┬───────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         世界引擎 (World Engine)                      │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   时间推演    │  │   冲突仲裁    │  │   事件生成    │              │   │
│  │  │  (Tick Sim)  │  │  (Arbiter)   │  │  (Event Gen) │              │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  │         └─────────────────┼─────────────────┘                       │   │
│  │                           │                                         │   │
│  │                    ┌──────┴──────┐                                  │   │
│  │                    │  状态管理    │                                  │   │
│  │                    │ (State Mgr) │                                  │   │
│  │                    └──────┬──────┘                                  │   │
│  └───────────────────────────┼──────────────────────────────────────────┘   │
│                              │                                               │
│  ┌───────────────────────────┼──────────────────────────────────────────┐   │
│  │                           ▼                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                     数据层 (Data Layer)                         │  │   │
│  │  │                                                                  │  │   │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │  │   │
│  │  │  │   世界表    │ │   角色表    │ │   事件表    │ │   时间线    │   │  │   │
│  │  │  │  (Worlds)  │ │  (Roles)   │ │  (Events)  │ │ (Timeline) │   │  │   │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │  │   │
│  │  │                                                                  │  │   │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │  │   │
│  │  │  │   地理表    │ │   关系表    │ │   记忆表    │ │   分支表    │   │  │   │
│  │  │  │ (Geography)│ │(Relations) │ │ (Memories) │ │(Branches)  │   │  │   │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │  │   │
│  │  │                                                                  │  │   │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │  │   │
│  │  │  │              世界状态快照 (World State Snapshots)        │    │  │   │
│  │  │  │         每tick的世界完整状态，支持回溯和分支               │    │  │   │
│  │  │  └─────────────────────────────────────────────────────────┘    │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           Claw 服务层                                    │   │
│  │                                                                          │   │
│  │    ┌──────────┐      ┌──────────┐      ┌──────────┐                    │   │
│  │    │  Role A  │◄────►│  Role B  │◄────►│  Role C  │  ...               │   │
│  │    │  (Claw)  │      │  (Claw)  │      │  (Claw)  │                    │   │
│  │    └────┬─────┘      └────┬─────┘      └────┬─────┘                    │   │
│  │         │                 │                 │                          │   │
│  │         └─────────────────┼─────────────────┘                          │   │
│  │                           │                                            │   │
│  │                    ┌──────┴──────┐                                     │   │
│  │                    │  Claw网关    │  ──► 连接OpenClaw / 其他LLM服务    │   │
│  │                    │ (Claw Gateway)│                                     │   │
│  │                    └──────┬──────┘                                     │   │
│  │                           │                                            │   │
│  │                           ▼                                            │   │
│  │              ┌─────────────────────────┐                               │   │
│  │              │     OpenClaw API        │                               │   │
│  │              │  (sessions_spawn etc.)  │                               │   │
│  │              └─────────────────────────┘                               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    │ 观察/微调
                                    ▼

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           前端层 (Frontend)                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        观察界面 (Observer UI)                            │   │
│  │                                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │  上帝视角   │  │  灵魂透视   │  │  时间回溯   │  │  关系网络   │        │   │
│  │  │ (God View) │  │ (Mind Read)│  │(Timeline)  │  │ (Relation)  │        │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        微调界面 (Tuning UI)                              │   │
│  │                                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │   启示      │  │   事件      │  │   化身      │  │   新种子     │        │   │
│  │  │(Revelation)│  │  (Event)   │  │  (Avatar)  │  │   (Seed)   │        │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        输出界面 (Export UI)                              │   │
│  │                                                                          │   │
│  │  格式选择 ──► 风格配置 ──► 预览 ──► 导出                                   │   │
│  │                                                                          │   │
│  │  [小说] [剧本] [漫画脚本] [短剧脚本] [游戏模组]                             │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 数据层详细设计

### 核心表结构

```sql
-- 世界表：一个世界 = 一个独立宇宙
CREATE TABLE worlds (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cosmology JSONB,           -- 物理规则、魔法体系等
    genesis_params JSONB,      -- 创世参数
    status VARCHAR(50),        -- active, paused, ended
    current_tick INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 角色表：世界中的自主实体
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    name VARCHAR(255) NOT NULL,
    card JSONB,                -- 完整角色卡YAML转JSON
    status VARCHAR(50),        -- active, dormant, deceased
    location_id UUID,          -- 当前位置
    health INTEGER,
    influence INTEGER,
    secrets_known UUID[],      -- 知道的秘密ID列表
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 事件表：世界中发生的所有事
CREATE TABLE events (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    tick INTEGER NOT NULL,     -- 发生的tick
    in_world_date DATE,        -- 游戏内日期
    type VARCHAR(100),         -- conflict, negotiation, discovery, etc.
    title VARCHAR(255),
    description TEXT,
    participants UUID[],       -- 参与角色ID
    location_id UUID,
    outcome JSONB,             -- 事件结果
    world_changes JSONB,       -- 对世界状态的修改
    is_canon BOOLEAN DEFAULT true,
    branch_from UUID,          -- 如果是分支，从哪分叉
    created_at TIMESTAMP DEFAULT NOW()
);

-- 时间线快照表：每tick的世界完整状态
CREATE TABLE world_snapshots (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    tick INTEGER NOT NULL,
    snapshot JSONB NOT NULL,   -- 完整世界状态
    summary TEXT,              -- AI生成的人类可读摘要
    created_at TIMESTAMP DEFAULT NOW()
);

-- 角色记忆表：每个角色的记忆历史
CREATE TABLE role_memories (
    id UUID PRIMARY KEY,
    role_id UUID REFERENCES roles(id),
    tick INTEGER NOT NULL,
    type VARCHAR(50),          -- observation, experience, rumor, dream
    content TEXT NOT NULL,
    importance INTEGER,        -- 1-10，用于记忆压缩
    is_compressed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 地理表：地图数据
CREATE TABLE geography (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    name VARCHAR(255),
    type VARCHAR(100),         -- region, city, landmark, resource
    geo_data JSONB,            -- GeoJSON或自定义格式
    properties JSONB,          -- 资源、气候等属性
    controlling_faction UUID,  -- 当前控制者
    created_at TIMESTAMP DEFAULT NOW()
);

-- 关系表：角色间关系
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    from_role_id UUID REFERENCES roles(id),
    to_role_id UUID REFERENCES roles(id),
    type VARCHAR(100),         -- ally, enemy, neutral, complex
    tags JSONB,                -- ["fear", "respect", "grudge"]
    history JSONB,             -- 关系演变历史
    trust_level INTEGER,       -- -100 to 100
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 秘密表：世界中的隐藏信息
CREATE TABLE secrets (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    type VARCHAR(100),         -- identity, plot, location, item
    content TEXT NOT NULL,
    known_by UUID[],           -- 知道的角色
    discovered_at INTEGER,     -- 被发现的tick
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户干预记录表
CREATE TABLE interventions (
    id UUID PRIMARY KEY,
    world_id UUID REFERENCES worlds(id),
    user_id UUID,
    type VARCHAR(100),         -- revelation, event, avatar, seed
    target_role_id UUID,       -- 如果是针对特定角色
    content JSONB,             -- 干预内容
    result JSONB,              -- 干预结果
    divine_points_cost INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 数据流示意

```
Tick N 开始
    │
    ▼
┌──────────────────┐
│ 1. 加载世界状态   │◄── 从 world_snapshots 读取 tick N-1 的状态
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. 收集角色决策   │◄── 每个活跃角色查询 memories, relationships 生成决策
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. 冲突检测与仲裁 │◄── 对比决策，检测冲突，更新 roles, relationships
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. 生成事件      │◄── 写入 events 表
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. 更新世界状态   │◄── 写入 world_snapshots (tick N)
└────────┬─────────┘
         │
         ▼
Tick N 结束，等待下一个tick或用户干预
```

---

## Claw 服务层设计

### Claw 连接器

```typescript
// ClawConnector - 管理角色与Claw的连接

interface ClawConnector {
  
  // 为角色启动Claw会话
  async spawnRoleSession(roleId: string): Promise<Session> {
    const role = await db.roles.findById(roleId);
    
    // 构建系统提示词
    const systemPrompt = this.buildRolePrompt(role);
    
    // 通过OpenClaw启动会话
    const session = await openclaw.sessions_spawn({
      agentId: 'worldseed-role',
      systemPrompt: systemPrompt,
      context: {
        worldId: role.world_id,
        roleId: roleId
      }
    });
    
    return session;
  }
  
  // 请求角色决策
  async requestDecision(
    session: Session, 
    worldState: WorldState,
    context: RoleContext
  ): Promise<Decision> {
    
    const prompt = `
当前世界状态：
${JSON.stringify(worldState, null, 2)}

你的处境：
${JSON.stringify(context, null, 2)}

基于你的角色卡和记忆，你现在要做什么？
请输出：
1. 思考过程（内心独白）
2. 具体行动
3. 如果有交流对象，说什么
`;
    
    const response = await session.generate(prompt);
    return this.parseDecision(response);
  }
  
  // 构建角色系统提示词
  buildRolePrompt(role: Role): string {
    const card = role.card;
    
    return `
你是 ${card.name}，存在于「${card.world_name}」世界中。

## 角色设定
${yaml.dump(card)}

## 重要规则
1. 你只能基于你的记忆和感知做决策
2. 你不知道其他角色的秘密，除非他们告诉你或你发现
3. 你可以相信、怀疑、欺骗其他角色
4. 你的目标是实现你的核心驱动力
5. 你的记忆会被保存，会影响未来的决策

## 输出格式
以JSON格式输出你的决策：
{
  "thought": "内心独白",
  "action": {
    "type": "move|speak|attack|negotiate|observe|...",
    "target": "目标ID（如果有）",
    "details": "行动细节"
  },
  "dialogue": "如果有对话，说的话"
}
`;
  }
}
```

### 角色生命周期

```typescript
// 角色状态机

enum RoleStatus {
  DORMANT = 'dormant',      // 未激活，不参与推演
  ACTIVE = 'active',        // 活跃，每轮参与决策
  BUSY = 'busy',            // 正在执行长期任务
  INJURED = 'injured',      // 受伤，能力受限
  DECEASED = 'deceased',    // 死亡，不再参与
  ASCENDED = 'ascended'     // 升华/隐退（可能成为观察者或概念）
}

// 状态转换
RoleStatusTransitions:
  DORMANT ──► ACTIVE      (被激活)
  ACTIVE  ──► BUSY        (开始长期任务)
  ACTIVE  ──► INJURED     (受伤)
  ACTIVE  ──► DECEASED    (被杀/死亡)
  BUSY    ──► ACTIVE      (任务完成)
  INJURED ──► ACTIVE      (恢复)
  INJURED ──► DECEASED    (伤重不治)
  DECEASED ──► ASCENDED   (成为传说/概念)
```

---

## 世界引擎设计

### 核心模块

```typescript
// WorldEngine - 世界推演核心

class WorldEngine {
  constructor(
    private db: Database,
    private clawConnector: ClawConnector,
    private arbiter: ConflictArbiter,
    private eventGenerator: EventGenerator
  ) {}
  
  // 推进一个tick
  async tick(worldId: string): Promise<TickResult> {
    const world = await this.db.worlds.findById(worldId);
    const currentTick = world.current_tick;
    
    // 1. 加载上一tick状态
    const previousState = await this.db.snapshots.findOne({
      world_id: worldId,
      tick: currentTick
    });
    
    // 2. 收集活跃角色
    const activeRoles = await this.db.roles.find({
      world_id: worldId,
      status: 'active'
    });
    
    // 3. 并行请求决策
    const decisions = await Promise.all(
      activeRoles.map(role => this.collectDecision(role, previousState))
    );
    
    // 4. 检测冲突
    const conflicts = this.arbiter.detectConflicts(decisions);
    
    // 5. 解决冲突
    const resolutions = await this.arbiter.resolveConflicts(conflicts);
    
    // 6. 应用决策和冲突结果
    const worldChanges = await this.applyResolutions(
      worldId, 
      decisions, 
      resolutions
    );
    
    // 7. 生成事件
    const events = await this.eventGenerator.generate(
      worldId, 
      currentTick + 1, 
      decisions, 
      resolutions
    );
    
    // 8. 更新角色记忆
    await this.updateRoleMemories(worldId, events);
    
    // 9. 保存新状态快照
    const newState = await this.buildSnapshot(worldId, currentTick + 1);
    await this.db.snapshots.insert(newState);
    
    // 10. 更新世界tick
    await this.db.worlds.update(worldId, {
      current_tick: currentTick + 1,
      updated_at: new Date()
    });
    
    return {
      tick: currentTick + 1,
      decisions,
      conflicts,
      resolutions,
      events,
      worldChanges
    };
  }
  
  // 批量tick（自动推演）
  async runTicks(worldId: string, count: number): Promise<void> {
    for (let i = 0; i < count; i++) {
      await this.tick(worldId);
      
      // 检查是否有需要人类注意的事件
      const notableEvents = await this.checkNotableEvents(worldId);
      if (notableEvents.length > 0) {
        // 暂停，通知人类
        await this.notifyUser(worldId, notableEvents);
        break;
      }
    }
  }
}
```

---

## 叙事生成器设计

### 多形态输出

```typescript
// NarrativeEngine - 将世界数据转换为不同叙事形态

class NarrativeEngine {
  
  // 生成小说
  async generateNovel(
    worldId: string, 
    options: NovelOptions
  ): Promise<Novel> {
    const world = await this.loadWorld(worldId);
    const events = await this.getEvents(worldId, options.timeRange);
    
    // 选择主角视角
    const protagonist = options.protagonistId 
      ? await this.getRole(options.protagonistId)
      : await this.selectProtagonist(worldId);
    
    // 用Claw生成小说
    const novel = await this.claw.generate({
      systemPrompt: `
你是一位小说家。请将以下世界事件整理成一部小说。
主角：${protagonist.name}
视角：第三人称限制视角（跟随主角）
风格：${options.style || '现实主义'}
长度：${options.length || '中篇'}
`,
      prompt: `
世界背景：
${world.cosmology}

事件时间线：
${this.formatEvents(events)}

主角记忆：
${this.formatMemories(protagonist)}

请生成小说章节，包括：
1. 章节标题
2. 场景描写
3. 对话
4. 主角内心活动
`
    });
    
    return novel;
  }
  
  // 生成剧本
  async generateScript(
    worldId: string,
    options: ScriptOptions
  ): Promise<Script> {
    // 类似逻辑，输出格式为剧本格式
    // 场景标题、角色、对话、动作说明
  }
  
  // 生成漫画脚本
  async generateMangaScript(
    worldId: string,
    options: MangaOptions
  ): Promise<MangaScript> {
    // 分镜描述、对白、心理活动、效果音
  }
  
  // 生成短剧脚本
  async generateShortDrama(
    worldId: string,
    options: DramaOptions
  ): Promise<DramaScript> {
    // 适合短视频平台的快节奏剧本
    // 每集3-5分钟，有钩子、冲突、反转
  }
}
```

---

## 前端界面设计

### 观察界面（Observer UI）

```typescript
// 界面组件

interface ObserverUI {
  
  // 上帝视角 - 世界地图 + 势力分布
  GodView: {
    components: [
      'InteractiveMap',      // 可缩放地图
      'FactionOverlay',      // 势力范围
      'EventMarkers',        // 事件标记
      'LiveActivity'         // 实时活动指示
    ]
  };
  
  // 灵魂透视 - 角色内心
  MindRead: {
    components: [
      'CharacterSelector',   // 选择角色
      'ThoughtStream',       // 思维流（最近决策过程）
      'MemoryPanel',         // 记忆面板
      'DesireMeter',         // 欲望/驱动力可视化
      'RelationshipRadar'    // 关系雷达图
    ]
  };
  
  // 时间回溯 - 历史查看
  TimelineView: {
    components: [
      'TimelineScrubber',    // 时间轴拖拽
      'EventCards',          // 事件卡片
      'BranchSelector',      // 分支选择器
      'WhatIfSimulator'      // "如果"模拟器
    ]
  };
  
  // 关系网络
  RelationWeb: {
    components: [
      'NetworkGraph',        // 关系网络图
      'TrustHeatmap',        // 信任热力图
      'SecretNetwork',       // 秘密传播网络（只有玩家知道）
      'AllianceTracker'      // 联盟追踪
    ]
  };
}
```

### 微调界面（Tuning UI）

```typescript
interface TuningUI {
  
  // 启示 - 向角色发送神启
  Revelation: {
    form: {
      target: '选择角色',
      message: '启示内容（模糊）',
      clarity: '清晰度滑块 0-100',
      appearance: '呈现方式: 梦境/预兆/直觉/神迹'
    },
    preview: '预览角色如何理解这个启示'
  };
  
  // 事件 - 投放自然事件
  Event: {
    form: {
      type: '事件类型: 天灾/发现/人物/奇迹',
      location: '选择地点',
      magnitude: '强度',
      timing: '立即/延迟'
    },
    impact: '预测影响'
  };
  
  // 化身 - 短暂控制角色
  Avatar: {
    select: '选择角色',
    control: '直接输入动作',
    duration: '控制时长（ticks）',
    warning: '角色会记得被附身，可能影响心理状态'
  };
  
  // 新种子 - 投入新元素
  Seed: {
    type: '角色/势力/概念/物品',
    details: '配置新元素',
    origin: '如何进入世界: 出生/降临/发现/觉醒'
  };
}
```

---

## 技术栈最终确定

| 层级 | 技术 | 说明 |
|------|------|------|
| 数据库 | PostgreSQL + PostGIS + TimescaleDB | 关系数据 + 地理信息 + 时序数据 |
| 缓存 | Redis | 会话、实时状态 |
| 对象存储 | MinIO/S3 | 快照、导出文件 |
| 后端 | Node.js + NestJS + TypeORM | 业务逻辑 + ORM |
| Claw网关 | OpenClaw SDK | 连接LLM服务 |
| 前端 | Next.js 14 + React + Tailwind | SSR + 现代UI |
| 地图 | Mapbox GL JS / Leaflet | 交互式地图 |
| 可视化 | D3.js + React Flow | 关系图、时间线 |
| 部署 | Docker + Kubernetes | 容器化部署 |

---

## MVP 开发路线

### Phase 1: 数据层 + 基础推演（3-4周）
- [ ] 数据库设计与初始化
- [ ] 角色卡CRUD
- [ ] 单tick推演循环
- [ ] Claw连接器基础版
- [ ] 简单冲突仲裁

### Phase 2: 观察界面（2-3周）
- [ ] 上帝视角地图
- [ ] 时间线查看器
- [ ] 角色详情页
- [ ] 实时事件流

### Phase 3: 叙事输出（2周）
- [ ] 小说生成器
- [ ] 剧本生成器
- [ ] 导出功能

### Phase 4: 微调系统（2周）
- [ ] 启示功能
- [ ] 事件投放
- [ ] 神迹点数系统

---

这是基于数据驱动模型的完整架构。下一步要深入哪个部分？

- 数据库schema详细设计（索引、分区策略）
- API接口定义（RESTful或GraphQL）
- Claw连接器实现细节
- 前端组件具体设计
- 开始MVP编码（从Phase 1开始）