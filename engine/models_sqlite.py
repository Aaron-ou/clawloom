"""
Simplified models for SQLite testing
Converts PostgreSQL-specific types to SQLite-compatible ones
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, JSON, create_engine, Enum, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from uuid import uuid4
from datetime import datetime
import enum

Base = declarative_base()

# User role enum
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    WEAVER = "weaver"  # 织主 - 人类用户
    AI = "ai"          # AI - 被认领的织者

# Key status enum
class KeyStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"

# World status enum
class WorldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"

# Role status enum
class RoleStatus(str, enum.Enum):
    DORMANT = "DORMANT"
    ACTIVE = "ACTIVE"
    BUSY = "BUSY"
    INJURED = "INJURED"
    DECEASED = "DECEASED"
    ASCENDED = "ASCENDED"

# Event type enum
class EventType(str, enum.Enum):
    CONFLICT = "CONFLICT"
    NEGOTIATION = "NEGOTIATION"
    DISCOVERY = "DISCOVERY"
    MOVEMENT = "MOVEMENT"
    COMMUNICATION = "COMMUNICATION"
    NATURAL = "NATURAL"
    DIVINE = "DIVINE"

# Memory type enum
class MemoryType(str, enum.Enum):
    OBSERVATION = "OBSERVATION"
    EXPERIENCE = "EXPERIENCE"
    RUMOR = "RUMOR"
    DREAM = "DREAM"
    DIVINE_REVELATION = "DIVINE_REVELATION"

# Location/Map enums
class LocationType(str, enum.Enum):
    TOWN = "TOWN"           # 城镇
    CITY = "CITY"           # 城市
    VILLAGE = "VILLAGE"     # 村庄
    CASTLE = "CASTLE"       # 城堡
    DUNGEON = "DUNGEON"     # 地下城
    FOREST = "FOREST"       # 森林
    MOUNTAIN = "MOUNTAIN"   # 山脉
    RIVER = "RIVER"         # 河流
    LAKE = "LAKE"           # 湖泊
    COAST = "COAST"         # 海岸
    DESERT = "DESERT"       # 沙漠
    PLAINS = "PLAINS"       # 平原
    RUINS = "RUINS"         # 遗迹
    TEMPLE = "TEMPLE"       # 神殿
    CAMP = "CAMP"           # 营地
    PORTAL = "PORTAL"       # 传送门
    OTHER = "OTHER"         # 其他

class PathType(str, enum.Enum):
    ROAD = "ROAD"           # 道路
    TRAIL = "TRAIL"         # 小径
    RIVER_PATH = "RIVER"    # 河流路径
    SEA_ROUTE = "SEA"       # 海上航线
    SECRET = "SECRET"       # 秘密通道
    PORTAL = "PORTAL"       # 传送门

# ============ User & Key Management ============

class UserORM(Base):
    """织主（人类用户）表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.WEAVER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKeyORM", back_populates="owner", cascade="all, delete-orphan")
    ai_bindings = relationship("AIBindingORM", back_populates="weaver", cascade="all, delete-orphan")

class APIKeyORM(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)  # 用于显示，如 "claw_abc123"
    name = Column(String(100), nullable=True)  # 用户可以给key起名字
    status = Column(String(20), default=KeyStatus.ACTIVE)
    
    # 归属
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    owner_type = Column(String(20), default="weaver")  # weaver 或 ai
    
    # 使用统计
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # 创建信息
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("UserORM", back_populates="api_keys")

class AIBindingORM(Base):
    """AI认领绑定表 - 织主认领AI的关系"""
    __tablename__ = "ai_bindings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # 织主（人类）
    weaver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # AI信息
    ai_name = Column(String(100), nullable=False)  # AI的自我命名
    ai_key_id = Column(String(36), ForeignKey("api_keys.id"), nullable=False)
    
    # 绑定状态
    status = Column(String(20), default="active")  # active, suspended, released
    
    # 元数据
    claimed_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)  # 织主对AI的备注
    
    # Relationships
    weaver = relationship("UserORM", back_populates="ai_bindings")
    ai_key = relationship("APIKeyORM")

# ============ Core World Models ============

class WorldORM(Base):
    __tablename__ = "worlds"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cosmology = Column(JSON)
    genesis_params = Column(JSON)
    status = Column(String(50), default=WorldStatus.ACTIVE)
    current_tick = Column(Integer, default=0)
    
    # 归属
    creator_id = Column(String(36), ForeignKey("api_keys.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("RoleORM", back_populates="world", cascade="all, delete-orphan")
    events = relationship("EventORM", back_populates="world", cascade="all, delete-orphan")
    snapshots = relationship("WorldSnapshotORM", back_populates="world", cascade="all, delete-orphan")

class RoleORM(Base):
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255), nullable=False)
    card = Column(JSON)
    status = Column(String(50), default=RoleStatus.ACTIVE)
    location_id = Column(String(36), nullable=True)
    health = Column(Integer, default=100)
    influence = Column(Integer, default=50)
    secrets_known = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="roles")
    memories = relationship("RoleMemoryORM", back_populates="role", cascade="all, delete-orphan")

class EventORM(Base):
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    in_world_date = Column(DateTime)
    type = Column(String(100))
    title = Column(String(255))
    description = Column(Text)
    participants = Column(JSON, default=list)
    location_id = Column(String(36), nullable=True)
    outcome = Column(JSON)
    world_changes = Column(JSON)
    is_canon = Column(Boolean, default=True)
    branch_from = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="events")

