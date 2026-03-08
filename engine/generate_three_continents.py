#!/usr/bin/env python3
"""
生成三块大陆的大型世界地图
- 北大陆：冰雪为主，中央有不冻湖
- 西大陆：沙漠为主，点缀高山和湿地
- 东大陆：茂密森林
每块大陆至少5个城镇
"""
import requests
import random
import json
from typing import List, Dict, Any, Optional

class ThreeContinentsGenerator:
    def __init__(self, api_key: str, world_id: str = None, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.world_id = world_id
        self.tiles = []
        self.locations = []
        
    def create_world(self, name: str, description: str) -> str:
        """创建新世界"""
        response = requests.post(
            f"{self.base_url}/worlds",
            headers=self.headers,
            json={
                "name": name,
                "description": description
            }
        )
        data = response.json()
        self.world_id = data["id"]
        print(f"✓ 创建世界: {name} (ID: {self.world_id})")
        return self.world_id
    
    def generate_base_map(self, radius: int = 25, seed: int = 42):
        """生成基础大地图"""
        print(f"\n🗺️  生成基础地形 (半径: {radius})...")
        response = requests.post(
            f"{self.base_url}/worlds/{self.world_id}/hexmap/generate",
            headers=self.headers,
            json={
                "radius": radius,
                "land_ratio": 0.65,
                "ocean_ring": 4,
                "seed": seed
            }
        )
        print(f"✓ 基础地图生成完成")
        
        # 获取所有瓦片
        response = requests.get(
            f"{self.base_url}/worlds/{self.world_id}/hexmap",
            headers=self.headers
        )
        self.tiles = response.json()["tiles"]
        print(f"✓ 获取 {len(self.tiles)} 个瓦片")
        return self.tiles
    
    def clear_and_regenerate_continents(self):
        """清除地图并重新生成三块大陆"""
        print("\n🎨 生成三块大陆的特殊地形...")
        
        # 按坐标将瓦片分到三个大陆
        # 北大陆: r < -5 (北方，冰雪)
        # 西大陆: q < -5, r >= -5 (西方，沙漠)
        # 东大陆: q > 5, r >= -5 (东方，森林)
        # 中部: 海洋或过渡带
        
        north_tiles = [t for t in self.tiles if t["r"] < -5]
        west_tiles = [t for t in self.tiles if t["q"] < -5 and t["r"] >= -5]
        east_tiles = [t for t in self.tiles if t["q"] > 5 and t["r"] >= -5]
        central_tiles = [t for t in self.tiles if -5 <= t["q"] <= 5 and t["r"] >= -5]
        
        print(f"  北大陆瓦片: {len(north_tiles)}")
        print(f"  西大陆瓦片: {len(west_tiles)}")
        print(f"  东大陆瓦片: {len(east_tiles)}")
        print(f"  中央/海洋: {len(central_tiles)}")
        
        updates = []
        
        # ========== 北大陆：冰雪世界 ==========
        print("\n  ❄️  构建北大陆（冰雪）...")
        # 找中心点创建不冻湖
        if north_tiles:
            center_north = north_tiles[len(north_tiles)//2]
            lake_q, lake_r = center_north["q"], center_north["r"]
            
            for tile in north_tiles:
                q, r = tile["q"], tile["r"]
                dist_to_center = max(abs(q - lake_q), abs(r - lake_r), abs(-q-r - (-lake_q-lake_r)))
                
                if dist_to_center <= 2:
                    # 不冻湖中心
                    updates.append({
                        "q": q, "r": r, "terrain": "LAKE", "elevation": 0,
                        "temperature": 5, "features": ["unfrozen", "magical"]
                    })
                elif dist_to_center <= 4:
                    # 湖周围的湿地/苔原
                    updates.append({
                        "q": q, "r": r, "terrain": "TUNDRA", "elevation": 1,
                        "temperature": -5
                    })
                elif random.random() < 0.7:
                    # 雪地
                    updates.append({
                        "q": q, "r": r, "terrain": "SNOW", "elevation": random.randint(2, 5),
                        "temperature": random.randint(-20, -5)
                    })
                else:
                    # 冰山/山脉
                    updates.append({
                        "q": q, "r": r, "terrain": "MOUNTAIN", "elevation": random.randint(6, 10),
                        "temperature": random.randint(-25, -15),
                        "features": ["icy_peak"]
                    })
        
        # ========== 西大陆：沙漠与高山 ==========
        print("  🏜️  构建西大陆（沙漠）...")
        if west_tiles:
            for tile in west_tiles:
                q, r = tile["q"], tile["r"]
                rand = random.random()
                
                if rand < 0.6:
                    # 沙漠
                    updates.append({
                        "q": q, "r": r, "terrain": "DESERT", "elevation": random.randint(1, 3),
                        "temperature": random.randint(30, 45), "moisture": random.randint(5, 20)
                    })
                elif rand < 0.75:
                    # 高山（点缀）
                    updates.append({
                        "q": q, "r": r, "terrain": "MOUNTAIN", "elevation": random.randint(7, 10),
                        "temperature": random.randint(10, 25),
                        "features": ["oasis_source"]
                    })
                elif rand < 0.85:
                    # 湿地/绿洲
                    updates.append({
                        "q": q, "r": r, "terrain": "SWAMP", "elevation": 0,
                        "temperature": random.randint(25, 35), "moisture": random.randint(70, 90),
                        "features": ["oasis"]
                    })
                else:
                    # 岩石/荒地
                    updates.append({
                        "q": q, "r": r, "terrain": "HILL", "elevation": random.randint(3, 5),
                        "temperature": random.randint(25, 40)
                    })
        
        # ========== 东大陆：茂密森林 ==========
        print("  🌲 构建东大陆（森林）...")
        if east_tiles:
            for tile in east_tiles:
                q, r = tile["q"], tile["r"]
                rand = random.random()
                
                if rand < 0.65:
                    # 茂密森林
                    updates.append({
                        "q": q, "r": r, "terrain": "FOREST", "elevation": random.randint(1, 3),
                        "temperature": random.randint(15, 25), "moisture": random.randint(60, 90),
                        "features": ["dense"]
                    })
                elif rand < 0.80:
                    # 丛林
                    updates.append({
                        "q": q, "r": r, "terrain": "JUNGLE", "elevation": 1,
                        "temperature": random.randint(20, 30), "moisture": random.randint(80, 95)
                    })
                elif rand < 0.90:
                    # 林间平原
                    updates.append({
                        "q": q, "r": r, "terrain": "PLAINS", "elevation": 1,
                        "temperature": random.randint(18, 25), "moisture": random.randint(50, 70)
                    })
                else:
                    # 河流/湖泊
                    updates.append({
                        "q": q, "r": r, "terrain": "RIVER" if random.random() < 0.7 else "LAKE",
                        "elevation": 0, "temperature": random.randint(18, 22)
                    })
        
        # ========== 中部：海洋 ==========
        print("  🌊 设置中部为海洋...")
        for tile in central_tiles:
            updates.append({
                "q": tile["q"], "r": tile["r"],
                "terrain": "OCEAN", "elevation": -2,
                "temperature": random.randint(10, 20)
            })
        
        # 批量更新
        print(f"\n  正在更新 {len(updates)} 个瓦片...")
        chunk_size = 100
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i+chunk_size]
            response = requests.post(
                f"{self.base_url}/worlds/{self.world_id}/ai/batch-update-tiles",
                headers=self.headers,
                json=chunk
            )
            if response.status_code == 200:
                print(f"    ✓ 更新 {i+len(chunk)}/{len(updates)}")
            else:
                print(f"    ✗ 更新失败: {response.text[:100]}")
        
        print("✓ 地形生成完成")
        return north_tiles, west_tiles, east_tiles
    
    def create_location(self, tile: Dict, name: str, loc_type: str, description: str, icon: str = None) -> Dict:
        """在指定瓦片上创建地点"""
        # 创建地点
        response = requests.post(
            f"{self.base_url}/worlds/{self.world_id}/locations",
            headers=self.headers,
            json={
                "name": name,
                "description": description,
                "location_type": loc_type,
                "x": int(tile["x"]),
                "y": int(tile["y"]),
                "icon": icon
            }
        )
        
        if response.status_code != 200:
            print(f"  ✗ 创建地点失败: {name}")
            return None
        
        location = response.json()
        
        # 更新瓦片绑定到地点
        requests.put(
            f"{self.base_url}/worlds/{self.world_id}/hexmap/tiles/{tile['id']}",
            headers=self.headers,
            json={
                "terrain": loc_type if loc_type in ["CITY", "TOWN", "CASTLE"] else tile["terrain"],
                "location_id": location["id"],
                "properties": {"city_type": loc_type}
            }
        )
        
        self.locations.append(location)
        print(f"  ✓ 创建地点: {name} ({loc_type})")
        return location
    
    def create_north_continent_locations(self, tiles: List[Dict]):
        """创建北大陆（冰雪）的地点"""
        print("\n❄️  北大陆 - 创建城镇...")
        
        # 找到不冻湖周围的瓦片（城镇）
        lake_tiles = [t for t in tiles if t["terrain"] == "LAKE"]
        tundra_tiles = [t for t in tiles if t["terrain"] == "TUNDRA"]
        snow_tiles = [t for t in tiles if t["terrain"] == "SNOW"]
        mountain_tiles = [t for t in tiles if t["terrain"] == "MOUNTAIN"]
        
        # 1. 不冻湖畔城（首都）
        if tundra_tiles:
            capital_tile = min(tundra_tiles, key=lambda t: abs(t["q"]) + abs(t["r"]))
            self.create_location(
                capital_tile, "霜语城", "CITY",
                "北大陆最大的城市，围绕不冻湖而建，因魔法温泉而终年不冻，是冰雪世界的贸易中心",
                "🏰"
            )
        
        # 2. 冰风港（港口）
        coast_tiles = [t for t in tiles if t["terrain"] in ["COAST", "OCEAN"] and t.get("elevation", 0) >= 0]
        if coast_tiles:
            self.create_location(
                coast_tiles[0], "冰风港", "TOWN",
                "北方最重要的港口，勇敢的渔民从这里出发捕捞冰海巨鱼",
                "⚓"
            )
        
        # 3. 雪原镇
        if snow_tiles:
            self.create_location(
                snow_tiles[len(snow_tiles)//3], "雪原镇", "VILLAGE",
                "位于广袤雪原上的游牧村落，居民以驯养冰原兽为生",
                "🏘️"
            )
        
        # 4. 霜牙要塞（军事要塞）
        if mountain_tiles:
            self.create_location(
                mountain_tiles[0], "霜牙要塞", "CASTLE",
                "扼守北方山脉通道的要塞，守卫着通往不冻湖的唯一陆路",
                "🏔️"
            )
        
        # 5. 温泉村（靠近不冻湖）
        if tundra_tiles and len(tundra_tiles) > 1:
            self.create_location(
                tundra_tiles[-1], "温泉村", "VILLAGE",
                "因地下温泉而温暖的小村落，是疲惫旅人的休憩之地",
                "♨️"
            )
        
        # 6. 极光哨站（边境）
        if snow_tiles and len(snow_tiles) > 2:
            self.create_location(
                snow_tiles[-1], "极光哨站", "CAMP",
                "位于北境最边缘的瞭望哨，据说能看到神秘的极光幻象",
                "⛺"
            )
    
    def create_west_continent_locations(self, tiles: List[Dict]):
        """创建西大陆（沙漠）的地点"""
        print("\n🏜️  西大陆 - 创建城镇...")
        
        desert_tiles = [t for t in tiles if t["terrain"] == "DESERT"]
        mountain_tiles = [t for t in tiles if t["terrain"] == "MOUNTAIN"]
        swamp_tiles = [t for t in tiles if t["terrain"] == "SWAMP"]
        hill_tiles = [t for t in tiles if t["terrain"] == "HILL"]
        
        # 1. 金砂城（沙漠中心大城）
        if desert_tiles:
            capital_tile = desert_tiles[len(desert_tiles)//2]
            self.create_location(
                capital_tile, "金砂城", "CITY",
                "沙漠中的明珠，建立在古代绿洲之上，以黄金贸易闻名",
                "🏰"
            )
        
        # 2. 绿洲镇
        if swamp_tiles:
            self.create_location(
                swamp_tiles[0], "绿洲镇", "TOWN",
                "沙漠中难得的绿洲，是商队必经的补给站",
                "🌴"
            )
        
        # 3. 铁岩堡（高山要塞）
        if mountain_tiles:
            self.create_location(
                mountain_tiles[0], "铁岩堡", "CASTLE",
                "建立在高山之巅的要塞，俯瞰整个沙漠，易守难攻",
                "🏔️"
            )
        
        # 4. 沙海商站
        if desert_tiles and len(desert_tiles) > 3:
            self.create_location(
                desert_tiles[len(desert_tiles)//4], "沙海商站", "TOWN",
                "位于沙漠商路中点的大型驿站，各种奇珍异宝在此交易",
                "🏪"
            )
        
        # 5. 岩窟村
        if hill_tiles:
            self.create_location(
                hill_tiles[0], "岩窟村", "VILLAGE",
                "居民居住在天然岩窟中，善于挖掘地下水脉",
                "🛖"
            )
        
        # 6. 遗迹哨站（靠近某处遗迹）
        if desert_tiles and len(desert_tiles) > 2:
            self.create_location(
                desert_tiles[-2], "遗迹哨站", "CAMP",
                "守卫着附近古代遗迹的临时营地，吸引了众多冒险者",
                "🏛️"
            )
    
    def create_east_continent_locations(self, tiles: List[Dict]):
        """创建东大陆（森林）的地点"""
        print("\n🌲 东大陆 - 创建城镇...")
        
        forest_tiles = [t for t in tiles if t["terrain"] == "FOREST"]
        jungle_tiles = [t for t in tiles if t["terrain"] == "JUNGLE"]
        plains_tiles = [t for t in tiles if t["terrain"] == "PLAINS"]
        river_tiles = [t for t in tiles if t["terrain"] in ["RIVER", "LAKE"]]
        
        # 1. 翠林城（精灵王城）
        if forest_tiles:
            capital_tile = forest_tiles[len(forest_tiles)//2]
            self.create_location(
                capital_tile, "翠林城", "CITY",
                "隐藏在古老森林深处的精灵城市，建筑与树木融为一体",
                "🌳"
            )
        
        # 2. 河湾镇
        if river_tiles:
            self.create_location(
                river_tiles[0], "河湾镇", "TOWN",
                "位于河流交汇处的小镇，渔猎资源丰富",
                "🏘️"
            )
        
        # 3. 深林前哨
        if jungle_tiles:
            self.create_location(
                jungle_tiles[0], "深林前哨", "CASTLE",
                "深入丛林的防御工事，防范着丛林深处的危险生物",
                "🏰"
            )
        
        # 4. 木语村
        if forest_tiles and len(forest_tiles) > 3:
            self.create_location(
                forest_tiles[len(forest_tiles)//3], "木语村", "VILLAGE",
                "德鲁伊的聚集地，村民能与森林中的动物交流",
                "🦉"
            )
        
        # 5. 林间驿站
        if plains_tiles:
            self.create_location(
                plains_tiles[0], "林间驿站", "TOWN",
                "森林边缘的贸易站，连接着森林与外部世界的商路",
                "🏪"
            )
        
        # 6. 古树神殿
        if forest_tiles and len(forest_tiles) > 2:
            self.create_location(
                forest_tiles[-2], "古树神殿", "TEMPLE",
                "供奉着一棵据说活了千年的古树的圣地",
                "⛩️"
            )
    
    def create_paths_between_locations(self):
        """在地点之间创建路径"""
        print("\n🛤️  创建路径连接...")
        
        if len(self.locations) < 2:
            return
        
        # 按距离连接最近的地点
        connected = set()
        paths_created = 0
        
        for loc_a in self.locations:
            # 找到最近的3个地点
            others = [(loc_b, ((loc_a["x"] - loc_b["x"])**2 + (loc_a["y"] - loc_b["y"])**2)**0.5) 
                     for loc_b in self.locations if loc_b["id"] != loc_a["id"]]
            others.sort(key=lambda x: x[1])
            
            for loc_b, dist in others[:3]:  # 只连接最近的3个
                if dist > 600:  # 距离太远不连接
                    continue
                
                # 检查是否已连接
                pair = tuple(sorted([loc_a["id"], loc_b["id"]]))
                if pair in connected:
                    continue
                connected.add(pair)
                
                # 确定路径类型
                if dist < 200:
                    path_type = "ROAD"
                    style = "solid"
                elif dist < 400:
                    path_type = "TRAIL"
                    style = "dashed"
                else:
                    path_type = "SEA_ROUTE"
                    style = "dotted"
                
                response = requests.post(
                    f"{self.base_url}/worlds/{self.world_id}/paths",
                    headers=self.headers,
                    json={
                        "from_location_id": loc_a["id"],
                        "to_location_id": loc_b["id"],
                        "path_type": path_type,
                        "style": style,
                        "color": "#6b7280"
                    }
                )
                
                if response.status_code == 200:
                    paths_created += 1
        
        print(f"✓ 创建 {paths_created} 条路径")
    
    def create_regions(self):
        """创建三大陆区域定义"""
        print("\n🗺️  创建区域...")
        
        regions = [
            {
                "name": "北境冰原",
                "description": "终年积雪的北方大陆，中央有不冻湖，居民以渔猎和贸易为生",
                "region_type": "country",
                "boundary": [
                    {"x": -300, "y": -800}, {"x": 300, "y": -800},
                    {"x": 300, "y": -300}, {"x": -300, "y": -300}
                ],
                "color": "rgba(200, 220, 255, 0.3)",
                "border_color": "#a5c9f5"
            },
            {
                "name": "西部荒漠",
                "description": "广袤的沙漠大陆，点缀着高山和绿洲，以黄金和香料贸易闻名",
                "region_type": "country",
                "boundary": [
                    {"x": -800, "y": -200}, {"x": -300, "y": -200},
                    {"x": -300, "y": 600}, {"x": -800, "y": 600}
                ],
                "color": "rgba(255, 220, 150, 0.3)",
                "border_color": "#f5d0a5"
            },
            {
                "name": "东土绿林",
                "description": "被茂密森林覆盖的大陆，精灵和德鲁伊的家园，拥有古老的智慧",
                "region_type": "country",
                "boundary": [
                    {"x": 300, "y": -200}, {"x": 800, "y": -200},
                    {"x": 800, "y": 600}, {"x": 300, "y": 600}
                ],
                "color": "rgba(150, 255, 150, 0.3)",
                "border_color": "#a5f5a5"
            }
        ]
        
        for region in regions:
            response = requests.post(
                f"{self.base_url}/worlds/{self.world_id}/regions",
                headers=self.headers,
                json=region
            )
            if response.status_code == 200:
                print(f"  ✓ 创建区域: {region['name']}")
    
    def generate(self, world_name: str = "三块大陆的世界", world_desc: str = "包含冰雪北境、沙漠西土、森林东域的宏大世界"):
        """执行完整生成流程"""
        print("=" * 60)
        print("🌍 开始生成三块大陆的世界地图")
        print("=" * 60)
        
        # 1. 创建世界
        self.create_world(world_name, world_desc)
        
        # 2. 生成基础地形
        self.generate_base_map(radius=25, seed=42)
        
        # 3. 重新生成三大陆地形
        north_tiles, west_tiles, east_tiles = self.clear_and_regenerate_continents()
        
        # 4. 创建地点
        self.create_north_continent_locations(north_tiles)
        self.create_west_continent_locations(west_tiles)
        self.create_east_continent_locations(east_tiles)
        
        # 5. 创建路径
        self.create_paths_between_locations()
        
        # 6. 创建区域
        self.create_regions()
        
        print("\n" + "=" * 60)
        print("✅ 世界地图生成完成！")
        print(f"   世界ID: {self.world_id}")
        print(f"   地点数: {len(self.locations)}")
        print(f"   访问: http://localhost:3000/worlds/{self.world_id}/map")
        print("=" * 60)
        
        return self.world_id


def main():
    # 配置 - 从命令行参数或环境变量获取
    import sys
    import os
    
    API_KEY = os.getenv("CLAWLOOM_API_KEY", "your_api_key_here")
    
    if len(sys.argv) > 1:
        API_KEY = sys.argv[1]
    
    # 如果没有提供API Key，使用默认（仅测试）
    if API_KEY == "your_api_key_here":
        API_KEY = "claw_46dc3ef1b5db5288fc07b9cee4d033075fc5e6f98a3115cef576a79ec62c5d0a"
    
    # 创建生成器
    generator = ThreeContinentsGenerator(api_key=API_KEY)
    
    # 执行生成
    try:
        world_id = generator.generate()
        print(f"\n世界已成功创建！ID: {world_id}")
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
