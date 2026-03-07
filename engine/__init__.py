"""
ClawLoom Engine

爪织世界推演引擎 - AI驱动的世界模拟与叙事生成
"""

__version__ = "0.1.0"

from core.world_engine import (
    WorldEngine,
    ClawConnector,
    ConflictArbiter,
    EventGenerator,
    create_world,
    create_role
)

from models import (
    WorldORM,
    RoleORM,
    EventORM,
    WorldSnapshotORM,
    RoleMemoryORM,
    WorldState,
    Decision,
    Conflict,
    ConflictResolution,
    TickResult
)

__all__ = [
    "WorldEngine",
    "ClawConnector",
    "ConflictArbiter",
    "EventGenerator",
    "create_world",
    "create_role",
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
]
