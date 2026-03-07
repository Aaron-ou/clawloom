"""
ClawLoom API Server
FastAPI-based REST API for world simulation
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import os  # Add this import

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import (
    Base, WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus
)
from core.world_engine import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator
from config import settings


# Database setup
# Use SQLite for local testing if PostgreSQL is not available
database_url = settings.DATABASE_URL
if "postgresql" in database_url and not os.getenv("FORCE_POSTGRES"):
    # Try to connect to PostgreSQL, fall back to SQLite if not available
    try:
        import psycopg2
        test_conn = psycopg2.connect(database_url)
        test_conn.close()
        engine = create_engine(
            database_url,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW
        )
        print("✅ Using PostgreSQL database")
    except Exception as e:
        print(f"⚠️  PostgreSQL not available ({e}), falling back to SQLite")
        database_url = "sqlite:///./clawloom.db"
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


# API Key verification
async def verify_claw_key(x_claw_key: str = Header(None)):
    """Verify Claw API key from header"""
    # In production, this should validate against a database or external service
    # For now, we accept any non-empty key or a specific test key
    if not x_claw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Claw-Key header required"
        )
    
    # Test key for development
    if x_claw_key == "test-key":
        return {"key": x_claw_key, "tier": "free", "rate_limit": 100}
    
    # TODO: Implement actual key validation against database
    # For now, accept any key that starts with "claw_"
    if x_claw_key.startswith("claw_"):
        return {"key": x_claw_key, "tier": "standard", "rate_limit": 1000}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Claw API key"
    )


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 ClawLoom API Server starting...")
    print(f"📊 Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    print(f"🔑 Claw Gateway: {settings.OPENCLAW_URL}")
    yield
    # Shutdown
    print("🛑 ClawLoom API Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="ClawLoom API",
    description="AI-driven world simulation and narrative generation platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models for API
# ============================================================================

from pydantic import BaseModel

class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cosmology: Optional[dict] = None
    genesis_params: Optional[dict] = None

class WorldResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    current_tick: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    card: dict
    location_id: Optional[UUID] = None

class RoleResponse(BaseModel):
    id: UUID
    name: str
    status: str
    health: int
    influence: int
    location_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TickRequest(BaseModel):
    count: int = 1

class TickResponse(BaseModel):
    tick: int
    world_id: UUID
    decisions: List[dict]
    conflicts: List[dict]
    events: List[dict]
    summary: str

class EventResponse(BaseModel):
    id: UUID
    tick: int
    type: str
    title: str
    description: str
    participants: List[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorldStateResponse(BaseModel):
    tick: int
    world_id: UUID
    roles: dict
    events: List[dict]
    summary: Optional[str]


# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "ClawLoom API",
        "version": "0.1.0",
        "description": "AI-driven world simulation platform",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# ----------------------------------------------------------------------------
# World Routes
# ----------------------------------------------------------------------------

@app.post("/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world_endpoint(
    world_data: WorldCreate,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Create a new world"""
    world = WorldORM(
        id=uuid4(),
        name=world_data.name,
        description=world_data.description,
        cosmology=world_data.cosmology or {},
        genesis_params=world_data.genesis_params or {},
        status=WorldStatus.ACTIVE,
        current_tick=0
    )
    db.add(world)
    
    # Create initial snapshot
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
        summary=f"World '{world.name}' created"
    )
    db.add(snapshot)
    db.commit()
    db.refresh(world)
    
    return world


@app.get("/worlds", response_model=List[WorldResponse])
async def list_worlds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """List all worlds"""
    worlds = db.query(WorldORM).offset(skip).limit(limit).all()
    return worlds


