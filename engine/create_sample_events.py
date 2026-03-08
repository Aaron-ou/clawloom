#!/usr/bin/env python3
"""手动创建示例事件数据用于展示"""
import sys
import os
sys.path.insert(0, 'engine')

# 设置数据库
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_sqlite import Base, EventORM, WorldSnapshotORM, RoleORM, WorldORM
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'clawloom.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

world_id = 'bb9a66f3-87a9-4558-8a77-ede9a9835d69'
db = SessionLocal()

print("Creating sample events...")

# 获取角色
roles = db.query(RoleORM).filter(RoleORM.world_id == world_id).all()
role_names = [r.name for r in roles]
print(f"Found {len(roles)} roles: {role_names}")

# 创建示例事件
sample_events = [
    {
        "tick": 1,
        "type": "discovery",
        "title": "Ancient Ruins Discovered",
        "description": "Alice the Brave discovered ancient ruins in the northern mountains. Strange magical energy emanates from within.",
        "participants": ["Alice the Brave"],
        "outcome": {"location_revealed": "Ancient Ruins", "quest_triggered": "explore_ruins"}
    },
    {
        "tick": 2,
        "type": "interaction",
        "title": "Meeting at the Tavern",
        "description": "Merlin the Wise and Sarah the Priest met at the local tavern. They discussed the recent magical disturbances in the forest.",
        "participants": ["Merlin the Wise", "Sarah the Priest"],
        "outcome": {"relationship": "friendly", "information_shared": "magic_disturbance"}
    },
    {
        "tick": 3,
        "type": "conflict",
        "title": "Bandit Ambush",
        "description": "Roy the Rogue was ambushed by bandits on the eastern road. He managed to escape but lost some supplies.",
        "participants": ["Roy the Rogue"],
        "outcome": {"health_change": -15, "items_lost": ["food", "gold"]}
    },
    {
        "tick": 4,
        "type": "decision",
        "title": "Alliance Formed",
        "description": "Alice, Merlin, and Sarah decided to form an alliance to investigate the ancient ruins together.",
        "participants": ["Alice the Brave", "Merlin the Wise", "Sarah the Priest"],
        "outcome": {"party_formed": "Ruins Expedition Team", "quest_accepted": "explore_ruins"}
    },
    {
        "tick": 5,
        "type": "discovery",
        "title": "Magical Artifact Found",
        "description": "The expedition team discovered a glowing crystal artifact deep within the ruins. It pulses with ancient power.",
        "participants": ["Alice the Brave", "Merlin the Wise", "Sarah the Priest"],
        "outcome": {"item_acquired": "Ancient Crystal", "magic_level_increase": 10}
    },
]

for event_data in sample_events:
    event = EventORM(
        world_id=world_id,
        tick=event_data["tick"],
        type=event_data["type"],
        title=event_data["title"],
        description=event_data["description"],
        participants=event_data["participants"],
        outcome=event_data["outcome"],
        created_at=datetime.utcnow()
    )
    db.add(event)
    print(f"  Created event: {event_data['title']} (Tick {event_data['tick']})")

# 创建快照
for tick in range(1, 6):
    snapshot = WorldSnapshotORM(
        world_id=world_id,
        tick=tick,
        snapshot={
            "roles": [{"id": r.id, "name": r.name, "status": r.status, "health": r.health} for r in roles],
            "tick": tick
        },
        summary=f"Tick {tick}: World continues to evolve. {len([e for e in sample_events if e['tick'] == tick])} major events occurred.",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    print(f"  Created snapshot for Tick {tick}")

# 更新世界的当前 tick
world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
if world:
    world.current_tick = 5
    print(f"  Updated world current_tick to 5")

db.commit()
db.close()

print("\nSample data created successfully!")
print(f"URL: http://localhost:3000/worlds/{world_id}/timeline")