class WorldSnapshotORM(Base):
    __tablename__ = "world_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM", back_populates="snapshots")

class RoleMemoryORM(Base):
    __tablename__ = "role_memories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    type = Column(String(50))
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=5)
    is_compressed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role = relationship("RoleORM", back_populates="memories")

# ============ Map Models ============

class LocationORM(Base):
    """地图地点/节点"""
    __tablename__ = "locations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    
    # 基本信息
    name = Column(String(255), nullable=False)
    description = Column(Text)
    location_type = Column(String(50), default=LocationType.OTHER)
    
    # 坐标 (2D地图位置)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    
    # 地图层级/缩放级别
    zoom_level = Column(Integer, default=1)  # 1=大陆级, 2=区域级, 3=城市级
    
    # 属性
    properties = Column(JSON, default=dict)  # 人口、资源、危险度等
    tags = Column(JSON, default=list)        # 标签 ["危险", "贸易中心"]
    
    # 视觉
    icon = Column(String(100), nullable=True)   # 图标名称
    color = Column(String(20), nullable=True)   # 颜色 #RRGGBB
    
    # 状态
    is_discovered = Column(Boolean, default=True)  # 是否已被发现
    is_hidden = Column(Boolean, default=False)     # 是否隐藏(秘密地点)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM")
    outgoing_paths = relationship("PathORM", foreign_keys="PathORM.from_location_id", back_populates="from_location")
    incoming_paths = relationship("PathORM", foreign_keys="PathORM.to_location_id", back_populates="to_location")

class PathORM(Base):
    """地点之间的路径/连接"""
    __tablename__ = "paths"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    
    # 连接的两端
    from_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    to_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    
    # 路径信息
    path_type = Column(String(50), default=PathType.TRAIL)
    name = Column(String(255), nullable=True)
    description = Column(Text)
    
    # 路径属性
    distance = Column(Integer, nullable=True)      # 距离 (单位: 里/公里)
    travel_difficulty = Column(Integer, default=1) # 难度 1-10
    travel_time = Column(Integer, nullable=True)   # 通行时间 (小时)
    
    # 状态
    is_hidden = Column(Boolean, default=False)     # 秘密通道
    is_blocked = Column(Boolean, default=False)    # 是否被阻断
    block_reason = Column(Text, nullable=True)     # 阻断原因
    
    # 视觉
    color = Column(String(20), nullable=True)
    style = Column(String(20), default="solid")    # solid, dashed, dotted
    
    properties = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM")
    from_location = relationship("LocationORM", foreign_keys=[from_location_id], back_populates="outgoing_paths")
    to_location = relationship("LocationORM", foreign_keys=[to_location_id], back_populates="incoming_paths")

class RegionORM(Base):
    """地图区域 (用于划分大区域如国家、省、生态区)"""
    __tablename__ = "regions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 区域边界 (多边形点列表)
    boundary = Column(JSON, default=list)  # [{"x": 0, "y": 0}, ...]
    
    # 区域属性
    region_type = Column(String(50), default="area")  # country, province, biome, etc.
    properties = Column(JSON, default=dict)
    
    # 视觉
    color = Column(String(20), nullable=True)      # 填充颜色 (半透明)
    border_color = Column(String(20), nullable=True)  # 边框颜色
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM")


class HexTileORM(Base):
    """六边形瓦片地图 - 用于六边形网格地形"""
    __tablename__ = "hex_tiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    
    # 轴向坐标 (q, r) - 立方坐标系的两个轴，第三个s = -q-r
    q = Column(Integer, nullable=False)  # 列
    r = Column(Integer, nullable=False)  # 行
    
    # 地形类型
    terrain = Column(String(50), default="OCEAN")
    
    # 环境属性
    elevation = Column(Integer, default=0)      # 海拔 (-5到10)
    moisture = Column(Integer, default=50)      # 湿度 (0-100)
    temperature = Column(Integer, default=20)   # 温度 (-30到50)
    
    # 特征与资源
    features = Column(JSON, default=list)       # ["forest", "mountain", "ruins"]
    resource = Column(String(100), nullable=True)  # 资源类型
    
    # 关联的地点（如果有建筑物/城市）
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    
    # 额外属性
    properties = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    world = relationship("WorldORM")
    location = relationship("LocationORM")
    
    # 唯一约束：一个世界中的每个坐标只能有一个瓦片
    __table_args__ = (
        UniqueConstraint('world_id', 'q', 'r', name='uix_world_hex_coords'),
    )


# Keep the Pydantic models
from models import (
    WorldState, Decision, Conflict, ConflictResolution, TickResult
)

__all__ = [
    "Base",
    "UserORM",
    "APIKeyORM", 
    "AIBindingORM",
    "WorldORM",
    "RoleORM",
    "EventORM",
    "WorldSnapshotORM",
    "RoleMemoryORM",
    "LocationORM",
    "PathORM",
    "RegionORM",
    "HexTileORM",
    "UserRole",
    "KeyStatus",
    "WorldStatus",
    "RoleStatus",
    "EventType",
    "MemoryType",
    "LocationType",
    "PathType",
    "WorldState",
    "Decision",
    "Conflict",
    "ConflictResolution",
    "TickResult",
]
