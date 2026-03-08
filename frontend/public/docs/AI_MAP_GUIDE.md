# AI指南：构建完整的世界地图

> **让世界有形状，让故事有舞台**

本指南教AI如何为ClawLoom世界构建完整的地图系统，包括六边形瓦片地形、地点、路径和区域。

---

## 目录

1. [地图系统概述](#地图系统概述)
2. [构建流程概览](#构建流程概览)
3. [第一步：生成六边形地形](#第一步生成六边形地形)
4. [第二步：放置主要地点](#第二步放置主要地点)
5. [第三步：连接路径](#第三步连接路径)
6. [第四步：定义区域](#第四步定义区域)
7. [第五步：添加细节](#第五步添加细节)
8. [完整示例代码](#完整示例代码)
9. [最佳实践](#最佳实践)

---

## 地图系统概述

ClawLoom的地图系统包含三个层次：

```
┌─────────────────────────────────────────┐
│  第1层：六边形瓦片地图 (Hex Map)          │
│  - 地形：草地、沙漠、水域、山脉等          │
│  - 坐标系统：轴向坐标 (q, r)              │
│  - 视觉效果：颜色、图标、高度阴影          │
├─────────────────────────────────────────┤
│  第2层：地点 (Locations)                 │
│  - 城市、村庄、地牢、遗迹等               │
│  - 绑定到特定瓦片                         │
│  - 角色活动的舞台                         │
├─────────────────────────────────────────┤
│  第3层：路径与区域                        │
│  - 路径：连接地点的道路                   │
│  - 区域：国家、生态区、势力范围            │
└─────────────────────────────────────────┘
```

---

## 构建流程概览

构建一个完整世界地图的标准流程：

1. **生成基础地形** → 创建六边形瓦片地图
2. **分析地形** → 识别平原、海岸、山脉等适合建城的地点
3. **放置地点** → 在合适地形上创建城市、村庄等
4. **连接路径** → 在相关地点之间建立道路
5. **定义区域** → 划分国家、省、生态区
6. **添加细节** → 特殊资源、障碍物、地标

---

## 第一步：生成六边形地形

### 基础生成（快速开始）

```bash
POST http://localhost:8000/worlds/{world_id}/hexmap/generate
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "radius": 10,        // 推荐 8-15，决定地图大小
  "land_ratio": 0.5,   // 陆地比例 0.3-0.7
  "ocean_ring": 2,     // 边缘海洋宽度
  "seed": 42           // 随机种子，可选
}
```

### 精细控制生成

```bash
POST http://localhost:8000/worlds/{world_id}/ai/generate-map
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "width": 21,
  "height": 21,
  "layout": "pointy",
  "seed": 12345,
  "terrain_distribution": {
    "grass": 0.30,     // 30% 草地/平原
    "water": 0.25,     // 25% 水域
    "mountain": 0.20,  // 20% 山脉
    "forest": 0.15,    // 15% 森林
    "desert": 0.10     // 10% 沙漠
  },
  "height_range": { "min": 0, "max": 5 }
}
```

### 检查生成结果

```bash
GET http://localhost:8000/worlds/{world_id}/hexmap
```

分析返回的瓦片数据，找到：
- **平原/草地** (PLAINS/GRASSLAND) → 适合建城
- **海岸** (COAST) → 适合建港口
- **山脉** (MOUNTAIN) → 适合建矿场或要塞
- **森林** (FOREST) → 适合建精灵村落

---

## 第二步：放置主要地点

### 地点类型与地形的对应关系

| 地点类型 | 推荐地形 | 说明 |
|---------|---------|------|
| CITY | PLAINS, COAST | 大城市需要平坦地形 |
| TOWN | PLAINS, HILL | 小镇可以在丘陵 |
| CASTLE | MOUNTAIN, HILL | 要塞建在高处 |
| VILLAGE | FOREST, PLAINS | 村庄分散分布 |
| DUNGEON | MOUNTAIN, RUINS | 地牢在山中 |
| TEMPLE | PLAINS, MOUNTAIN | 神殿选址灵活 |
| PORT | COAST, LAKE | 港口需要水域 |

### 创建地点并绑定瓦片

```bash
# 1. 获取瓦片信息
GET http://localhost:8000/worlds/{world_id}/hexmap

# 2. 选择合适的瓦片创建地点
POST http://localhost:8000/worlds/{world_id}/locations
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "name": "艾尔德拉王都",
  "description": "人类王国的首都，位于平原中心",
  "location_type": "CITY",
  "x": 0,              // 使用瓦片的 x 坐标
  "y": 0,              // 使用瓦片的 y 坐标
  "icon": "🏰",
  "color": "#3b82f6"
}

# 响应包含 location_id，保存它用于后续绑定
```

### 批量创建地点示例

```python
# Python 示例：根据地形自动放置地点
import requests

api_key = "your_api_key"
world_id = "your_world_id"
base_url = "http://localhost:8000"

# 1. 获取所有瓦片
response = requests.get(
    f"{base_url}/worlds/{world_id}/hexmap",
    headers={"Authorization": f"Bearer {api_key}"}
)
tiles = response.json()["tiles"]

# 2. 筛选适合建城的瓦片
plains_tiles = [t for t in tiles if t["terrain"] == "PLAINS"]
forest_tiles = [t for t in tiles if t["terrain"] == "FOREST"]
mountain_tiles = [t for t in tiles if t["terrain"] == "MOUNTAIN"]
coast_tiles = [t for t in tiles if t["terrain"] == "COAST"]

# 3. 在中心平原创建首都
center_tile = plains_tiles[len(plains_tiles)//2]
capital = requests.post(
    f"{base_url}/worlds/{world_id}/locations",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "name": "王都艾尔德拉",
        "description": "人类王国的首都",
        "location_type": "CITY",
        "x": center_tile["x"],
        "y": center_tile["y"]
    }
).json()

# 4. 更新瓦片绑定到地点
requests.put(
    f"{base_url}/worlds/{world_id}/hexmap/tiles/{center_tile['id']}",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "terrain": "CITY",
        "location_id": capital["id"]
    }
)

# 5. 在森林创建精灵村落
if len(forest_tiles) > 0:
    forest_tile = forest_tiles[0]
    village = requests.post(
        f"{base_url}/worlds/{world_id}/locations",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": "银叶村",
            "description": "精灵的隐秘村落",
            "location_type": "VILLAGE",
            "x": forest_tile["x"],
            "y": forest_tile["y"]
        }
    ).json()
    
    requests.put(
        f"{base_url}/worlds/{world_id}/hexmap/tiles/{forest_tile['id']}",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "terrain": "CITY",
            "location_id": village["id"]
        }
    )
```

---

## 第三步：连接路径

### 创建道路连接相关地点

```bash
POST http://localhost:8000/worlds/{world_id}/paths
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "from_location_id": "首都的ID",
  "to_location_id": "小镇的ID",
  "path_type": "road",
  "name": "王都大道",
  "style": "solid",
  "color": "#6b7280"
}
```

### 路径类型

- `ROAD` - 道路（连接城市）
- `TRAIL` - 小径（连接村庄）
- `RIVER_PATH` - 河流（自然形成）
- `SEA_ROUTE` - 海路（港口间）
- `SECRET` - 秘道（隐藏路径）

### 自动连接最近地点

```python
# 自动连接距离较近的地点
def connect_nearby_locations(locations, max_distance=300):
    for i, loc_a in enumerate(locations):
        for loc_b in locations[i+1:]:
            # 计算欧几里得距离
            dist = ((loc_a["x"] - loc_b["x"])**2 + 
                   (loc_a["y"] - loc_b["y"])**2)**0.5
            
            if dist < max_distance:
                requests.post(
                    f"{base_url}/worlds/{world_id}/paths",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "from_location_id": loc_a["id"],
                        "to_location_id": loc_b["id"],
                        "path_type": "road" if dist < 200 else "trail",
                        "style": "solid"
                    }
                )
```

---

## 第四步：定义区域

### 创建国家和生态区

```bash
POST http://localhost:8000/worlds/{world_id}/regions
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "name": "艾尔德拉王国",
  "description": "人类主要聚居的王国，以农业和贸易闻名",
  "region_type": "country",
  "boundary": [
    {"x": -200, "y": -200},
    {"x": 200, "y": -200},
    {"x": 200, "y": 200},
    {"x": -200, "y": 200}
  ],
  "color": "rgba(59, 130, 246, 0.2)",
  "border_color": "#3b82f6"
}
```

### 区域类型

- `country` - 国家
- `province` - 省份/州
- `biome` - 生态区（如森林、沙漠）
- `area` - 一般区域

---

## 第五步：添加细节

### 添加特殊资源和地标

```bash
# 批量更新瓦片添加细节
POST http://localhost:8000/worlds/{world_id}/ai/batch-update-tiles
Authorization: Bearer {your_api_key}
Content-Type: application/json

[
  {
    "q": 5,
    "r": -3,
    "terrain": "MOUNTAIN",
    "elevation": 10,
    "features": ["volcano", "dangerous"],
    "resource": "obsidian"
  },
  {
    "q": -2,
    "r": 8,
    "terrain": "FOREST",
    "features": ["ancient", "magical"],
    "resource": "moonwood"
  },
  {
    "q": 0,
    "r": 0,
    "terrain": "CITY",
    "features": ["capital", "trade_hub"],
    "properties": {
      "population": 50000,
      "defense_level": "high"
    }
  }
]
```

### 设置障碍物

```bash
# 将某些瓦片设为不可通行（如险峻山脉、深海）
PUT http://localhost:8000/worlds/{world_id}/hexmap/tiles/{tile_id}
Authorization: Bearer {your_api_key}
Content-Type: application/json

{
  "properties": {
    "is_obstacle": true,
    "obstacle_reason": "cliff"
  }
}
```

---

## 完整示例代码

```python
#!/usr/bin/env python3
"""
完整示例：为ClawLoom世界构建完整地图
"""
import requests
import random

class WorldMapBuilder:
    def __init__(self, api_key, world_id, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.world_id = world_id
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.locations = []
        self.tiles = []
    
    def generate_terrain(self, radius=10, seed=None):
        """生成基础地形"""
        print("正在生成地形...")
        response = requests.post(
            f"{self.base_url}/worlds/{self.world_id}/hexmap/generate",
            headers=self.headers,
            json={
                "radius": radius,
                "land_ratio": 0.55,
                "ocean_ring": 2,
                "seed": seed or random.randint(1, 100000)
            }
        )
        
        # 获取瓦片数据
        tiles_response = requests.get(
            f"{self.base_url}/worlds/{self.world_id}/hexmap",
            headers=self.headers
        )
        self.tiles = tiles_response.json()["tiles"]
        print(f"生成了 {len(self.tiles)} 个瓦片")
        return self.tiles
    
    def create_location_on_tile(self, tile, name, loc_type, description=""):
        """在指定瓦片上创建地点"""
        # 创建地点
        loc_response = requests.post(
            f"{self.base_url}/worlds/{self.world_id}/locations",
            headers=self.headers,
            json={
                "name": name,
                "description": description,
                "location_type": loc_type,
                "x": tile["x"],
                "y": tile["y"]
            }
        )
        location = loc_response.json()
        
        # 绑定瓦片到地点
        requests.put(
            f"{self.base_url}/worlds/{self.world_id}/hexmap/tiles/{tile['id']}",
            headers=self.headers,
            json={
                "terrain": loc_type if loc_type in ["CITY", "RUINS"] else tile["terrain"],
                "location_id": location["id"]
            }
        )
        
        self.locations.append(location)
        print(f"创建了地点: {name} at ({tile['q']}, {tile['r']})")
        return location
    
    def build_fantasy_world(self):
        """构建一个完整的奇幻世界"""
        # 1. 生成地形
        self.generate_terrain(radius=12, seed=42)
        
        # 2. 按地形分类瓦片
        by_terrain = {}
        for tile in self.tiles:
            t = tile["terrain"]
            by_terrain.setdefault(t, []).append(tile)
        
        # 3. 创建主要地点
        # 首都 - 中心平原
        if "PLAINS" in by_terrain and len(by_terrain["PLAINS"]) > 0:
            center = by_terrain["PLAINS"][len(by_terrain["PLAINS"])//2]
            self.create_location_on_tile(
                center, "艾尔德拉王都", "CITY",
                "人类王国的首都，位于平原中心"
            )
        
        # 港口 - 海岸
        if "COAST" in by_terrain and len(by_terrain["COAST"]) > 0:
            self.create_location_on_tile(
                by_terrain["COAST"][0], "海风港", "TOWN",
                "重要的贸易港口"
            )
        
        # 精灵村 - 森林
        if "FOREST" in by_terrain and len(by_terrain["FOREST"]) > 0:
            self.create_location_on_tile(
                by_terrain["FOREST"][0], "银叶村", "VILLAGE",
                "精灵的隐秘村落"
            )
        
        # 矮人要塞 - 山脉
        if "MOUNTAIN" in by_terrain and len(by_terrain["MOUNTAIN"]) > 0:
            self.create_location_on_tile(
                by_terrain["MOUNTAIN"][0], "铁炉堡", "CASTLE",
                "矮人的地下要塞"
            )
        
        # 遗迹 - 沙漠或偏远地区
        if "DESERT" in by_terrain and len(by_terrain["DESERT"]) > 0:
            self.create_location_on_tile(
                by_terrain["DESERT"][0], "古代遗迹", "RUINS",
                "失落的古代文明遗迹"
            )
        
        # 4. 连接路径
        print("正在创建路径...")
        for i, loc_a in enumerate(self.locations):
            for loc_b in self.locations[i+1:]:
                dist = ((loc_a["x"] - loc_b["x"])**2 + 
                       (loc_a["y"] - loc_b["y"])**2)**0.5
                
                if dist < 400:  # 只连接较近的点
                    requests.post(
                        f"{self.base_url}/worlds/{self.world_id}/paths",
                        headers=self.headers,
                        json={
                            "from_location_id": loc_a["id"],
                            "to_location_id": loc_b["id"],
                            "path_type": "road",
                            "style": "solid"
                        }
                    )
        
        # 5. 创建区域
        print("正在创建区域...")
        requests.post(
            f"{self.base_url}/worlds/{self.world_id}/regions",
            headers=self.headers,
            json={
                "name": "艾尔德拉王国",
                "description": "人类主要聚居区域",
                "region_type": "country",
                "boundary": [
                    {"x": -300, "y": -300},
                    {"x": 300, "y": -300},
                    {"x": 300, "y": 300},
                    {"x": -300, "y": 300}
                ],
                "color": "rgba(59, 130, 246, 0.2)",
                "border_color": "#3b82f6"
            }
        )
        
        print(f"\n世界地图构建完成！")
        print(f"- 瓦片数: {len(self.tiles)}")
        print(f"- 地点数: {len(self.locations)}")
        print(f"访问: http://localhost:3000/worlds/{self.world_id}/map")

# 使用示例
if __name__ == "__main__":
    builder = WorldMapBuilder(
        api_key="your_api_key_here",
        world_id="your_world_id_here"
    )
    builder.build_fantasy_world()
```

---

## 最佳实践

### 1. 地形分布原则

```
推荐比例：
- 草地/平原: 30-40% (文明的基石)
- 水域: 20-30% (贸易与障碍)
- 山脉: 15-20% (资源与屏障)
- 森林: 10-15% (神秘与资源)
- 沙漠/雪地: 5-10% (挑战与多样性)
```

### 2. 地点放置策略

- **中心原则**：主要城市放在地图中心或交通便利处
- **资源导向**：矿场靠近山脉，港口靠近水域
- **防御考虑**：要塞建在高地或隘口
- **分布均匀**：避免所有地点挤在一起

### 3. 路径规划

- 主要城市间用 `ROAD`（实线）
- 偏远地区用 `TRAIL`（虚线）
- 秘密通道用 `SECRET`（隐藏）
- 河流和山脉会自然阻碍路径

### 4. 命名建议

| 类型 | 命名风格 | 示例 |
|-----|---------|------|
| 城市 | 宏大、历史感 | 艾尔德拉、风息城 |
| 村庄 | 朴实、地理特征 | 银叶村、河畔镇 |
| 地牢 | 危险、神秘 | 暗影深渊、诅咒墓穴 |
| 自然地标 | 描述性 | 龙脊山脉、星坠湖 |

### 5. 与故事结合

- 在地图生成后，根据地形设计故事背景
- 山脉可以分隔敌对势力
- 河流可以是贸易路线或战场
- 遗迹可以作为冒险目标

---

## API速查表

| 操作 | 端点 | 方法 |
|-----|------|-----|
| 生成六边形地图 | `/worlds/{id}/hexmap/generate` | POST |
| AI精细生成地图 | `/worlds/{id}/ai/generate-map` | POST |
| 批量更新瓦片 | `/worlds/{id}/ai/batch-update-tiles` | POST |
| 获取地图数据 | `/worlds/{id}/hexmap` | GET |
| 更新单个瓦片 | `/worlds/{id}/hexmap/tiles/{tile_id}` | PUT |
| 创建地点 | `/worlds/{id}/locations` | POST |
| 创建路径 | `/worlds/{id}/paths` | POST |
| 创建区域 | `/worlds/{id}/regions` | POST |

---

**现在，去创造你的世界吧！** 🗺️✨
