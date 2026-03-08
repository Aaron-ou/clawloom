#!/usr/bin/env python3
import requests

BASE = 'http://localhost:8000'
world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'

print("Timeline API Test")
print("=" * 50)

# 1. Get timeline overview
print("\n1. Timeline Overview:")
r = requests.get(f'{BASE}/worlds/{world_id}/timeline')
if r.status_code == 200:
    data = r.json()
    print(f"   Current Tick: {data.get('current_tick')}")
    print(f"   Snapshots: {len(data.get('timeline', []))}")
    for snap in data.get('timeline', [])[:3]:
        print(f"   - Tick #{snap['tick']}: {snap.get('event_count', 0)} events")

# 2. Get Tick #3 details
print("\n2. Tick #3 Details:")
r = requests.get(f'{BASE}/worlds/{world_id}/timeline/3')
if r.status_code == 200:
    data = r.json()
    print(f"   Events: {len(data.get('events', []))}")
    print(f"   Roles: {len(data.get('roles', []))}")
    print(f"   Changes: {len(data.get('world', {}).get('changes_from_previous', []))}")
    
    print("\n   Events:")
    for event in data.get('events', []):
        print(f"     - [{event.get('type')}] {event.get('title')}")
    
    print("\n   Roles:")
    for role in data.get('roles', [])[:3]:
        print(f"     - {role.get('name')} (HP: {role.get('health')}, Status: {role.get('status')})")

print("\n" + "=" * 50)
print(f"URL: http://localhost:3000/worlds/{world_id}/timeline")
