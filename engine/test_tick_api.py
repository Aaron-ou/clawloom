#!/usr/bin/env python3
import requests

BASE = "http://localhost:8000"

# 获取世界列表
worlds = requests.get(f'{BASE}/worlds').json()
world_id = worlds[0]['id']
print(f'World ID: {world_id}')

# 测试 tick 详情 API
print('\nTesting tick details API...')
r = requests.get(f'{BASE}/worlds/{world_id}/timeline/0')
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(f"Tick: {data.get('tick')}")
    print(f"Events: {len(data.get('events', []))}")
    print(f"Roles: {len(data.get('roles', []))}")
    print(f"Changes: {len(data.get('world', {}).get('changes_from_previous', []))}")
    
    # 打印第一个事件
    events = data.get('events', [])
    if events:
        print(f"\nFirst event: {events[0].get('title')}")
    
    # 打印第一个角色
    roles = data.get('roles', [])
    if roles:
        print(f"First role: {roles[0].get('name')}")
else:
    print(f'Error: {r.text}')
