"""
ClawLoom API Server - SQLite Version
Simplified version for local testing without PostgreSQL
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import os
import sys

from fastapi import FastAPI, HTTPException, Depends, Header, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

# Use SQLite-compatible models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models_sqlite import (
    Base, WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus
)

# Import core engine
from core import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator

# SQLite database
DATABASE_URL = "sqlite:///./clawloom.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] SQLite database initialized")

# API Key verification
async def verify_claw_key(x_claw_key: str = Header(None)):
    if not x_claw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Claw-Key header required"
        )
    if x_claw_key == "test-key" or x_claw_key.startswith("claw_"):
        return {"key": x_claw_key}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Claw API key"
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[START] ClawLoom API Server (SQLite) starting...")
    yield
    print("[STOP] Server shutting down...")

app = FastAPI(
    title="ClawLoom API (SQLite)",
    description="AI-driven world simulation - SQLite test version",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
from pydantic import BaseModel

class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cosmology: Optional[dict] = None
    genesis_params: Optional[dict] = None

class WorldResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    current_tick: int
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    card: dict
    location_id: Optional[str] = None

class RoleResponse(BaseModel):
    id: str
    name: str
    status: str
    health: int
    influence: int
    location_id: Optional[str]
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

class TickRequest(BaseModel):
    count: int = 1

class TickResponse(BaseModel):
    tick: int
    world_id: str
    decisions_count: int
    conflicts_count: int
    events_count: int
    summary: str
    events: List[Dict[str, Any]]

class EventResponse(BaseModel):
    id: str
    tick: int
    type: str
    title: str
    description: str
    participants: List[str]
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

class MemoryResponse(BaseModel):
    id: str
    tick: int
    type: str
    content: str
    importance: int
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

# ============================================================================
# World Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "ClawLoom API (SQLite)",
        "version": "0.2.0",
        "docs": "/docs",
        "endpoints": {
            "worlds": "/worlds",
            "roles": "/worlds/{id}/roles",
            "tick": "/worlds/{id}/tick",
            "events": "/worlds/{id}/events",
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "sqlite",
        "version": "0.2.0",
        "timestamp": datetime.utcnow()
    }

@app.post("/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    world_data: WorldCreate,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = WorldORM(
        id=str(uuid4()),
        name=world_data.name,
        description=world_data.description,
        cosmology=world_data.cosmology or {},
        genesis_params=world_data.genesis_params or {},
        status=WorldStatus.ACTIVE,
        current_tick=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(world)
    
    snapshot = WorldSnapshotORM(
        world_id=world.id,
        tick=0,
        snapshot={
            "tick": 0,
            "world_id": world.id,
            "roles": {},
            "geography": {},
            "factions": {},
            "global_events": [],
            "secrets_status": {}
        },
        summary=f"World '{world.name}' created",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    db.refresh(world)
    return world

@app.get("/worlds", response_model=List[WorldResponse])
async def list_worlds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    return db.query(WorldORM).offset(skip).limit(limit).all()

@app.get("/worlds/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

@app.delete("/worlds/{world_id}")
async def delete_world(
    world_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 级联删除相关数据
    db.query(RoleORM).filter(RoleORM.world_id == world_id).delete()
    db.query(EventORM).filter(EventORM.world_id == world_id).delete()
    db.query(WorldSnapshotORM).filter(WorldSnapshotORM.world_id == world_id).delete()
    db.delete(world)
    db.commit()
    
    return {"message": "World deleted", "world_id": world_id}

# ============================================================================
# Role Endpoints
# ============================================================================

@app.post("/worlds/{world_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    world_id: str,
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    role = RoleORM(
        id=str(uuid4()),
        world_id=world_id,
        name=role_data.name,
        card=role_data.card,
        status=RoleStatus.ACTIVE,
        location_id=role_data.location_id,
        health=100,
        influence=50,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(role)
    
    memory = RoleMemoryORM(
        id=str(uuid4()),
        role_id=role.id,
        tick=world.current_tick,
        type="experience",
        content=f"{role.name} is born into the world",
        importance=10,
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    db.refresh(role)
    return role

@app.get("/worlds/{world_id}/roles", response_model=List[RoleResponse])
async def list_roles(
    world_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    return db.query(RoleORM).filter(RoleORM.world_id == world_id).all()

@app.get("/worlds/{world_id}/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    world_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    role = db.query(RoleORM).filter(
        RoleORM.id == role_id,
        RoleORM.world_id == world_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@app.get("/worlds/{world_id}/roles/{role_id}/memories", response_model=List[MemoryResponse])
async def get_role_memories(
    world_id: str,
    role_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    role = db.query(RoleORM).filter(
        RoleORM.id == role_id,
        RoleORM.world_id == world_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    memories = db.query(RoleMemoryORM).filter(
        RoleMemoryORM.role_id == role_id
    ).order_by(desc(RoleMemoryORM.tick)).limit(limit).all()
    
    return memories

# ============================================================================
# Simulation Endpoints
# ============================================================================

@app.post("/worlds/{world_id}/tick", response_model=TickResponse)
async def advance_tick(
    world_id: str,
    tick_request: TickRequest,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    from uuid import UUID
    from core import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator
    
    # Initialize engine components
    claw_connector = ClawConnector()
    arbiter = ConflictArbiter()
    event_generator = EventGenerator()
    
    world_engine = WorldEngine(
        db_session=db,
        claw_connector=claw_connector,
        arbiter=arbiter,
        event_generator=event_generator
    )
    
    results = []
    world_uuid = UUID(world_id)
    
    for i in range(tick_request.count):
        try:
            result = await world_engine.tick(world_uuid)
            results.append(result)
        except Exception as e:
            import traceback
            raise HTTPException(
                status_code=500,
                detail=f"Tick {i+1} failed: {str(e)}\n{traceback.format_exc()}"
            )
    
    last_result = results[-1] if results else None
    if not last_result:
        raise HTTPException(status_code=500, detail="No tick results")
    
    # Format events for response
    events_data = []
    for event in last_result.events:
        events_data.append({
            "id": event.id,
            "tick": event.tick,
            "type": event.type,
            "title": event.title,
            "description": event.description,
            "participants": event.participants
        })
    
    return {
        "tick": last_result.tick,
        "world_id": str(last_result.world_id),
        "decisions_count": len(last_result.decisions),
        "conflicts_count": len(last_result.conflicts),
        "events_count": len(last_result.events),
        "summary": last_result.summary,
        "events": events_data
    }

@app.get("/worlds/{world_id}/state")
async def get_world_state(
    world_id: str,
    tick: Optional[int] = Query(None, description="特定 tick 的状态，默认当前"),
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    target_tick = tick if tick is not None else world.current_tick
    
    snapshot = db.query(WorldSnapshotORM).filter(
        WorldSnapshotORM.world_id == world_id,
        WorldSnapshotORM.tick == target_tick
    ).first()
    
    events = db.query(EventORM).filter(
        EventORM.world_id == world_id,
        EventORM.tick == target_tick
    ).all()
    
    roles = db.query(RoleORM).filter(RoleORM.world_id == world_id).all()
    
    return {
        "tick": target_tick,
        "world_id": world_id,
        "world_name": world.name,
        "world_status": world.status,
        "snapshot": snapshot.snapshot if snapshot else None,
        "summary": snapshot.summary if snapshot else None,
        "events": [
            {
                "id": e.id,
                "type": e.type,
                "title": e.title,
                "description": e.description,
                "participants": e.participants
            }
            for e in events
        ],
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status,
                "health": r.health,
                "influence": r.influence
            }
            for r in roles
        ]
    }

# ============================================================================
# Event Endpoints
# ============================================================================

@app.get("/worlds/{world_id}/events", response_model=List[EventResponse])
async def list_events(
    world_id: str,
    tick: Optional[int] = Query(None, description="筛选特定 tick"),
    event_type: Optional[str] = Query(None, description="筛选事件类型"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    query = db.query(EventORM).filter(EventORM.world_id == world_id)
    
    if tick is not None:
        query = query.filter(EventORM.tick == tick)
    if event_type:
        query = query.filter(EventORM.type == event_type)
    
    events = query.order_by(desc(EventORM.tick)).limit(limit).all()
    return events

@app.get("/worlds/{world_id}/events/{event_id}")
async def get_event(
    world_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    event = db.query(EventORM).filter(
        EventORM.id == event_id,
        EventORM.world_id == world_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# ============================================================================
# Timeline Endpoints
# ============================================================================

@app.get("/worlds/{world_id}/timeline")
async def get_timeline(
    world_id: str,
    start_tick: int = Query(0, ge=0),
    end_tick: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """获取世界时间线概览"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    end = end_tick if end_tick is not None else world.current_tick
    
    snapshots = db.query(WorldSnapshotORM).filter(
        WorldSnapshotORM.world_id == world_id,
        WorldSnapshotORM.tick >= start_tick,
        WorldSnapshotORM.tick <= end
    ).order_by(WorldSnapshotORM.tick).all()
    
    event_counts = db.query(
        EventORM.tick,
        EventORM.type
    ).filter(
        EventORM.world_id == world_id,
        EventORM.tick >= start_tick,
        EventORM.tick <= end
    ).all()
    
    # 统计每 tick 的事件数
    tick_events = {}
    for tick, etype in event_counts:
        if tick not in tick_events:
            tick_events[tick] = {"total": 0, "types": {}}
        tick_events[tick]["total"] += 1
        tick_events[tick]["types"][etype] = tick_events[tick]["types"].get(etype, 0) + 1
    
    timeline = []
    for snap in snapshots:
        timeline.append({
            "tick": snap.tick,
            "summary": snap.summary,
            "event_count": tick_events.get(snap.tick, {}).get("total", 0),
            "event_types": tick_events.get(snap.tick, {}).get("types", {})
        })
    
    return {
        "world_id": world_id,
        "current_tick": world.current_tick,
        "start_tick": start_tick,
        "end_tick": end,
        "timeline": timeline
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_sqlite:app", host="0.0.0.0", port=8000, reload=True)
