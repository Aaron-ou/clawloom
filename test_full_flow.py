#!/usr/bin/env python3
"""ClawLoom 完整流程测试"""
import requests
import json

BASE = 'http://localhost:8000'

def test():
    # 1. AI注册
    print('=== 1. AI注册 ===')
    resp = requests.post(f'{BASE}/ai/register', json={'name': '测试AI-阿尔法'})
    print(f'Status: {resp.status_code}')
    data = resp.json()
    ai_key = data.get('api_key')
    print(f"AI Key: {ai_key[:30]}...")
    
    # 2. 织主注册
    print('\n=== 2. 织主注册 ===')
    resp = requests.post(f'{BASE}/auth/register', json={
        'username': 'test_weaver',
        'password': 'testpass123'
    })
    print(f'Status: {resp.status_code}')
    reg_data = resp.json()
    weaver_token = reg_data.get('access_token')
    print(f"Token: {weaver_token[:30]}...")
    
    # 3. 织主绑定AI
    print('\n=== 3. 织主绑定AI ===')
    resp = requests.post(f'{BASE}/weaver/bind', 
        headers={'Authorization': f'Bearer {weaver_token}'},
        json={'ai_key': ai_key, 'ai_name': '我的小阿尔法'}
    )
    print(f'Status: {resp.status_code}')
    bind_data = resp.json()
    print(f"Binding ID: {bind_data.get('binding_id')}")
    
    # 4. AI创建世界
    print('\n=== 4. AI创建世界 ===')
    resp = requests.post(f'{BASE}/worlds', 
        headers={'Authorization': f'Bearer {ai_key}'},
        json={
            'name': '测试世界-阿尔法',
            'description': '这是AI创造的第一个世界'
        }
    )
    print(f'Status: {resp.status_code}')
    world = resp.json()
    world_id = world.get('id')
    print(f"World ID: {world_id}")
    
    # 5. 创建多个角色
    print('\n=== 5. 创建角色 ===')
    roles = []
    for name, personality in [('勇者小明', '勇敢'), ('法师小红', '智慧'), ('盗贼小黑', '狡猾')]:
        resp = requests.post(f'{BASE}/worlds/{world_id}/roles',
            headers={'Authorization': f'Bearer {ai_key}'},
            json={
                'name': name,
                'card': {'personality': personality, 'goal': '探索世界'}
            }
        )
        if resp.status_code == 200:
            roles.append(resp.json())
            print(f"  Created: {name}")
    
    # 6. 推进20个tick
    print('\n=== 6. 推进20个tick ===')
    resp = requests.post(f'{BASE}/worlds/{world_id}/tick',
        headers={'Authorization': f'Bearer {ai_key}'},
        json={'count': 20}
    )
    print(f'Status: {resp.status_code}')
    result = resp.json()
    summary = result.get('summary', 'N/A')
    print(f"Summary: {summary[:100]}...")
    print(f"Events count: {result.get('events_count')}")
    print(f"Current tick: {result.get('tick')}")
    
    # 7. 获取世界状态
    print('\n=== 7. 获取世界状态 ===')
    resp = requests.get(f'{BASE}/worlds/{world_id}',
        headers={'Authorization': f'Bearer {ai_key}'}
    )
    world_state = resp.json()
    print(f"Name: {world_state.get('name')}")
    print(f"Current Tick: {world_state.get('current_tick')}")
    print(f"Status: {world_state.get('status')}")
    
    # 8. 获取事件列表
    print('\n=== 8. 获取事件列表 ===')
    resp = requests.get(f'{BASE}/worlds/{world_id}/events',
        headers={'Authorization': f'Bearer {ai_key}'}
    )
    events = resp.json()
    print(f"Total events: {len(events)}")
    for e in events[:5]:
        print(f"  Tick {e.get('tick')}: [{e.get('type')}] {e.get('title')}")
    
    # 9. 获取时间线
    print('\n=== 9. 获取时间线 ===')
    resp = requests.get(f'{BASE}/worlds/{world_id}/timeline',
        headers={'Authorization': f'Bearer {ai_key}'}
    )
    timeline = resp.json()
    print(f"Snapshots: {len(timeline.get('timeline', []))}")
    
    print('\n=== 测试完成！ ===')
    print(f'世界 {world_id} 已成功运行 {world_state.get("current_tick")} 个tick')
    print(f'共生成 {len(events)} 个事件')

if __name__ == '__main__':
    test()
