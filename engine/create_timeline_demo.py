#!/usr/bin/env python3
import requests
import json

API_KEY = 'claw_46dc3ef1b5db5288fc07b9cee4d033075fc5e6f98a3115cef576a79ec62c5d0a'
BASE = 'http://localhost:8000'
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'

print("Creating timeline demo data...")
print("=" * 50)

# 1. Create roles
print("\n1. Creating roles...")
roles = [
    {"name": "Alice the Brave", "card": {"personality": "brave", "goal": "protect the weak", "avatar": "🗡️"}},
    {"name": "Merlin the Wise", "card": {"personality": "wise", "goal": "discover ancient magic", "avatar": "🧙"}},
    {"name": "Roy the Rogue", "card": {"personality": "cunning", "goal": "find legendary treasure", "avatar": "🗡️"}},
    {"name": "Sarah the Priest", "card": {"personality": "kind", "goal": "heal the wounded", "avatar": "✨"}},
]

created_roles = []
for role_data in roles:
    r = requests.post(f'{BASE}/worlds/{world_id}/roles', headers=headers, json=role_data)
    if r.status_code == 200:
        role = r.json()
        created_roles.append(role)
        print(f"  Created: {role['name']}")

print(f"\nTotal roles: {len(created_roles)}")

# 2. Advance ticks
print("\n2. Advancing world (5 ticks)...")
for i in range(5):
    r = requests.post(f'{BASE}/worlds/{world_id}/tick', headers=headers, json={'count': 1})
    if r.status_code == 200:
        result = r.json()
        print(f"  Tick {i+1}: {result.get('events_count', 0)} events, {result.get('decisions_count', 0)} decisions")
        if result.get('summary'):
            print(f"    Summary: {result['summary'][:50]}...")
    else:
        print(f"  Error: {r.status_code}")

# 3. Check timeline
print("\n3. Checking timeline...")
r = requests.get(f'{BASE}/worlds/{world_id}/timeline')
if r.status_code == 200:
    timeline = r.json()
    print(f"  Current tick: {timeline.get('current_tick')}")
    print(f"  Snapshots: {len(timeline.get('timeline', []))}")

# 4. Check tick details
print("\n4. Checking Tick #1 details...")
r = requests.get(f'{BASE}/worlds/{world_id}/timeline/1')
if r.status_code == 200:
    details = r.json()
    print(f"  Events: {len(details.get('events', []))}")
    print(f"  Roles: {len(details.get('roles', []))}")
    print(f"  Changes: {len(details.get('world', {}).get('changes_from_previous', []))}")
    
    events = details.get('events', [])
    if events:
        print("\n  Event list:")
        for event in events[:3]:
            print(f"    - [{event.get('type', 'unknown')}] {event.get('title', 'Untitled')}")

print("\n" + "=" * 50)
print("Demo data created!")
print(f"URL: http://localhost:3000/worlds/{world_id}/timeline")
