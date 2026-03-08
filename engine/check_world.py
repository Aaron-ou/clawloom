#!/usr/bin/env python3
import requests

API_KEY = 'claw_46dc3ef1b5db5288fc07b9cee4d033075fc5e6f98a3115cef576a79ec62c5d0a'
BASE = 'http://localhost:8000'
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'

# 获取现有地图数据
map_data = requests.get(f'{BASE}/worlds/{world_id}/map', headers=headers).json()
hex_data = requests.get(f'{BASE}/worlds/{world_id}/hexmap', headers=headers).json()

locations = map_data.get('locations', [])
tiles = hex_data['tiles']

print(f"Total locations: {len(locations)}")
print(f"Total tiles: {len(tiles)}")

# 按区域统计
north_count = sum(1 for l in locations if l['y'] < -150)
west_count = sum(1 for l in locations if l['x'] < -150 and l['y'] >= -150)
east_count = sum(1 for l in locations if l['x'] > 150 and l['y'] >= -150)

print(f"\nNorth (Ice) locations: {north_count}")
print(f"West (Desert) locations: {west_count}")
print(f"East (Forest) locations: {east_count}")

print("\nAll locations:")
for l in locations:
    print(f"  - {l['name']} ({l['location_type']}) at ({l['x']}, {l['y']})")
