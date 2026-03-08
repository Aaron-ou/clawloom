"""
WorldSeed Engine - Core World Engine
负责推进世界状态，管理 ticks，协调角色决策
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from models_sqlite import (
        WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
        WorldState, Decision, Conflict, ConflictResolution, TickResult,
        WorldStatus, RoleStatus, EventType
    )
except ImportError:
    from models import (
        WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
        WorldState, Decision, Conflict, ConflictResolution, TickResult,
        WorldStatus, RoleStatus, EventType
    )

# 导入核心组件
from .claw_connector import ClawConnector
from .conflict_arbiter import ConflictArbiter
from .event_generator import EventGenerator


class WorldEngine:
    """
    世界引擎核心
    负责推进世界状态，管理 tick 循环
    """
    
    def __init__(
        self,
        db_session: Session,
        claw_connector: Optional[ClawConnector] = None,
        arbiter: Optional[ConflictArbiter] = None,
        event_generator: Optional[EventGenerator] = None
    ):
        self.db = db_session
        self.claw = claw_connector or ClawConnector()
        self.arbiter = arbiter or ConflictArbiter()
        self.event_gen = event_generator or EventGenerator()
    
    async def tick(self, world_id: UUID) -> TickResult:
        """
        推进一个 tick
        
        流程：
        1. 加载世界当前状态
        2. 收集活跃角色的决策
        3. 检测冲突
        4. 解决冲突
        5. 生成事件
        6. 更新角色记忆
        7. 应用世界变更
        8. 保存世界快照
        9. 更新世界 tick
        """
        # 将 UUID 转为字符串以兼容 SQLite
        world_id_str = str(world_id)
        
        # 获取世界
        world = self.db.query(WorldORM).filter(WorldORM.id == world_id_str).first()
        if not world:
            raise ValueError(f"World {world_id} not found")
        
        if world.status != WorldStatus.ACTIVE:
            raise ValueError(f"World {world_id} is not active")
        
        current_tick = world.current_tick
        
        # 1. 加载上一 tick 状态
        previous_state = await self._load_world_state(world_id, current_tick)
        
        # 2. 收集活跃角色
        active_roles = self.db.query(RoleORM).filter(
            RoleORM.world_id == world_id_str,
            RoleORM.status.in_([RoleStatus.ACTIVE, RoleStatus.BUSY])
        ).all()
        
        # 缓存角色信息（用于事件生成）
        roles_info = {r.id: r for r in active_roles}
        
        # 3. 并行请求决策
        decisions = await self._collect_decisions(active_roles, previous_state)
        
        # 4. 检测冲突
        conflicts = self.arbiter.detect_conflicts(decisions)
        
        # 5. 解决冲突
        resolutions = await self.arbiter.resolve_conflicts(conflicts, self.db)
        
        # 6. 应用决策和冲突结果
        world_changes = await self._apply_resolutions(resolutions)
        
        # 7. 生成事件
        events = self.event_gen.generate_events(
            world_id_str, current_tick + 1, decisions, resolutions, roles_info
        )
        
        # 保存事件到数据库
        for event in events:
            self.db.add(event)
        
        # 8. 更新角色记忆
        await self._update_role_memories(resolutions, current_tick + 1)
        
        # 9. 保存新状态快照
        snapshot_data = await self._build_snapshot_dict(world_id_str, current_tick + 1)
        snapshot = WorldSnapshotORM(
            world_id=world_id_str,
            tick=current_tick + 1,
            snapshot=snapshot_data,
            summary=await self.claw.generate_summary(current_tick + 1, events, world_changes)
        )
        self.db.add(snapshot)
        
        # 10. 更新世界 tick
        world.current_tick = current_tick + 1
        world.updated_at = datetime.utcnow()
        
        # 提交事务
        self.db.commit()
        
        # 将EventORM对象转换为字典，用于TickResult
        events_dicts = [
            {
                "id": e.id,
                "world_id": e.world_id,
                "tick": e.tick,
                "type": e.type,
                "title": e.title,
                "description": e.description,
                "participants": e.participants,
                "outcome": e.outcome,
                "is_canon": e.is_canon,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in events
        ]
        
        return TickResult(
            tick=current_tick + 1,
            world_id=world_id,
            decisions=decisions,
            conflicts=conflicts,
            resolutions=resolutions,
            events=events_dicts,
            world_changes=world_changes,
            summary=snapshot.summary
        )
    
    async def run_ticks(self, world_id: UUID, count: int) -> List[TickResult]:
        """连续推进多个 tick"""
        results = []
        
        for i in range(count):
            result = await self.tick(world_id)
            results.append(result)
            
            # 检查是否有需要人类注意的事件
            notable_events = self._check_notable_events(result)
            if notable_events:
                print(f"[注意] Tick {result.tick} 发生重要事件: {notable_events}")
                break
            
            # 小延迟，避免 API 限流
            await asyncio.sleep(0.1)
        
        return results
    
    async def _load_world_state(self, world_id: UUID, tick: int) -> WorldState:
        """加载指定 tick 的世界状态"""
        world_id_str = str(world_id)
        snapshot = self.db.query(WorldSnapshotORM).filter(
            WorldSnapshotORM.world_id == world_id_str,
            WorldSnapshotORM.tick == tick
        ).first()
        
        if snapshot:
            # 将字符串 ID 的数据转为 Pydantic 模型
            data = snapshot.snapshot
            return WorldState(
                tick=data.get("tick", tick),
                world_id=world_id,
                roles=data.get("roles", {}),
                geography=data.get("geography", {}),
                factions=data.get("factions", {}),
                global_events=data.get("global_events", []),
                secrets_status=data.get("secrets_status", {})
            )
        
        # 如果没有快照，构建初始状态
        return WorldState(
            tick=tick,
            world_id=world_id,
            roles={},
            geography={},
            factions={},
            global_events=[],
            secrets_status={}
        )
    
    async def _collect_decisions(
        self,
        roles: List[RoleORM],
        world_state: WorldState
    ) -> List[Decision]:
        """收集所有角色的决策"""
        decisions = []
        
        for role in roles:
            # 构建角色上下文
            context = await self._build_role_context(role)
            
            # 请求决策
            decision = await self.claw.request_decision(role, world_state, context)
            decisions.append(decision)
        
        return decisions
    
    async def _build_role_context(self, role: RoleORM) -> Dict[str, Any]:
        """构建角色上下文"""
        # 获取最近记忆
        recent_memories = self.db.query(RoleMemoryORM).filter(
            RoleMemoryORM.role_id == role.id
        ).order_by(RoleMemoryORM.tick.desc()).limit(10).all()
        
        return {
            "memories": [m.content for m in recent_memories],
            "health": role.health,
            "influence": role.influence
        }
    
    async def _apply_resolutions(
        self,
        resolutions: List[ConflictResolution]
    ) -> Dict[str, Any]:
        """应用冲突解决结果到世界状态"""
        changes = {
            "influence_changes": [],
            "health_changes": [],
            "status_changes": [],
            "location_changes": []
        }
        
        for resolution in resolutions:
            for change in resolution.world_changes:
                if not change:
                    continue
                    
                change_type = change.get("type")
                target_id = change.get("target")
                
                if change_type == "influence_change":
                    changes["influence_changes"].append(change)
                    role = self.db.query(RoleORM).filter(
                        RoleORM.id == target_id
                    ).first()
                    if role:
                        role.influence = max(0, min(100, role.influence + change.get("delta", 0)))
                
                elif change_type == "health_change":
                    changes["health_changes"].append(change)
                    role = self.db.query(RoleORM).filter(
                        RoleORM.id == target_id
                    ).first()
                    if role:
                        role.health = max(0, min(100, role.health + change.get("delta", 0)))
                        # 检查是否死亡
                        if role.health <= 0:
                            role.status = RoleStatus.DECEASED
                            changes["status_changes"].append({
                                "target": target_id,
                                "new_status": "DECEASED"
                            })
                
                elif change_type == "relationship_change":
                    # TODO: 实现关系变更
                    pass
        
        return changes
    
    async def _update_role_memories(
        self,
        resolutions: List[ConflictResolution],
        tick: int
    ):
        """更新角色记忆"""
        for resolution in resolutions:
            for mem_update in resolution.memory_updates:
                if not mem_update:
                    continue
                
                memory = RoleMemoryORM(
                    id=str(uuid4()),
                    role_id=mem_update["role_id"],
                    tick=tick,
                    type="experience",
                    content=mem_update["content"],
                    importance=mem_update.get("importance", 5),
                    created_at=datetime.utcnow()
                )
                self.db.add(memory)
    
    async def _build_snapshot_dict(self, world_id: str, tick: int) -> dict:
        """构建世界状态快照字典（可 JSON 序列化）"""
        roles = self.db.query(RoleORM).filter(RoleORM.world_id == world_id).all()
        
        return {
            "tick": tick,
            "world_id": world_id,
            "roles": {
                r.id: {
                    "name": r.name,
                    "status": r.status,
                    "health": r.health,
                    "influence": r.influence,
                    "location": r.location_id
                }
                for r in roles
            },
            "geography": {},
            "factions": {},
            "global_events": [],
            "secrets_status": {}
        }
    
    def _check_notable_events(self, result: TickResult) -> List[str]:
        """检查是否有需要人类注意的事件"""
        notable = []
        
        for event in result.events:
            event_type = event.type if hasattr(event, 'type') else str(event.type)
            
            if "CONFLICT" in event_type:
                outcome = event.outcome or {}
                if outcome.get("severity") == "critical":
                    notable.append(f"严重冲突: {event.title}")
            
            if "DIVINE" in event_type:
                notable.append(f"神迹事件: {event.title}")
        
        # 检查角色死亡
        for resolution in result.resolutions:
            if resolution.outcome_type == "destruction":
                notable.append(f"角色死亡: {resolution.loser}")
        
        # 检查影响力剧烈变化
        for change in result.world_changes.get("influence_changes", []):
            if abs(change.get("delta", 0)) > 20:
                notable.append(f"影响力剧变: {change.get('target')}")
        
        return notable


# ============================================================================
# 便利函数
# ============================================================================

async def create_world(
    db: Session,
    name: str,
    description: str,
    cosmology: Dict[str, Any],
    genesis_params: Dict[str, Any]
) -> WorldORM:
    """创建新世界"""
    world = WorldORM(
        name=name,
        description=description,
        cosmology=cosmology,
        genesis_params=genesis_params,
        status=WorldStatus.ACTIVE,
        current_tick=0
    )
    db.add(world)
    db.commit()
    db.refresh(world)
    
    # 创建初始快照
    snapshot = WorldSnapshotORM(
        world_id=str(world.id),
        tick=0,
        snapshot={
            "tick": 0,
            "world_id": str(world.id),
            "roles": {},
            "geography": {},
            "factions": {},
            "global_events": [],
            "secrets_status": {}
        },
        summary="世界创世",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    
    return world


async def create_role(
    db: Session,
    world_id: UUID,
    name: str,
    card: Dict[str, Any],
    initial_location: Optional[UUID] = None
) -> RoleORM:
    """创建新角色"""
    role = RoleORM(
        world_id=str(world_id),
        name=name,
        card=card,
        status=RoleStatus.ACTIVE,
        location_id=str(initial_location) if initial_location else None,
        health=100,
        influence=50
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # 创建初始记忆
    memory = RoleMemoryORM(
        id=str(uuid4()),
        role_id=role.id,
        tick=0,
        type="experience",
        content=f"{name} 诞生于世界",
        importance=10,
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    
    return role
