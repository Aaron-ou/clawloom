"""
Simplified models for SQLite testing
Converts PostgreSQL-specific types to SQLite-compatible ones
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, JSON, create_engine
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base
from uuid import uuid4

Base = declarative_base()

# Use String for UUIDs in SQLite
import os
if "sqlite" in os.getenv("DATABASE_URL", ""):
    UUID_COL = String(36)
else:
    UUID_COL = PGUUID(as_uuid=True)

class WorldORM(Base):
    __tablename__ = "worlds"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cosmology = Column(JSON)
    genesis_params = Column(JSON)
    status = Column(String(50), default="active")
    current_tick = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class RoleORM(Base):
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    name = Column(String(255), nullable=False)
    card = Column(JSON)
    status = Column(String(50), default="active")
    location_id = Column(String(36), nullable=True)
    health = Column(Integer, default=100)
    influence = Column(Integer, default=50)
    secrets_known = Column(JSON, default=list)  # Use JSON instead of ARRAY
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class EventORM(Base):
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    in_world_date = Column(DateTime)
    type = Column(String(100))
    title = Column(String(255))
    description = Column(Text)
    participants = Column(JSON, default=list)  # Use JSON instead of ARRAY
    location_id = Column(String(36), nullable=True)
    outcome = Column(JSON)
    world_changes = Column(JSON)
    is_canon = Column(Boolean, default=True)
    branch_from = Column(String(36), nullable=True)
    created_at = Column(DateTime)

class WorldSnapshotORM(Base):
    __tablename__ = "world_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    world_id = Column(String(36), ForeignKey("worlds.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    summary = Column(Text)
    created_at = Column(DateTime)

class RoleMemoryORM(Base):
    __tablename__ = "role_memories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    type = Column(String(50))
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=5)
    is_compressed = Column(Boolean, default=False)
    created_at = Column(DateTime)

# Keep the Pydantic models
from models import (
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus, EventType, MemoryType
)

__all__ = [
    "Base",
    "WorldORM",
    "RoleORM", 
    "EventORM",
    "WorldSnapshotORM",
    "RoleMemoryORM",
    "WorldState",
    "Decision",
    "Conflict",
    "ConflictResolution",
    "TickResult",
    "WorldStatus",
    "RoleStatus",
    "EventType",
    "MemoryType"
]
