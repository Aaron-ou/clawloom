"""
WorldSeed Engine - Core World Engine
Responsible for advancing world state, managing ticks, and coordinating role decisions.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus, EventType
)


class ClawConnector:
    """
    连接Claw服务的接口
    实际实现会通过HTTP调用OpenClaw或其他LLM服务
    """
    
    async def request_decision(
        self,
        role: RoleORM,
        world_state: WorldState,
        context: Dict[str, Any]
    ) -> Decision:
        """
        向Claw请求角色决策
        
        实际实现：
        1. 构建包含角色卡、记忆、世界状态的prompt
        2. 调用OpenClaw API
        3. 解析返回的决策
        """
        # TODO: 实现实际的Claw调用
        # 这里先返回一个模拟决策用于测试
        return Decision(
            role_id=role.id,
            tick=world_state.tick,
            thought=f"{role.name}正在思考当前局势...",
            action={
                "type": "observe",
                "target": None,
                "details": "观察周围环境"
            },
            dialogue=None
        )
    
    async def generate_summary(
        self,
        tick: int,
        events: List[EventORM],
        world_changes: Dict[str, Any]
    ) -> str:
        """生成tick摘要"""
        # TODO: 调用Claw生成人类可读摘要
        return f"第{tick}轮：世界继续运转"


class ConflictArbiter:
    """
    冲突检测与仲裁器
    检测角色决策之间的冲突，并裁决结果
    """
    
    def detect_conflicts(self, decisions: List[Decision]) -> List[Conflict]:
        """
        检测决策之间的冲突
        
        冲突类型：
        1. resource: 争夺同一资源
        2. stealth_vs_detection: 秘密行动 vs 侦察
        3. betrayal: 欺骗/背叛
        4. confrontation: 直接对抗
        """
        conflicts = []
        
        for i, dec1 in enumerate(decisions):
            for dec2 in decisions[i+1:]:
                conflict = self._check_pair_conflict(dec1, dec2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_pair_conflict(self, dec1: Decision, dec2: Decision) -> Optional[Conflict]:
        """检查两个决策是否冲突"""
        
        # 检查是否争夺同一目标
        if dec1.target and dec2.target and dec1.target == dec2.target:
            if dec1.action.get("type") in ["attack", "seize", "claim"] and \
               dec2.action.get("type") in ["defend", "protect", "claim"]:
                return Conflict(
                    type="resource",
                    parties=[dec1.role_id, dec2.role_id],
                    description=f"{dec1.role_id} 和 {dec2.role_id} 争夺同一目标",
                    stakes=str(dec1.target),
                    severity="serious"
                )
        
        # 检查欺骗 vs 侦察
        if dec1.action.get("type") == "stealth" and dec2.action.get("type") == "detect":
            if dec1.target == dec2.role_id or dec2.target == dec1.role_id:
                return Conflict(
                    type="stealth_vs_detection",
                    parties=[dec1.role_id, dec2.role_id],
                    description="秘密行动可能被察觉",
                    stakes="秘密暴露",
                    severity="normal"
                )
        
        return None
    
    async def resolve_conflicts(
        self,
        conflicts: List[Conflict],
        db: Session
    ) -> List[ConflictResolution]:
        """
        解决冲突
        
        简单实现：基于实力和随机因素
        复杂实现：可以调用Claw模拟对抗过程
        """
        resolutions = []
        
        for conflict in conflicts:
            resolution = await self._resolve_single_conflict(conflict, db)
            resolutions.append(resolution)
        
        return resolutions
    
    async def _resolve_single_conflict(
        self,
        conflict: Conflict,
        db: Session
    ) -> ConflictResolution:
        """解决单个冲突"""
        
        # 获取冲突双方的角色信息
        roles = db.query(RoleORM).filter(RoleORM.id.in_(conflict.parties)).all()
        
        # 简化逻辑：比较influence + random
        import random
        
        role_powers = {r.id: r.influence + random.randint(-20, 20) for r in roles}
        
        if len(role_powers) >= 2:
            sorted_roles = sorted(role_powers.items(), key=lambda x: x[1], reverse=True)
            winner_id = sorted_roles[0][0]
            loser_id = sorted_roles[1][0] if len(sorted_roles) > 1 else None
        else:
            winner_id = list(role_powers.keys())[0] if role_powers else None
            loser_id = None
        
        # 根据冲突类型决定结果
        if conflict.type == "resource":
            outcome = "victory" if winner_id else "compromise"
        elif conflict.type == "stealth_vs_detection":
            outcome = "detected" if winner_id == conflict.parties[1] else "undetected"
        else:
            outcome = "compromise"
        
        return ConflictResolution(
            conflict_id=conflict.id,
            outcome_type=outcome,
            winner=winner_id,
            loser=loser_id,
            description=f"冲突解决：{outcome}",
            world_changes=[
                {"type": "influence_change", "target": winner_id, "delta": 10},
                {"type": "influence_change", "target": loser_id, "delta": -10} if loser_id else None
            ],
            memory_updates=[
                {"role_id": winner_id, "content": f"在冲突中战胜了对手"},
                {"role_id": loser_id, "content": f"在冲突中失利"} if loser_id else None
            ]
        )


class EventGenerator:
    """
    事件生成器
    将决策和冲突结果转化为世界事件
    """
    
    def generate_events(
        self,
        world_id: UUID,
        tick: int,
        decisions: List[Decision],
        resolutions: List[ConflictResolution],
        db: Session
    ) -> List[EventORM]:
        """生成事件"""
        events = []
        
        # 为每个重要决策生成事件
        for decision in decisions:
            if decision.action.get("type") in ["attack", "negotiate", "discover", "move"]:
                event = EventORM(
                    world_id=world_id,
                    tick=tick,
                    type=self._map_action_to_event_type(decision.action["type"]),
                    title=f"{decision.role_id}的{decision.action['type']}",
                    description=decision.thought[:200],
                    participants=[decision.role_id],
                    outcome={"action": decision.action},
                    is_canon=True
                )
                events.append(event)
        
        # 为冲突生成事件
        for resolution in resolutions:
            if resolution.outcome_type in ["victory", "destruction", "exposed"]:
                event = EventORM(
                    world_id=world_id,
                    tick=tick,
                    type=EventType.CONFLICT,
                    title=f"冲突：{resolution.outcome_type}",
                    description=resolution.description,
                    participants=[resolution.winner, resolution.loser] if resolution.loser else [resolution.winner],
                    outcome={"resolution": resolution.outcome_type},
                    is_canon=True
                )
                events.append(event)
        
        return events
    
    def _map_action_to_event_type(self, action_type: str) -> EventType:
        """映射行动类型到事件类型"""
        mapping = {
            "attack": EventType.CONFLICT,
            "negotiate": EventType.NEGOTIATION,
            "discover": EventType.DISCOVERY,
            "move": EventType.MOVEMENT,
            "speak": EventType.COMMUNICATION
        }
        return mapping.get(action_type, EventType.NATURAL)


class WorldEngine:
    """
    世界引擎核心
    负责推进世界状态，管理tick循环
    """
    
    def __init__(
        self,
        db_session: Session,
        claw_connector: ClawConnector,
        arbiter: ConflictArbiter,
        event_generator: EventGenerator
    ):
        self.db = db_session
        self.claw = claw_connector
        self.arbiter = arbiter
        self.event_gen = event_generator
    
    async def tick(self, world_id: UUID) -> TickResult:
        """
        推进一个tick
        
        流程：
        1. 加载世界当前状态
        2. 收集活跃角色的决策
        3. 检测冲突
        4. 解决冲突
        5. 生成事件
        6. 更新角色记忆
        7. 保存世界快照
        8. 更新世界tick
        """
        # 获取世界
        world = self.db.query(WorldORM).filter(WorldORM.id == world_id).first()
        if not world:
            raise ValueError(f"World {world_id} not found")
        
        if world.status != WorldStatus.ACTIVE:
            raise ValueError(f"World {world_id} is not active")
        
        current_tick = world.current_tick
        
        # 1. 加载上一tick状态
        previous_state = await self._load_world_state(world_id, current_tick)
        
        # 2. 收集活跃角色
        active_roles = self.db.query(RoleORM).filter(
            RoleORM.world_id == world_id,
            RoleORM.status.in_([RoleStatus.ACTIVE, RoleStatus.BUSY])
        ).all()
        
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
            world_id, current_tick + 1, decisions, resolutions, self.db
        )
        
        # 保存事件到数据库
        for event in events:
            self.db.add(event)
        
        # 8. 更新角色记忆
        await self._update_role_memories(resolutions, current_tick + 1)
        
        # 9. 保存新状态快照
        new_state = await self._build_snapshot(world_id, current_tick + 1)
        snapshot = WorldSnapshotORM(
            world_id=world_id,
            tick=current_tick + 1,
            snapshot=new_state.dict(),
            summary=await self.claw.generate_summary(current_tick + 1, events, world_changes)
        )
        self.db.add(snapshot)
        
        # 10. 更新世界tick
        world.current_tick = current_tick + 1
        world.updated_at = datetime.utcnow()
        
        # 提交事务
        self.db.commit()
        
        return TickResult(
            tick=current_tick + 1,
            world_id=world_id,
            decisions=decisions,
            conflicts=conflicts,
            resolutions=resolutions,
            events=events,
            world_changes=world_changes,
            summary=snapshot.summary
        )
    
    async def run_ticks(self, world_id: UUID, count: int) -> List[TickResult]:
        """连续推进多个tick"""
        results = []
        
        for i in range(count):
            result = await self.tick(world_id)
            results.append(result)
            
            # 检查是否有需要人类注意的事件
            notable_events = self._check_notable_events(result)
            if notable_events:
                # 暂停，通知人类
                print(f"Notable events detected at tick {result.tick}: {notable_events}")
                break
            
            # 小延迟，避免API限流
            await asyncio.sleep(0.1)
        
        return results
    
    async def _load_world_state(self, world_id: UUID, tick: int) -> WorldState:
        """加载指定tick的世界状态"""
        snapshot = self.db.query(WorldSnapshotORM).filter(
            WorldSnapshotORM.world_id == world_id,
            WorldSnapshotORM.tick == tick
        ).first()
        
        if snapshot:
            return WorldState.parse_obj(snapshot.snapshot)
        
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
        
        # 获取关系
        from models import RelationshipORM
        relationships = self.db.query(RelationshipORM).filter(
            (RelationshipORM.from_role_id == role.id) |
            (RelationshipORM.to_role_id == role.id)
        ).all()
        
        return {
            "memories": [m.content for m in recent_memories],
            "relationships": [
                {
                    "with": r.to_role_id if r.from_role_id == role.id else r.from_role_id,
                    "type": r.type,
                    "trust": r.trust_level
                }
                for r in relationships
            ],
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
            "status_changes": [],
            "location_changes": []
        }
        
        for resolution in resolutions:
            for change in resolution.world_changes:
                if change and change.get("type") == "influence_change":
                    changes["influence_changes"].append(change)
                    # 实际更新数据库
                    role = self.db.query(RoleORM).filter(
                        RoleORM.id == change["target"]
                    ).first()
                    if role:
                        role.influence = max(0, role.influence + change["delta"])
        
        return changes
    
    async def _update_role_memories(
        self,
        resolutions: List[ConflictResolution],
        tick: int
    ):
        """更新角色记忆"""
        for resolution in resolutions:
            for mem_update in resolution.memory_updates:
                if mem_update:
                    memory = RoleMemoryORM(
                        role_id=mem_update["role_id"],
                        tick=tick,
                        type="experience",
                        content=mem_update["content"],
                        importance=7
                    )
                    self.db.add(memory)
    
    async def _build_snapshot(self, world_id: UUID, tick: int) -> WorldState:
        """构建世界状态快照"""
        roles = self.db.query(RoleORM).filter(RoleORM.world_id == world_id).all()
        
        return WorldState(
            tick=tick,
            world_id=world_id,
            roles={
                r.id: {
                    "name": r.name,
                    "status": r.status,
                    "health": r.health,
                    "influence": r.influence,
                    "location": r.location_id
                }
                for r in roles
            },
            geography={},
            factions={},
            global_events=[],
            secrets_status={}
        )
    
    def _check_notable_events(self, result: TickResult) -> List[str]:
        """检查是否有需要人类注意的事件"""
        notable = []
        
        for event in result.events:
            if event.type == EventType.CONFLICT and event.outcome.get("severity") == "critical":
                notable.append(f"Critical conflict: {event.title}")
            
            if event.type == EventType.DIVINE:
                notable.append(f"Divine intervention: {event.title}")
        
        # 检查角色死亡
        for resolution in result.resolutions:
            if resolution.outcome_type == "destruction":
                notable.append(f"Character destroyed: {resolution.loser}")
        
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
        world_id=world.id,
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
        summary="世界创世"
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
        world_id=world_id,
        name=name,
        card=card,
        status=RoleStatus.ACTIVE,
        location_id=initial_location,
        health=100,
        influence=50
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # 创建初始记忆
    memory = RoleMemoryORM(
        role_id=role.id,
        tick=0,
        type="experience",
        content=f"{name}诞生于世界",
        importance=10
    )
    db.add(memory)
    db.commit()
    
    return role
