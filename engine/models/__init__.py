# WorldSeed Engine - Python World Engine
# Core data models using Pydantic and SQLAlchemy

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, ForwardRef
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, JSON, ARRAY, create_engine
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ============================================================================
# Enums
# ============================================================================

class WorldStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class RoleStatus(str, Enum):
    DORMANT = "dormant"
    ACTIVE = "active"
    BUSY = "busy"
    INJURED = "injured"
    DECEASED = "deceased"
    ASCENDED = "ascended"

class EventType(str, Enum):
    CONFLICT = "conflict"
    NEGOTIATION = "negotiation"
    DISCOVERY = "discovery"
    MOVEMENT = "movement"
    COMMUNICATION = "communication"
    NATURAL = "natural"
    DIVINE = "divine"  # 人类干预

class MemoryType(str, Enum):
    OBSERVATION = "observation"
    EXPERIENCE = "experience"
    RUMOR = "rumor"
    DREAM = "dream"
    DIVINE_REVELATION = "divine_revelation"

# ============================================================================
# SQLAlchemy ORM Models (Database Layer)
# ============================================================================

class WorldORM(Base):
    __tablename__ = "worlds"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cosmology = Column(JSON)           # 物理规则、魔法体系
    genesis_params = Column(JSON)      # 创世参数
    status = Column(String(50), default=WorldStatus.ACTIVE)
    current_tick = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("RoleORM", back_populates="world", cascade="all, delete-orphan")
    events = relationship("EventORM", back_populates="world", cascade="all, delete-orphan")
    snapshots = relationship("WorldSnapshotORM", back_populates="world", cascade="all, delete-orphan")

class RoleORM(Base):
    __tablename__ = "roles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255), nullable=False)
    card = Column(JSON)                # 完整角色卡
    status = Column(String(50), default=RoleStatus.ACTIVE)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("geography.id"), nullable=True)
    health = Column(Integer, default=100)
    influence = Column(Integer, default=50)
    secrets_known = Column(ARRAY(PGUUID(as_uuid=True)), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="roles")
    memories = relationship("RoleMemoryORM", back_populates="role", cascade="all, delete-orphan")

class EventORM(Base):
    __tablename__ = "events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    in_world_date = Column(DateTime)
    type = Column(String(100))
    title = Column(String(255))
    description = Column(Text)
    participants = Column(ARRAY(PGUUID(as_uuid=True)), default=[])
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("geography.id"), nullable=True)
    outcome = Column(JSON)
    world_changes = Column(JSON)
    is_canon = Column(Boolean, default=True)
    branch_from = Column(PGUUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="events")

class WorldSnapshotORM(Base):
    __tablename__ = "world_snapshots"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)  # 完整世界状态
    summary = Column(Text)                   # AI生成的人类可读摘要
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="snapshots")

class RoleMemoryORM(Base):
    __tablename__ = "role_memories"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    role_id = Column(PGUUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    type = Column(String(50))
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=5)  # 1-10
    is_compressed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role = relationship("RoleORM", back_populates="memories")

class GeographyORM(Base):
    __tablename__ = "geography"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255))
    type = Column(String(100))  # region, city, landmark, resource
    geo_data = Column(JSON)     # GeoJSON或自定义
    properties = Column(JSON)   # 资源、气候等
    controlling_faction = Column(PGUUID(as_uuid=True), nullable=True)

class RelationshipORM(Base):
    __tablename__ = "relationships"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    from_role_id = Column(PGUUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    to_role_id = Column(PGUUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    type = Column(String(100))
    tags = Column(JSON)
    history = Column(JSON)
    trust_level = Column(Integer, default=0)  # -100 to 100
    last_updated = Column(DateTime, default=datetime.utcnow)

class SecretORM(Base):
    __tablename__ = "secrets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    type = Column(String(100))
    content = Column(Text, nullable=False)
    known_by = Column(ARRAY(PGUUID(as_uuid=True)), default=[])
    discovered_at = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InterventionORM(Base):
    __tablename__ = "interventions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id = Column(PGUUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    type = Column(String(100))
    target_role_id = Column(PGUUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    content = Column(JSON)
    result = Column(JSON)
    divine_points_cost = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# Pydantic Models (API/Service Layer)
# ============================================================================

class RoleCard(BaseModel):
    """角色卡 - 定义角色的核心属性和行为"""
    name: str
    drives: List[Dict[str, Any]]  # 核心驱动力
    memory: Dict[str, List[str]]   # 记忆分层（public/private/false_beliefs/traumas）
    perception: Dict[str, Any]     # 感知边界
    agency: Dict[str, Any]         # 行动能力
    decision_style: Dict[str, str] # 决策风格

class WorldState(BaseModel):
    """世界状态 - 单个tick的完整状态"""
    tick: int
    world_id: UUID
    roles: Dict[UUID, Dict[str, Any]]  # 角色状态
    geography: Dict[UUID, Dict[str, Any]]  # 地理状态
    factions: Dict[UUID, Dict[str, Any]]   # 势力状态
    global_events: List[Dict[str, Any]]    # 全局事件
    secrets_status: Dict[UUID, List[UUID]] # 秘密传播状态

class Decision(BaseModel):
    """角色决策"""
    role_id: UUID
    tick: int
    thought: str                   # 思考过程
    action: Dict[str, Any]         # 行动
    dialogue: Optional[str] = None # 对话
    target: Optional[UUID] = None  # 目标对象
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conflict(BaseModel):
    """冲突"""
    id: UUID = Field(default_factory=uuid4)
    type: str                      # resource, stealth_vs_detection, betrayal, negotiation
    parties: List[UUID]            # 冲突方
    description: str
    stakes: str
    severity: str = "normal"       # minor, normal, serious, critical

class ConflictResolution(BaseModel):
    """冲突解决结果"""
    conflict_id: UUID
    outcome_type: str              # victory, compromise, destruction, undetected, exposed, etc.
    winner: Optional[UUID] = None
    loser: Optional[UUID] = None
    description: str
    world_changes: List[Dict[str, Any]]
    memory_updates: List[Dict[str, Any]]

class TickResult(BaseModel):
    """Tick推演结果"""
    tick: int
    world_id: UUID
    decisions: List[Decision]
    conflicts: List[Conflict]
    resolutions: List[ConflictResolution]
    events: List[EventORM]
    world_changes: Dict[str, Any]
    summary: str                   # AI生成的摘要