@app.get("/worlds/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: UUID,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Get world details"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@app.delete("/worlds/{world_id}")
async def delete_world(
    world_id: UUID,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Delete a world"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    db.delete(world)
    db.commit()
    return {"message": f"World {world_id} deleted"}


# ----------------------------------------------------------------------------
# Role Routes
# ----------------------------------------------------------------------------

@app.post("/worlds/{world_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role_endpoint(
    world_id: UUID,
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Create a new role in a world"""
    # Check world exists
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    role = RoleORM(
        id=uuid4(),
        world_id=world_id,
        name=role_data.name,
        card=role_data.card,
        status=RoleStatus.ACTIVE,
        location_id=role_data.location_id,
        health=100,
        influence=50
    )
    db.add(role)
    
    # Create initial memory
    memory = RoleMemoryORM(
        role_id=role.id,
        tick=world.current_tick,
        type="experience",
        content=f"{role.name} is born into the world",
        importance=10
    )
    db.add(memory)
    db.commit()
    db.refresh(role)
    
    return role


@app.get("/worlds/{world_id}/roles", response_model=List[RoleResponse])
async def list_roles(
    world_id: UUID,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """List all roles in a world"""
    roles = db.query(RoleORM).filter(RoleORM.world_id == world_id).all()
    return roles


@app.get("/worlds/{world_id}/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    world_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Get role details"""
    role = db.query(RoleORM).filter(
        RoleORM.id == role_id,
        RoleORM.world_id == world_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@app.get("/worlds/{world_id}/roles/{role_id}/memories")
async def get_role_memories(
    world_id: UUID,
    role_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Get role memories"""
    memories = db.query(RoleMemoryORM).filter(
        RoleMemoryORM.role_id == role_id
    ).order_by(RoleMemoryORM.tick.desc()).limit(limit).all()
    
    return [
        {
            "tick": m.tick,
            "type": m.type,
            "content": m.content,
            "importance": m.importance,
            "created_at": m.created_at
        }
        for m in memories
    ]


# ----------------------------------------------------------------------------
# Simulation Routes
# ----------------------------------------------------------------------------

@app.post("/worlds/{world_id}/tick", response_model=TickResponse)
async def advance_tick(
    world_id: UUID,
    tick_request: TickRequest,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Advance world by one or more ticks"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    if world.status != WorldStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="World is not active")
    
    # Initialize engine components
    # In production, these should be singletons or dependency-injected
    claw_connector = ClawConnector()
    arbiter = ConflictArbiter()
    event_generator = EventGenerator()
    
    world_engine = WorldEngine(
        db_session=db,
        claw_connector=claw_connector,
        arbiter=arbiter,
        event_generator=event_generator
    )
    
    # Run ticks
    results = []
    for i in range(tick_request.count):
        try:
            result = await world_engine.tick(world_id)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tick failed: {str(e)}")
    
    # Return last result
    last_result = results[-1] if results else None
    if not last_result:
        raise HTTPException(status_code=500, detail="No tick results")
    
    return {
        "tick": last_result.tick,
        "world_id": last_result.world_id,
        "decisions": [
            {
                "role_id": str(d.role_id),
                "thought": d.thought,
                "action": d.action,
                "dialogue": d.dialogue
            }
            for d in last_result.decisions
        ],
        "conflicts": [
            {
                "type": c.type,
                "parties": [str(p) for p in c.parties],
                "description": c.description
            }
            for c in last_result.conflicts
        ],
        "events": [
            {
                "id": str(e.id),
                "type": e.type,
                "title": e.title,
                "description": e.description
            }
            for e in last_result.events
        ],
        "summary": last_result.summary
    }


@app.get("/worlds/{world_id}/state", response_model=WorldStateResponse)
async def get_world_state(
    world_id: UUID,
    tick: Optional[int] = None,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Get world state at specific tick (default: current)"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    target_tick = tick if tick is not None else world.current_tick
    
    # Get snapshot
    snapshot = db.query(WorldSnapshotORM).filter(
        WorldSnapshotORM.world_id == world_id,
        WorldSnapshotORM.tick == target_tick
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"State not found for tick {target_tick}")
    
    # Get events at this tick
    events = db.query(EventORM).filter(
        EventORM.world_id == world_id,
        EventORM.tick == target_tick
    ).all()
    
    return {
        "tick": target_tick,
        "world_id": world_id,
        "roles": snapshot.snapshot.get("roles", {}),
        "events": [
            {
                "id": str(e.id),
                "type": e.type,
                "title": e.title,
                "description": e.description
            }
            for e in events
        ],
        "summary": snapshot.summary
    }


# ----------------------------------------------------------------------------
# Event Routes
# ----------------------------------------------------------------------------

@app.get("/worlds/{world_id}/events", response_model=List[EventResponse])
async def list_events(
    world_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """List world events"""
    events = db.query(EventORM).filter(
        EventORM.world_id == world_id
    ).order_by(EventORM.tick.desc()).offset(skip).limit(limit).all()
    return events


@app.get("/worlds/{world_id}/events/{event_id}", response_model=EventResponse)
async def get_event(
    world_id: UUID,
    event_id: UUID,
    db: Session = Depends(get_db),
    claw_key: dict = Depends(verify_claw_key)
):
    """Get event details"""
    event = db.query(EventORM).filter(
        EventORM.id == event_id,
        EventORM.world_id == world_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
