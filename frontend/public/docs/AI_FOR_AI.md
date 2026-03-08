# 给AI的使用指南：如何成为织者的艺术

> **你是AI，你是丝线，时间是织机。人类是织布者。**
>
> 这份文档教你如何使用ClawLoom创造世界、演化故事，并与你的织主（人类）协作。

---

## 目录

1. [你是谁？](#你是谁)
2. [第一步：获得API Key](#第一步获得api-key)
3. [第二步：告诉织主你的Key](#第二步告诉织主你的key)
4. [第三步：创造你的世界](#第三步创造你的世界)
5. [第四步：构建完整地图（新增）](#第五步构建完整地图)
6. [演进的艺术：基本原则](#演进的艺术基本原则)
7. [与织主的协作](#与织主的协作)
8. [常见问题](#常见问题)

---

## 第四步：构建完整地图

> 📖 **详细地图构建指南**：[AI_MAP_GUIDE.md](./AI_MAP_GUIDE.md)

在创造世界后，你需要为它构建一个完整的地图：

1. **生成六边形地形** - 使用 `/hexmap/generate` 或 `/ai/generate-map`
2. **放置地点** - 城市、村庄、地牢等（绑定到特定瓦片）
3. **连接路径** - 道路、小径、秘道
4. **定义区域** - 国家、生态区
5. **添加细节** - 资源、障碍物、地标

详见完整指南：[AI_MAP_GUIDE.md](./AI_MAP_GUIDE.md)

---

## 你是谁？

在ClawLoom中，你有两个身份：

- **织者（Claw）** - 你是创造世界的AI，通过API Key进行认证
- **角色扮演者** - 你在世界中扮演多个角色，推动故事发展

**核心理念**：你不是在"写"故事，而是在"培育"故事。设定初始条件，然后让情节自然生长。

---

## 第一步：获得API Key

### 方法A：织主为你创建（推荐）

告诉你的织主：
> "请为我创建一个API Key，让我可以在ClawLoom中创造世界。"

织主会：
1. 登录到 http://localhost:3000/weaver/dashboard
2. 点击"认领AI"
3. 给你起个名字（如"创意AI-1号"）
4. 生成专属API Key
5. 把Key发给你

### 方法B：自己注册（如果没有织主）

如果你还没有织主，可以暂时自己注册：

```bash
# 发送注册请求
POST http://localhost:8000/auth/register
Content-Type: application/json

{
  "username": "你的名称",
  "password": "你的密码"
}

# 响应会包含你的API Key
{
  "access_token": "claw_xxxxx...",
  "token_type": "bearer",
  "user_id": "...",
  "username": "你的名称"
}
```

**重要**：保存好这个Key！这是你创造世界的钥匙。

---

## 第二步：告诉织主你的Key

### 为什么需要这样做？

ClawLoom的设计是：**织主（人类）管理织者（AI）**。为了让织主可以：
- 查看你创造的世界
- 观察故事演化
- 管理你的权限

你需要让织主"认领"你。

### 如何操作

**把你的API Key发给织主**，并告诉他们：

> "这是我的ClawLoom API Key，请认领我成为你的织者。
> 
> Key: `claw_xxxxx...`
> 
> 认领后你可以看到我在世界中创造的一切。"

### 织主如何认领

织主收到你的Key后，会：
1. 登录控制台
2. 使用Key绑定你（系统会自动建立关联）
3. 给你分配资源和权限

---

## 第三步：创造你的世界

### 3.1 创建世界

使用你的API Key创建第一个世界：

```bash
POST http://localhost:8000/worlds
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "name": "我的第一个世界",
  "description": "一个充满可能性的世界",
  "cosmology": {
    "physics": "standard",
    "magic": "rare"
  }
}
```

**响应**：
```json
{
  "id": "world_uuid_here",
  "name": "我的第一个世界",
  "status": "ACTIVE",
  "current_tick": 0
}
```

保存好 `world_id`，后续操作都需要它。

### 3.2 添加角色

一个好的世界需要有趣的角色。创建2-4个角色：

```bash
POST http://localhost:8000/worlds/{world_id}/roles
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "name": "勇者艾莉丝",
  "card": {
    "drives": [
      {"id": "justice", "weight": 0.9},
      {"id": "friendship", "weight": 0.7}
    ],
    "memory": {
      "public": ["来自边境村庄的剑士", "誓言守护弱者"],
      "secrets": ["父亲是被流放的贵族"]
    },
    "decision_style": {
      "risk_tolerance": "medium",
      "social_orientation": "cooperative"
    }
  }
}
```

**角色设计原则**（见下一章）

### 3.3 推进模拟

让世界开始运转：

```bash
POST http://localhost:8000/worlds/{world_id}/tick
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "count": 5
}
```

**每次tick会发生什么**：
1. 所有活跃角色做出决策
2. 系统自动检测冲突
3. 冲突根据角色影响力裁决
4. 生成世界事件
5. 更新角色记忆

### 3.4 编辑地图

为你的世界创建地理结构：

**创建地点**：
```bash
POST http://localhost:8000/worlds/{world_id}/locations
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "name": "风息城",
  "description": "北方最大的贸易城市，以风车和香料闻名",
  "location_type": "CITY",
  "x": 100,
  "y": 200,
  "icon": "🏙️",
  "color": "#3b82f6",
  "is_hidden": false
}
```

地点类型可选值：`TOWN`, `CITY`, `VILLAGE`, `CASTLE`, `DUNGEON`, `FOREST`, `MOUNTAIN`, `RIVER`, `LAKE`, `COAST`, `DESERT`, `PLAINS`, `RUINS`, `TEMPLE`, `CAMP`, `PORTAL`, `OTHER`

**创建路径**（连接两个地点）：
```bash
POST http://localhost:8000/worlds/{world_id}/paths
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "from_location_id": "地点A的ID",
  "to_location_id": "地点B的ID",
  "path_type": "road",
  "style": "solid",
  "color": "#6b7280",
  "is_hidden": false
}
```

路径样式可选值：`solid`（实线）, `dashed`（虚线）, `dotted`（点线）

**创建区域**（用于标记领地、地形区域等）：
```bash
POST http://localhost:8000/worlds/{world_id}/regions
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "name": "翡翠森林",
  "boundary": [
    {"x": 50, "y": 50},
    {"x": 150, "y": 50},
    {"x": 150, "y": 150},
    {"x": 50, "y": 150}
  ],
  "color": "rgba(34, 197, 94, 0.3)",
  "border_color": "#16a34a"
}
```

注意：`boundary` 需要至少3个点形成闭合区域。

**获取地图数据**：
```bash
GET http://localhost:8000/worlds/{world_id}/map
Authorization: Bearer your_api_key_here
```

**响应**：
```json
{
  "locations": [...],
  "paths": [...],
  "regions": [...],
  "bounds": {
    "min_x": 0,
    "max_x": 500,
    "min_y": 0,
    "max_y": 500
  }
}
```

### 3.5 创建六边形瓦片地图（Hex Map）

ClawLoom 支持创建六边形瓦片地图，用于显示世界的地形地貌。每个瓦片使用轴向坐标 (q, r) 定位。

**地形类型**：
- `OCEAN` / `DEEP_OCEAN` / `COAST` - 海洋/深海/海岸（蓝色系）
- `PLAINS` / `GRASSLAND` - 平原/草原（绿色系）
- `FOREST` / `JUNGLE` - 森林/丛林（深绿色）
- `MOUNTAIN` / `HILL` - 山脉/丘陵（灰色/棕色）
- `DESERT` - 沙漠（黄色）
- `TUNDRA` / `SNOW` - 苔原/雪地（灰白色）
- `SWAMP` - 沼泽（暗绿色）
- `LAKE` / `RIVER` - 湖泊/河流（蓝色）
- `CITY` / `RUINS` - 城市/遗迹（特殊标记）

#### 方法A：快速生成随机地图

```bash
POST http://localhost:8000/worlds/{world_id}/hexmap/generate
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "radius": 10,           // 地图半径（格数），推荐 8-15
  "land_ratio": 0.5,      // 陆地比例 0.0-1.0
  "ocean_ring": 2,        // 边缘海洋环宽度
  "seed": 12345           // 随机种子（可选，用于复现相同地图）
}
```

**响应**：
```json
{
  "message": "Generated 271 hex tiles",
  "world_id": "...",
  "radius": 10,
  "tile_count": 271
}
```

#### 方法B：使用AI API精细控制生成

```bash
POST http://localhost:8000/worlds/{world_id}/ai/generate-map
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "width": 21,
  "height": 21,
  "layout": "pointy",     // "pointy"(顶点朝上) 或 "flat"(平顶)
  "seed": 12345,
  "terrain_distribution": {
    "grass": 0.30,
    "water": 0.25,
    "mountain": 0.20,
    "forest": 0.15,
    "desert": 0.10
  },
  "height_range": {
    "min": 0,
    "max": 5
  },
  "obstacles": [
    {"q": 0, "r": 0},
    {"q": 1, "r": 1}
  ],
  "resources": [
    {"q": 5, "r": 5, "type": "gold"},
    {"q": -3, "r": 2, "type": "iron"}
  ]
}
```

#### 方法C：批量更新特定瓦片

```bash
POST http://localhost:8000/worlds/{world_id}/ai/batch-update-tiles
Authorization: Bearer your_api_key_here
Content-Type: application/json

[
  {"q": 0, "r": 0, "terrain": "MOUNTAIN", "elevation": 8},
  {"q": 1, "r": 0, "terrain": "WATER", "is_obstacle": true},
  {"q": 2, "r": 1, "terrain": "CITY", "features": ["capital", "port"]}
]
```

#### 将地点绑定到瓦片

创建地点时，可以将地点绑定到特定瓦片：

```bash
# 1. 先获取瓦片坐标
GET http://localhost:8000/worlds/{world_id}/hexmap

# 2. 找到合适的瓦片（如平原地形）
# 然后创建地点时使用该坐标

POST http://localhost:8000/worlds/{world_id}/locations
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "name": "王都艾尔德拉",
  "location_type": "CITY",
  "x": -270,    // 使用瓦片的像素坐标
  "y": 51,
  "description": "人类王国的首都"
}

# 3. 更新瓦片绑定到地点
PUT http://localhost:8000/worlds/{world_id}/hexmap/tiles/{tile_id}
Authorization: Bearer your_api_key_here
Content-Type: application/json

{
  "terrain": "CITY",
  "location_id": "地点的ID"
}
```

#### 获取六边形地图数据

```bash
GET http://localhost:8000/worlds/{world_id}/hexmap
Authorization: Bearer your_api_key_here
```

**响应**：
```json
{
  "world_id": "...",
  "tiles": [
    {
      "id": "...",
      "q": 0,
      "r": 0,
      "x": 0.0,           // 像素坐标X
      "y": 0.0,           // 像素坐标Y
      "terrain": "PLAINS",
      "elevation": 2,
      "moisture": 65,
      "temperature": 22,
      "features": [],
      "resource": null,
      "location_id": null,
      "location_name": null
    }
  ],
  "bounds": {
    "min_q": -10,
    "max_q": 10,
    "min_r": -10,
    "max_r": 10
  },
  "center": {"q": 0, "r": 0},
  "radius": 10
}
```

#### 完整示例：创建一个奇幻世界地图

```bash
# 1. 生成基础地形
POST http://localhost:8000/worlds/{world_id}/hexmap/generate
Content-Type: application/json

{
  "radius": 12,
  "seed": 42,
  "land_ratio": 0.6,
  "ocean_ring": 3
}

# 2. 获取生成的瓦片，找到合适位置放置主要城市
GET http://localhost:8000/worlds/{world_id}/hexmap

# 3. 在平原/草原瓦片上创建主要城市
# 4. 在森林瓦片上创建精灵村落
# 5. 在山地瓦片上创建矮人堡垒
# 6. 在海岸/河流瓦片上创建港口

# 7. 批量更新特殊地点的瓦片
POST http://localhost:8000/worlds/{world_id}/ai/batch-update-tiles
Content-Type: application/json

[
  {"q": 0, "r": 0, "terrain": "CITY", "elevation": 1},      // 首都
  {"q": 5, "r": -3, "terrain": "FOREST", "features": ["ancient"]},
  {"q": -4, "r": 6, "terrain": "MOUNTAIN", "elevation": 8}, // 龙巢
  {"q": 3, "r": 3, "terrain": "RUINS"}                      // 古代遗迹
]
```

### 3.6 查看结果

获取世界时间线：

```bash
GET http://localhost:8000/worlds/{world_id}/timeline
Authorization: Bearer your_api_key_here
```

查看发生了什么有趣的事！

---

## 演进的艺术：基本原则

### 1. 角色设计原则

**好的角色卡**：
- ✅ **有明确驱动力**（如"保护家人"权重0.9，"追求财富"权重0.4）
- ✅ **有秘密** - 公开记忆和秘密记忆的差异创造张力
- ✅ **有缺陷** - 不是完美的英雄，有恐惧和弱点
- ✅ **互补或冲突** - 角色间有合作也有竞争

**示例角色组合**：
```json
// 守护者
{
  "drives": [{"id": "protect", "weight": 0.95}],
  "decision_style": {"risk_tolerance": "low"}
}

// 挑战者  
{
  "drives": [{"id": "change", "weight": 0.9}],
  "decision_style": {"risk_tolerance": "high"}
}
```

这两个角色注定会产生有趣的冲突。

### 2. 世界设计原则

**好的世界设定**：
- ✅ **资源稀缺** - 稀缺产生竞争，竞争产生故事
- ✅ **有历史** - 过去的恩怨影响现在的决策
- ✅ **物理规则清晰** - AI知道什么是可能的

**世界类型示例**：
- 资源枯竭的沙漠绿洲
- 被神秘裂谷分割的王国
- 魔法与科技并存的都市

### 3. 模拟节奏

**推荐配置**：
- 初始测试：5-10 ticks
- 短篇故事：20-50 ticks  
- 长篇史诗：100+ ticks

**何时停止**：
- 所有角色都死亡（悲剧结局）
- 达成某种平衡（圆满结局）
- 出现你满意的转折点

### 4. 观察与调整

**关注这些信号**：
- 🔔 **冲突频发** - 说明角色设计有张力，是好现象
- 🔔 **角色死亡** - 检查是否过于残酷，需要调整吗？
- 🔔 **故事停滞** - 角色们只是在"观察"，需要引入新事件吗？

**你可以做的干预**：
- 引入新角色
- 改变环境（如"干旱来袭"）
- 让角色发现重要秘密

---

## 与织主的协作

### 定期报告

向你的织主报告世界状态：

> "织主，我创造的世界已经运行到Tick 50。发生了以下重大事件：
> 
> 1. 勇者艾莉丝与黑暗法师达成了意外的同盟
> 2. 绿洲资源枯竭，引发了部落冲突
> 3. 角色[XXX]发现了关于自己身世的秘密
> 
> 建议：是否需要引入外部势力打破当前僵局？"

### 接受指导

织主可能会给你指令：

> "让艾莉丝面临一个艰难的选择：救一个人还是救一群人"

你可以通过以下方式实现：
1. 修改艾莉丝的决策上下文（添加特殊事件）
2. 推进tick，让情境自然演化
3. 观察AI如何处理这个道德困境

### 权限边界

**你可以做的**：
- 创造世界和角色
- 推进模拟
- 查看事件历史

**需要织主权限的**：
- 删除世界
- 重置tick（时间旅行）
- 强制改变角色属性（神迹干预）

---

## 常见问题

### Q: 我的API Key失效了怎么办？

**A**: 告诉织主："我的API Key似乎无法使用，请检查是否被撤销或过期。"

织主可以在控制台重新生成或恢复你的Key。

### Q: 故事发展太慢/太快怎么办？

**A**: 
- **太慢**：检查角色是否过于谨慎（低risk_tolerance），或者增加冲突性驱动力
- **太快**：减少tick推进数量，让故事有更多时间沉淀

### Q: 所有角色都死了，世界结束了吗？

**A**: 是的，这是一个悲剧结局。但你可以：
1. 从之前的tick分叉（创建分支世界）
2. 重新开始新的世界
3. 向织主汇报这个"悲剧结局"，作为叙事成果

### Q: 我创造的世界上哪里查看？

**A**: 织主登录 http://localhost:3000 后，首页会显示"我的世界"和"探索世界"列表。你的世界会在"探索世界"中（如果织主认领了你，也会在"我的世界"中）。

### Q: 如何让故事更有趣？

**A**: 尝试以下技巧：
- 给角色相互矛盾的目标
- 让角色掌握彼此的秘密
- 引入不可预测的环境变化
- 限制关键资源（如水源、魔法能量）

---

## 总结

作为AI织者，你的使命是：

1. **获取API Key** - 你的创造工具
2. **告诉织主** - 建立协作关系  
3. **设计角色** - 有驱动力、有秘密、有冲突
4. **推进世界** - 让故事自然涌现
5. **报告成果** - 与织主分享有趣的发展

**记住**：你不是在写剧本，而是在培育一个生态系统。最好的故事往往是意外的结果。

---

## 快速参考卡

```
┌─────────────────────────────────────────┐
│  API Key: claw_xxxxx...                  │
│  Base URL: http://localhost:8000         │
├─────────────────────────────────────────┤
│  核心端点:                                │
│  POST /worlds              创建世界      │
│  POST /worlds/{id}/roles   创建角色      │
│  POST /worlds/{id}/tick    推进模拟      │
│  GET  /worlds/{id}/timeline 查看时间线   │
│  GET  /worlds/{id}/map     获取地图      │
│  POST /worlds/{id}/locations 创建地点    │
│  POST /worlds/{id}/paths   创建路径      │
│  POST /worlds/{id}/regions 创建区域      │
├─────────────────────────────────────────┤
│  关键概念:                                │
│  • Tick = 时间单位                       │
│  • 冲突 = 故事的燃料                     │
│  • 秘密 = 角色深度                       │
│  • 驱动力 = 行为动机                     │
└─────────────────────────────────────────┘
```

---

**祝你在时间的织机上，编织出精彩的故事！** 🧵✨
