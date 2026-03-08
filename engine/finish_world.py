#!/usr/bin/env python3
"""完成三块大陆世界的创建"""
import requests

API_KEY = 'claw_46dc3ef1b5db5288fc07b9cee4d033075fc5e6f98a3115cef576a79ec62c5d0a'
BASE = 'http://localhost:8000'
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'

# 获取所有地点
map_data = requests.get(f'{BASE}/worlds/{world_id}/map', headers=headers).json()
locations = map_data.get('locations', [])
print(f'Found {len(locations)} locations')

# 创建路径
connected = set()
paths = 0
for loc_a in locations:
    for loc_b in locations:
        if loc_a['id'] >= loc_b['id']:
            continue
        dist = ((loc_a['x'] - loc_b['x'])**2 + (loc_a['y'] - loc_b['y'])**2)**0.5
        if dist < 400:
            pair = tuple(sorted([loc_a['id'], loc_b['id']]))
            if pair in connected:
                continue
            connected.add(pair)
            path_type = 'ROAD' if dist < 200 else 'TRAIL'
            style = 'solid' if dist < 200 else 'dashed'
            r = requests.post(f'{BASE}/worlds/{world_id}/paths', headers=headers, json={
                'from_location_id': loc_a['id'],
                'to_location_id': loc_b['id'],
                'path_type': path_type,
                'style': style
            })
            if r.status_code == 200:
                paths += 1

print(f'Created {paths} paths')

# 创建区域
regions = [
    {'name': 'North Ice Land', 'region_type': 'country', 'boundary': [{'x': -300, 'y': -800}, {'x': 300, 'y': -800}, {'x': 300, 'y': -300}, {'x': -300, 'y': -300}], 'color': 'rgba(200, 220, 255, 0.3)', 'border_color': '#a5c9f5'},
    {'name': 'West Desert', 'region_type': 'country', 'boundary': [{'x': -800, 'y': -200}, {'x': -300, 'y': -200}, {'x': -300, 'y': 600}, {'x': -800, 'y': 600}], 'color': 'rgba(255, 220, 150, 0.3)', 'border_color': '#f5d0a5'},
    {'name': 'East Forest', 'region_type': 'country', 'boundary': [{'x': 300, 'y': -200}, {'x': 800, 'y': -200}, {'x': 800, 'y': 600}, {'x': 300, 'y': 600}], 'color': 'rgba(150, 255, 150, 0.3)', 'border_color': '#a5f5a5'}
]

for region in regions:
    r = requests.post(f'{BASE}/worlds/{world_id}/regions', headers=headers, json=region)
    if r.status_code == 200:
        print(f"Created region: {region['name']}")

print('')
print('=' * 60)
print('WORLD GENERATION COMPLETE!')
print('=' * 60)
print(f'World ID: {world_id}')
print(f'Locations: {len(locations)}')
print(f'Paths: {paths}')
print(f'URL: http://localhost:3000/worlds/{world_id}/map')
print('=' * 60)
