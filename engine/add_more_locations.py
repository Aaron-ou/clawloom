#!/usr/bin/env python3
import requests
import random

API_KEY = 'claw_46dc3ef1b5db5288fc07b9cee4d033075fc5e6f98a3115cef576a79ec62c5d0a'
BASE = 'http://localhost:8000'
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'

# 获取地图数据
hex_data = requests.get(f'{BASE}/worlds/{world_id}/hexmap', headers=headers).json()
tiles = hex_data['tiles']

# 分类
west = [t for t in tiles if t['q'] < -5 and t['r'] >= -5]
desert_tiles = [t for t in west if t['terrain'] == 'DESERT']
swamp_tiles = [t for t in west if t['terrain'] == 'SWAMP']
mtn_tiles = [t for t in west if t['terrain'] == 'MOUNTAIN']
hill_tiles = [t for t in west if t['terrain'] == 'HILL']

print(f"West continent tiles: {len(west)}")
print(f"  Desert: {len(desert_tiles)}")
print(f"  Swamp/Oasis: {len(swamp_tiles)}")
print(f"  Mountain: {len(mtn_tiles)}")
print(f"  Hill: {len(hill_tiles)}")

locations_added = []

def create_loc(tile, name, loc_type, desc, icon):
    loc_r = requests.post(f'{BASE}/worlds/{world_id}/locations', headers=headers, json={
        'name': name, 'description': desc, 'location_type': loc_type,
        'x': int(tile['x']), 'y': int(tile['y']), 'icon': icon
    })
    if loc_r.status_code == 200:
        loc = loc_r.json()
        tile_id = tile['id']
        requests.put(f'{BASE}/worlds/{world_id}/hexmap/tiles/{tile_id}', headers=headers, json={
            'terrain': loc_type if loc_type in ['CITY', 'CASTLE'] else tile['terrain'],
            'location_id': loc['id']
        })
        locations_added.append(name)
        print(f"Created: {name}")
        return True
    return False

# 为西大陆添加更多地点
print("\nAdding more locations to West (Desert) continent...")

# 3. 另一个沙漠城镇
if len(desert_tiles) > 5:
    create_loc(desert_tiles[2], "Sandstone City", "TOWN", 
               "Built from golden sandstone, a wealthy trade hub", "🏛️")

# 4. 另一个绿洲
if len(swamp_tiles) > 1:
    create_loc(swamp_tiles[1], "Mirage Oasis", "VILLAGE", 
               "Hidden oasis surrounded by palm trees", "🌴")

# 5. 山地矿镇
if len(mtn_tiles) > 1:
    create_loc(mtn_tiles[1], "Iron Peak Mine", "TOWN", 
               "Mining town extracting precious metals from the mountains", "⛏️")

# 为北大陆补充更多地点
print("\nAdding more to North (Ice) continent...")
north = [t for t in tiles if t['r'] < -5]
snow_tiles = [t for t in north if t['terrain'] == 'SNOW']
tundra_tiles = [t for t in north if t['terrain'] == 'TUNDRA']

if len(snow_tiles) > 5:
    create_loc(snow_tiles[4], "Frost Village", "VILLAGE", 
               "Small village of ice fishermen", "🏘️")

if len(tundra_tiles) > 2:
    create_loc(tundra_tiles[2], "Northern Light Camp", "CAMP", 
               "Research camp studying the aurora", "🔭")

# 为东大陆补充
print("\nAdding more to East (Forest) continent...")
east = [t for t in tiles if t['q'] > 5 and t['r'] >= -5]
forest_tiles = [t for t in east if t['terrain'] == 'FOREST']
jungle_tiles = [t for t in east if t['terrain'] == 'JUNGLE']

if len(forest_tiles) > 5:
    create_loc(forest_tiles[4], "Whispering Woods", "VILLAGE", 
               "Village where trees are said to speak", "🌲")

if len(jungle_tiles) > 1:
    create_loc(jungle_tiles[1], "Ruins of Eldoria", "RUINS", 
               "Ancient ruins hidden deep in the jungle", "🏛️")

print(f"\nAdded {len(locations_added)} new locations")
print(f"Total locations should now be: {10 + len(locations_added)}")
