"""
WorldSeed Engine - Main Entry Point
"""

import asyncio
import os
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base
from core.world_engine import (
    WorldEngine, ClawConnector, ConflictArbiter, EventGenerator,
    create_world, create_role
)


# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/worldseed"
)


def init_database():
    """初始化数据库"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("✓ Database initialized")
    return engine


async def demo_run():
    """演示运行"""
    # 初始化数据库
    engine = init_database()
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 创建组件
        claw_connector = ClawConnector()
        arbiter = ConflictArbiter()
        event_generator = EventGenerator()
        
        # 创建世界引擎
        world_engine = WorldEngine(
            db_session=db,
            claw_connector=claw_connector,
            arbiter=arbiter,
            event_generator=event_generator
        )
        
        # 创建演示世界
        world = await create_world(
            db=db,
            name="裂谷三地",
            description="干旱裂谷中的水源争夺",
            cosmology={
                "physics": "低魔中世纪",
                "resource_scarcity": 0.8,
                "climate": "干旱"
            },
            genesis_params={
                "initial_roles": 3,
                "conflict_type": "resource"
            }
        )
        print(f"✓ World created: {world.name} (ID: {world.id})")
        
        # 创建三个角色（使用之前验证的原型角色）
        tieyan = await create_role(
            db=db,
            world_id=world.id,
            name="铁岩",
            card={
                "drives": [
                    {"id": "survival", "description": "保护氏族", "weight": 0.95},
                    {"id": "status", "description": "维护高地地位", "weight": 0.8}
                ],
                "memory": {
                    "public": ["北崖高地氏族领袖"],
                    "private": ["可以控制泉眼闸门"],
                    "traumas": ["父亲被毒杀"]
                },
                "decision_style": {
                    "risk_tolerance": "low",
                    "time_preference": "long_term"
                }
            }
        )
        print(f"✓ Role created: {tieyan.name}")
        
        jinsuanpan = await create_role(
            db=db,
            world_id=world.id,
            name="金算盘",
            card={
                "drives": [
                    {"id": "profit", "description": "利润最大化", "weight": 0.95},
                    {"id": "control", "description": "控制水源", "weight": 0.8}
                ],
                "memory": {
                    "public": ["西丘商会会长"],
                    "private": ["地窖有存水", "与风狼有私生子关系"],
                    "traumas": []
                },
                "decision_style": {
                    "risk_tolerance": "medium",
                    "time_preference": "short_term"
                }
            }
        )
        print(f"✓ Role created: {jinsuanpan.name}")
        
        fenglang = await create_role(
            db=db,
            world_id=world.id,
            name="风狼",
            card={
                "drives": [
                    {"id": "survival", "description": "族人活下去", "weight": 0.95},
                    {"id": "revenge", "description": "对高地的仇恨", "weight": 0.7}
                ],
                "memory": {
                    "public": ["东谷游牧民头领"],
                    "private": ["祖父被高地伏击身亡"],
                    "traumas": ["目睹祖父死亡"]
                },
                "decision_style": {
                    "risk_tolerance": "high",
                    "time_preference": "immediate"
                }
            }
        )
        print(f"✓ Role created: {fenglang.name}")
        
        # 运行5个tick
        print("\n" + "="*50)
        print("Starting simulation...")
        print("="*50 + "\n")
        
        results = await world_engine.run_ticks(world.id, 5)
        
        # 输出结果
        for result in results:
            print(f"\n--- Tick {result.tick} ---")
            print(f"Summary: {result.summary}")
            print(f"Decisions: {len(result.decisions)}")
            print(f"Conflicts: {len(result.conflicts)}")
            print(f"Events: {len(result.events)}")
            
            if result.conflicts:
                print("\nConflicts:")
                for conflict in result.conflicts:
                    print(f"  - {conflict.type}: {conflict.description}")
            
            if result.events:
                print("\nEvents:")
                for event in result.events:
                    print(f"  - {event.type}: {event.title}")
        
        print("\n" + "="*50)
        print("Simulation completed!")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(demo_run())
