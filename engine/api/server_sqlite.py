"""
ClawLoom API Server - SQLite Version
Simplified version for local testing without PostgreSQL
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import os

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Use SQLite-compatible models
from models_sqlite import (
    Base, WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus
)

# SQLite database
DATABASE_URL = "sqlite:///./clawloom.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("✅ SQLite database initialized")

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
    print("🚀 ClawLoom API Server (SQLite) starting...")
    yield
    print("🛑 Server shutting down...")

app = FastAPI(
    title="ClawLoom API (SQLite Test)",
    description="AI-driven world simulation - SQLite test version",
    version="0.1.0",
    lifespan=lifespan
)

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
    class Config:
        from_attributes = True

class TickRequest(BaseModel):
    count: int = 1

@app.get("/")
async def root():
    return {"name": "ClawLoom API (SQLite)", "version": "0.1.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "sqlite", "timestamp": datetime.utcnow()}

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
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    return db.query(WorldORM).all()

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

@app.post("/worlds/{world_id}/tick")
async def advance_tick(
    world_id: str,
    tick_request: TickRequest,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Simple tick simulation (without actual Claw integration for now)
    from core.world_engine import ClawConnector, ConflictArbiter, EventGenerator, WorldEngine
    
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
    for i in range(tick_request.count):
        try:
            result = await world_engine.tick(world_id)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tick failed: {str(e)}")
    
    last_result = results[-1] if results else None
    if not last_result:
        raise HTTPException(status_code=500, detail="No tick results")
    
    return {
        "tick": last_result.tick,
        "world_id": str(last_result.world_id),
        "decisions_count": len(last_result.decisions),
        "conflicts_count": len(last_result.conflicts),
        "events_count": len(last_result.events),
        "summary": last_result.summary
    }

@app.get("/worlds/{world_id}/state")
async def get_world_state(
    world_id: str,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    snapshot = db.query(WorldSnapshotORM).filter(
        WorldSnapshotORM.world_id == world_id,
        WorldSnapshotORM.tick == world.current_tick
    ).first()
    
    events = db.query(EventORM).filter(
        EventORM.world_id == world_id,
        EventORM.tick == world.current_tick
    ).all()
    
    return {
        "tick": world.current_tick,
        "world_id": world_id,
        "roles": snapshot.snapshot.get("roles", {}) if snapshot else {},
        "events": [{"id": e.id, "type": e.type, "title": e.title} for e in events],
        "summary": snapshot.summary if snapshot else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_sqlite:app", host="0.0.0.0", port=8000, reload=True)
