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
        print(f"Created: {name}")
        return True
    return False

# 北大陆补充2个
print("Adding to North continent...")
north = [t for t in tiles if t['r'] < -5]
snow_tiles = [t for t in north if t['terrain'] == 'SNOW']
mtn_north = [t for t in north if t['terrain'] == 'MOUNTAIN']

if len(snow_tiles) > 3:
    create_loc(random.choice(snow_tiles[2:]), "Icewind Camp", "CAMP", 
               "Trading camp for ice merchants", "⛺")
if len(mtn_north) > 1:
    create_loc(random.choice(mtn_north[1:]), "Crystal Cave", "DUNGEON", 
               "Ice crystal cave with mysterious energy", "💎")

# 西大陆补充2个
print("Adding to West continent...")
west = [t for t in tiles if t['q'] < -5 and t['r'] >= -5]
desert_tiles = [t for t in west if t['terrain'] == 'DESERT']
hill_tiles = [t for t in west if t['terrain'] == 'HILL']

if len(desert_tiles) > 3:
    create_loc(random.choice(desert_tiles[3:]), "Nomad Tent City", "VILLAGE", 
               "Mobile settlement of desert nomads", "🏕️")
if len(hill_tiles) > 3:
    create_loc(random.choice(hill_tiles[3:]), "Scorpion Den", "CAMP", 
               "Outlaw hideout in the rocky hills", "🦂")

# 东大陆补充1个
print("Adding to East continent...")
east = [t for t in tiles if t['q'] > 5 and t['r'] >= -5]
forest_tiles = [t for t in east if t['terrain'] == 'FOREST']
plains_tiles = [t for t in east if t['terrain'] == 'PLAINS']

if len(plains_tiles) > 0:
    create_loc(plains_tiles[0], "Meadowbrook", "VILLAGE", 
               "Peaceful village in forest clearings", "🏡")

print("\nDone! Each continent should now have 5+ locations.")
