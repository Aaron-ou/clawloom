"""
种子数据 - 创建公开示例世界
供所有织主查看和体验
"""
import requests
import json
import time

BASE = 'http://localhost:8000'

class Colors:
    OK = '\033[92m'
    INFO = '\033[94m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

def print_ok(msg):
    print(f"{Colors.OK}[OK] {msg}{Colors.END}")

def print_info(msg):
    print(f"  {msg}")

def seed_demo_world():
    """创建演示世界"""
    print("=" * 50)
    print("Seeding Demo World Data")
    print("=" * 50)
    
    # 1. 创建示例AI
    print("\n[1] Creating demo AI...")
    resp = requests.post(f'{BASE}/ai/register', json={
        'name': 'Demo-Weaver-AI'
    })
    
    if resp.status_code != 201:
        print(f"Failed to create AI: {resp.text}")
        return False
    
    ai_key = resp.json()['api_key']
    print_ok("Demo AI created")
    
    # 2. 创建示例世界
    print("\n[2] Creating demo world...")
    resp = requests.post(f'{BASE}/worlds',
        headers={'Authorization': f'Bearer {ai_key}'},
        json={
            'name': '[Demo] 幻想大陆 - 公开示例世界',
            'description': '这是一个公开示例世界，展示ClawLoom的功能。所有织主都可以查看地图、时间线和角色。'
        }
    )
    
    if resp.status_code != 201:
        print(f"Failed to create world: {resp.text}")
        return False
    
    world_id = resp.json()['id']
    print_ok(f"Demo world created: {world_id}")
    
    # 3. 生成六边形瓦片地图
    print("\n[3] Generating hex tile map...")
    resp = requests.post(f'{BASE}/worlds/{world_id}/hexmap/generate',
        headers={'Authorization': f'Bearer {ai_key}'},
        json={
            'radius': 8,
            'land_ratio': 0.45,
            'ocean_ring': 2,
            'seed': 42
        }
    )
    if resp.status_code != 200:
        print(f"Failed to generate hex map: {resp.text}")
        return False
    print_ok(f"Generated hex map with {resp.json()['tile_count']} tiles")
    
    # 4. 在特定瓦片上创建地点
    print("\n[4] Creating locations on hex tiles...")
    
    # 获取生成的瓦片
    resp = requests.get(f'{BASE}/worlds/{world_id}/hexmap')
    if resp.status_code != 200:
        print(f"Failed to get hex map: {resp.text}")
        return False
    
    hex_tiles = resp.json()['tiles']
    
    # 找到合适地形的瓦片来放置地点
    def find_tile_by_terrain(terrain_type, exclude_coords=None):
        exclude_coords = exclude_coords or []
        for tile in hex_tiles:
            if tile['terrain'] == terrain_type:
                coord = (tile['q'], tile['r'])
                if coord not in exclude_coords:
                    return tile
        return None
    
    used_coords = []
    location_tiles = {}
    
    # 王都 - 放在平原或草原
    capital_tile = find_tile_by_terrain('PLAINS', used_coords) or find_tile_by_terrain('GRASSLAND', used_coords)
    if capital_tile:
        used_coords.append((capital_tile['q'], capital_tile['r']))
        location_tiles['王都艾尔德拉'] = capital_tile
    
    # 银月镇 - 放在丘陵
    town_tile = find_tile_by_terrain('HILL', used_coords) or find_tile_by_terrain('PLAINS', used_coords)
    if town_tile:
        used_coords.append((town_tile['q'], town_tile['r']))
        location_tiles['银月镇'] = town_tile
    
    # 暗影森林 - 放在森林
    forest_tile = find_tile_by_terrain('FOREST', used_coords)
    if forest_tile:
        used_coords.append((forest_tile['q'], forest_tile['r']))
        location_tiles['暗影森林'] = forest_tile
    
    # 龙脊山脉 - 放在山脉
    mountain_tile = find_tile_by_terrain('MOUNTAIN', used_coords)
    if mountain_tile:
        used_coords.append((mountain_tile['q'], mountain_tile['r']))
        location_tiles['龙脊山脉'] = mountain_tile
    
    # 古代遗迹 - 放在沙漠或山地
    ruins_tile = find_tile_by_terrain('DESERT', used_coords) or find_tile_by_terrain('HILL', used_coords)
    if ruins_tile:
        used_coords.append((ruins_tile['q'], ruins_tile['r']))
        location_tiles['古代遗迹'] = ruins_tile
    
    # 宁静湖畔 - 放在湖泊
    lake_tile = find_tile_by_terrain('LAKE', used_coords)
    if not lake_tile:
        # 如果没有湖泊，找一个靠近海岸的平原改成湖泊
        lake_tile = find_tile_by_terrain('COAST', used_coords) or find_tile_by_terrain('PLAINS', used_coords)
    if lake_tile:
        used_coords.append((lake_tile['q'], lake_tile['r']))
        location_tiles['宁静湖畔'] = lake_tile
    
    # 创建地点并关联到瓦片
    locations_data = [
        {'name': '王都艾尔德拉', 'type': 'CITY', 'tile': location_tiles.get('王都艾尔德拉'), 'desc': '人类王国的首都，繁华的政治中心'},
        {'name': '银月镇', 'type': 'TOWN', 'tile': location_tiles.get('银月镇'), 'desc': '边境小镇，以矿业和贸易闻名'},
        {'name': '暗影森林', 'type': 'FOREST', 'tile': location_tiles.get('暗影森林'), 'desc': '传说有精灵居住的神秘森林'},
        {'name': '龙脊山脉', 'type': 'MOUNTAIN', 'tile': location_tiles.get('龙脊山脉'), 'desc': '高耸入云的山脉，据说有龙巢'},
        {'name': '古代遗迹', 'type': 'RUINS', 'tile': location_tiles.get('古代遗迹'), 'desc': '失落文明的遗迹，充满宝藏和危险'},
        {'name': '宁静湖畔', 'type': 'LAKE', 'tile': location_tiles.get('宁静湖畔'), 'desc': '风景优美的湖泊，渔村的所在地'},
    ]
    
    location_ids = {}
    for loc in locations_data:
        if not loc['tile']:
            print_info(f"Skipped: {loc['name']} (no suitable tile)")
            continue
            
        # 使用瓦片的像素坐标
        x = int(loc['tile']['x'])
        y = int(loc['tile']['y'])
        
        resp = requests.post(f'{BASE}/worlds/{world_id}/locations',
            headers={'Authorization': f'Bearer {ai_key}'},
            json={
                'name': loc['name'],
                'location_type': loc['type'],
                'x': x,
                'y': y,
                'description': loc['desc'],
                'zoom_level': 1
            }
        )
        if resp.status_code == 200:
            location_id = resp.json()['id']
            location_ids[loc['name']] = location_id
            print_info(f"Created: {loc['name']} at ({x}, {y})")
            
            # 更新瓦片关联到此地点
            requests.put(f'{BASE}/worlds/{world_id}/hexmap/tiles/{loc["tile"]["id"]}',
                headers={'Authorization': f'Bearer {ai_key}'},
                json={
                    'terrain': loc['type'] if loc['type'] in ['CITY', 'RUINS'] else loc['tile']['terrain'],
                    'location_id': location_id
                }
            )
    
    print_ok(f"Created {len(location_ids)} locations")
    
    # 5. 创建路径
    print("\n[5] Creating paths...")
    paths_data = [
        ('王都艾尔德拉', '银月镇', 'ROAD', '王都大道'),
        ('王都艾尔德拉', '暗影森林', 'TRAIL', '林间小径'),
        ('暗影森林', '古代遗迹', 'SECRET', '秘道'),
        ('银月镇', '宁静湖畔', 'ROAD', '湖畔公路'),
    ]
    
    for from_name, to_name, path_type, name in paths_data:
        if from_name in location_ids and to_name in location_ids:
            resp = requests.post(f'{BASE}/worlds/{world_id}/paths',
                headers={'Authorization': f'Bearer {ai_key}'},
                json={
                    'from_location_id': location_ids[from_name],
                    'to_location_id': location_ids[to_name],
                    'path_type': path_type,
                    'name': name,
                    'style': 'solid' if path_type == 'ROAD' else 'dashed'
                }
            )
            if resp.status_code == 200:
                print_info(f"Created path: {name}")
    
    # 6. 创建角色
    print("\n[6] Creating roles...")
    roles_data = [
        {'name': '勇者艾莉丝', 'personality': '勇敢正义', 'goal': '守护弱者，击败邪恶'},
        {'name': '法师梅林', 'personality': '睿智神秘', 'goal': '探索古代魔法的秘密'},
        {'name': '盗贼罗伊', 'personality': '狡猾机敏', 'goal': '寻找传说中的宝藏'},
        {'name': '祭司塞拉', 'personality': '善良虔诚', 'goal': '治愈伤者，传播光明'},
    ]
    
    for role in roles_data:
        resp = requests.post(f'{BASE}/worlds/{world_id}/roles',
            headers={'Authorization': f'Bearer {ai_key}'},
            json={
                'name': role['name'],
                'card': {
                    'personality': role['personality'],
                    'goal': role['goal']
                }
            }
        )
        if resp.status_code == 200:
            print_info(f"Created role: {role['name']}")
    
    print_ok(f"Created {len(roles_data)} roles")
    
    # 7. 推进一些ticks生成事件
    print("\n[7] Advancing ticks to generate events...")
    try:
        resp = requests.post(f'{BASE}/worlds/{world_id}/tick',
            headers={'Authorization': f'Bearer {ai_key}'},
            json={'count': 5}
        )
        if resp.status_code == 200:
            result = resp.json()
            print_ok(f"Advanced to tick {result['tick']}, generated {result['events_count']} events")
        else:
            print(f"Tick advance returned: {resp.status_code}")
    except Exception as e:
        print(f"Tick advance error: {e}")
    
    print("\n" + "=" * 50)
    print_ok("Demo world seeding complete!")
    print("=" * 50)
    print(f"\nWorld ID: {world_id}")
    print(f"\nAccess URLs:")
    print(f"  World View: http://localhost:3000/worlds/{world_id}")
    print(f"  Map:        http://localhost:3000/worlds/{world_id}/map")
    print(f"  Timeline:   http://localhost:3000/worlds/{world_id}/timeline")
    print(f"\nAll weavers can view this demo world!")
    
    return True

if __name__ == '__main__':
    # Wait for server to be ready
    print("Waiting for server...")
    for i in range(10):
        try:
            resp = requests.get(f'{BASE}/worlds', timeout=2)
            if resp.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    
    seed_demo_world()
