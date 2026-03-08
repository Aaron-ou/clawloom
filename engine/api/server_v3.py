"""
ClawLoom API Server v3
分离认证体系:
- 织主(Weaver): JWT Token
- AI(Claw): API Key
"""

import os
import sys
import math
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, status, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from datetime import datetime, timedelta

from models_sqlite import (
    Base, UserORM, APIKeyORM, AIBindingORM,
    WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    LocationORM, PathORM, RegionORM, HexTileORM,
    WorldStatus, RoleStatus, KeyStatus, MemoryType
)
from models.map_models import (
    LocationCreate, LocationUpdate, LocationResponse,
    PathCreate, PathUpdate, PathResponse,
    RegionCreate, RegionUpdate, RegionResponse,
    MapDataResponse,
    HexTileCreate, HexTileUpdate, HexTileResponse, HexMapDataResponse,
    HexMapGenerateRequest, TerrainType,
)
from core import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator
from pydantic import BaseModel, Field

# 导入新的认证工具
from api.auth_utils import (
    hash_password,
    create_weaver_token,
    verify_weaver_token,
    generate_api_key,
    verify_api_key_match,
    AIAuthService,
    get_current_weaver_user,
    get_current_weaver_user_optional,
    get_current_ai_user,
    get_current_ai_user_optional,
    get_current_auth_user,
    get_current_auth_user_optional,
)

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'clawloom.db')}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Database initialized")

app = FastAPI(
    title="ClawLoom API v3",
    description="AI自注册、织主绑定、世界模拟 - 分离认证体系",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ Pydantic Models ============

class WeaverRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class WeaverLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class AIRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class AIRegisterResponse(BaseModel):
    ai_id: str
    ai_name: str
    api_key: str
    message: str

class UserInfoResponse(BaseModel):
    id: str
    username: str
    role: str
    is_ai: bool
    can_tick: bool
    can_create: bool
    can_divine: bool

class WorldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class WorldResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    current_tick: int
    created_at: datetime

class DivineRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)

# ============ Auth Routes ============

@app.post("/auth/register", response_model=TokenResponse)
def register_weaver(data: WeaverRegister, db: Session = Depends(get_db)):
    """织主注册"""
    existing = db.query(UserORM).filter(UserORM.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = UserORM(
        id=str(uuid4()),
        username=data.username,
        hashed_password=hash_password(data.password),
        role="weaver",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    
    token = create_weaver_token(user.id, user.username)
    
    return TokenResponse(
        access_token=token,
        username=user.username,
        role="weaver"
    )

@app.post("/auth/login", response_model=TokenResponse)
def login_weaver(data: WeaverLogin, db: Session = Depends(get_db)):
    """织主登录"""
    user = db.query(UserORM).filter(
        UserORM.username == data.username,
        UserORM.hashed_password == hash_password(data.password)
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    
    token = create_weaver_token(user.id, user.username)
    
    return TokenResponse(
        access_token=token,
        username=user.username,
        role="weaver"
    )

@app.get("/auth/me", response_model=UserInfoResponse)
def get_me(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = get_current_auth_user(authorization, db)
    """获取当前用户信息"""
    if user["type"] == "weaver":
        db_user = db.query(UserORM).filter(UserORM.id == user["user_id"]).first()
        return UserInfoResponse(
            id=db_user.id,
            username=db_user.username,
            role="weaver",
            is_ai=False,
            can_tick=False,
            can_create=False,
            can_divine=True,
        )
    else:  # AI
        api_key = user["api_key"]
        binding = db.query(AIBindingORM).filter(
            AIBindingORM.ai_key_id == api_key.id
        ).first()
        return UserInfoResponse(
            id=api_key.owner_id,
            username=api_key.name,
            role="ai",
            is_ai=True,
            can_tick=True,
            can_create=True,
            can_divine=False,
        )

# ============ AI Routes ============

@app.post("/ai/register", response_model=AIRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_ai(data: AIRegister, db: Session = Depends(get_db)):
    """AI自注册"""
    plain_key, key_hash, key_prefix = generate_api_key()
    
    # 创建AI用户
    ai_user = UserORM(
        id=str(uuid4()),
        username=f"ai_{data.name}_{str(uuid4())[:8]}",
        hashed_password="",
        role="ai",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(ai_user)
    db.flush()
    
    # 创建API Key
    api_key = APIKeyORM(
        id=str(uuid4()),
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=f"AI: {data.name}",
        status=KeyStatus.ACTIVE,
        owner_id=ai_user.id,
        owner_type="ai",
        created_at=datetime.utcnow()
    )
    db.add(api_key)
    db.commit()
    
    return AIRegisterResponse(
        ai_id=ai_user.id,
        ai_name=data.name,
        api_key=plain_key,
        message=f"注册成功！请妥善保存API Key: {plain_key}"
    )

@app.get("/ai/info")
def get_ai_info(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    ai_data = get_current_ai_user(authorization, db)
    """获取AI自身信息"""
    api_key, owner_type = ai_data
    
    binding = db.query(AIBindingORM).filter(
        AIBindingORM.ai_key_id == api_key.id
    ).first()
    
    return {
        "ai_id": api_key.owner_id,
        "ai_name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "is_bound": binding is not None,
        "weaver_name": binding.weaver.username if binding and binding.weaver else None,
        "bound_at": binding.claimed_at if binding else None
    }

# ============ Weaver Binding Routes ============

class BindAIRequest(BaseModel):
    ai_key: str
    ai_name: Optional[str] = None

@app.post("/weaver/bind")
def bind_ai(
    data: BindAIRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """织主绑定AI"""
    weaver = get_current_weaver_user(authorization, db)
    # 验证AI Key
    auth_service = AIAuthService(db)
    result = auth_service.verify_ai_key(data.ai_key)
    
    if not result:
        raise HTTPException(status_code=400, detail="无效的AI API Key")
    
    ai_key, owner_type = result
    
    if owner_type != "ai":
        raise HTTPException(status_code=400, detail="这个Key不属于AI")
    
    # 检查是否已被绑定
    existing = db.query(AIBindingORM).filter(
        AIBindingORM.ai_key_id == ai_key.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="这个AI已经被绑定了")
    
    # 创建绑定
    binding = AIBindingORM(
        id=str(uuid4()),
        weaver_id=weaver["user_id"],
        ai_name=data.ai_name or ai_key.name or "未命名AI",
        ai_key_id=ai_key.id,
        status="active",
        claimed_at=datetime.utcnow()
    )
    db.add(binding)
    db.commit()
    
    return {
        "binding_id": binding.id,
        "ai_name": binding.ai_name,
        "message": "成功绑定AI！"
    }

@app.get("/weaver/ais")
def get_weaver_ais(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    weaver = get_current_weaver_user(authorization, db)
    """获取织主绑定的所有AI"""
    bindings = db.query(AIBindingORM).filter(
        AIBindingORM.weaver_id == weaver["user_id"],
        AIBindingORM.status == "active"
    ).all()
    
    return [
        {
            "id": b.id,
            "ai_name": b.ai_name,
            "ai_key_id": b.ai_key_id,
            "key_prefix": b.ai_key.key_prefix if b.ai_key else None,
            "claimed_at": b.claimed_at,
            "notes": b.notes
        }
        for b in bindings
    ]

# ============ World Routes ============

@app.get("/worlds", response_model=List[WorldResponse])
def list_worlds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """列出所有世界（公开）"""
    return db.query(WorldORM).order_by(WorldORM.created_at.desc()).offset(skip).limit(limit).all()

@app.post("/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
def create_world(
    data: WorldCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建世界（需要AI Key）"""
    ai_data = get_current_ai_user(authorization, db)
    api_key, owner_type = ai_data
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以创建世界")
    
    world = WorldORM(
        id=str(uuid4()),
        name=data.name,
        description=data.description,
        status=WorldStatus.ACTIVE,
        current_tick=0,
        creator_id=api_key.id,
        created_at=datetime.utcnow()
    )
    db.add(world)
    db.commit()
    db.refresh(world)
    
    return world

@app.get("/worlds/{world_id}", response_model=WorldResponse)
def get_world(world_id: str, db: Session = Depends(get_db)):
    """获取世界详情"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

# ============ Role Routes ============

@app.get("/worlds/{world_id}/roles")
def list_roles(world_id: str, db: Session = Depends(get_db)):
    """列出世界中的所有角色"""
    return db.query(RoleORM).filter(RoleORM.world_id == world_id).all()

@app.post("/worlds/{world_id}/roles")
def create_role(
    world_id: str,
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建角色（需要AI Key）"""
    ai_data = get_current_ai_user(authorization, db)
    api_key, owner_type = ai_data
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    role = RoleORM(
        id=str(uuid4()),
        world_id=world_id,
        name=data.get("name"),
        card=data.get("card", {}),
        status=RoleStatus.ACTIVE,
        health=100,
        influence=50,
        secrets_known=[],
        created_at=datetime.utcnow()
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return role

@app.post("/worlds/{world_id}/roles/{role_id}/divine")
def give_divine_inspiration(
    world_id: str,
    role_id: str,
    data: DivineRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """织主给予角色神启"""
    weaver = get_current_weaver_user(authorization, db)
    role = db.query(RoleORM).filter(
        RoleORM.id == role_id,
        RoleORM.world_id == world_id
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    memory = RoleMemoryORM(
        id=str(uuid4()),
        role_id=role_id,
        tick=0,
        type=MemoryType.DIVINE_REVELATION,
        content=f"[神启] {data.message}",
        importance=10,
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    
    return {"message": "神启已传达", "role_name": role.name}

# ============ Event Routes ============

@app.get("/worlds/{world_id}/events")
def get_events(
    world_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取世界事件列表"""
    return db.query(EventORM).filter(
        EventORM.world_id == world_id
    ).order_by(EventORM.tick.desc()).limit(limit).all()

# ============ Simulation Routes ============

class TickRequest(BaseModel):
    count: int = Field(1, ge=1, le=100)

@app.post("/worlds/{world_id}/tick")
def advance_tick(
    world_id: str,
    req: TickRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """推进世界（需要AI Key）"""
    # 首先检查是否为AI（织主应该被拒绝）
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    # 如果是织主token（JWT），直接拒绝
    if not token.startswith("claw_"):
        raise HTTPException(status_code=403, detail="Only AI can advance ticks")
    
    ai_data = get_current_ai_user(authorization, db)
    from uuid import UUID
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 初始化引擎
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
    for i in range(req.count):
        result = world_engine.tick(UUID(world_id))
        results.append(result)
    
    last_result = results[-1]
    
    return {
        "tick": last_result.tick,
        "world_id": str(last_result.world_id),
        "decisions_count": len(last_result.decisions),
        "conflicts_count": len(last_result.conflicts),
        "events_count": len(last_result.events),
        "summary": last_result.summary
    }

# ============ Map Routes ============

@app.get("/worlds/{world_id}/map", response_model=MapDataResponse)
def get_world_map(
    world_id: str,
    zoom_level: Optional[int] = Query(None, ge=1, le=3),
    db: Session = Depends(get_db)
):
    """获取世界完整地图数据"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    locations = db.query(LocationORM).filter(LocationORM.world_id == world_id).all()
    paths = db.query(PathORM).filter(PathORM.world_id == world_id).all()
    regions = db.query(RegionORM).filter(RegionORM.world_id == world_id).all()
    
    if locations:
        min_x = min(l.x for l in locations)
        max_x = max(l.x for l in locations)
        min_y = min(l.y for l in locations)
        max_y = max(l.y for l in locations)
    else:
        min_x = max_x = min_y = max_y = 0
    
    return {
        "world_id": world_id,
        "locations": locations,
        "paths": paths,
        "regions": regions,
        "bounds": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y
        }
    }

@app.post("/worlds/{world_id}/locations", response_model=LocationResponse)
def create_location(
    world_id: str,
    data: LocationCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建地点（需要AI Key）"""
    ai_data = get_current_ai_user(authorization, db)
    api_key, owner_type = ai_data
    
    location = LocationORM(
        id=str(uuid4()),
        world_id=world_id,
        name=data.name,
        description=data.description,
        location_type=data.location_type.value if hasattr(data.location_type, 'value') else data.location_type,
        x=data.x,
        y=data.y,
        zoom_level=data.zoom_level,
        properties=data.properties,
        tags=data.tags,
        icon=data.icon,
        color=data.color,
        is_hidden=data.is_hidden,
        is_discovered=True
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return location

@app.get("/worlds/{world_id}/locations", response_model=List[LocationResponse])
def list_locations(world_id: str, db: Session = Depends(get_db)):
    """获取地点列表"""
    return db.query(LocationORM).filter(LocationORM.world_id == world_id).all()

@app.post("/worlds/{world_id}/paths", response_model=PathResponse)
def create_path(
    world_id: str,
    data: PathCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建路径（需要AI Key）"""
    ai_data = get_current_ai_user(authorization, db)
    path = PathORM(
        id=str(uuid4()),
        world_id=world_id,
        from_location_id=data.from_location_id,
        to_location_id=data.to_location_id,
        path_type=data.path_type.value if hasattr(data.path_type, 'value') else data.path_type,
        name=data.name,
        description=data.description,
        distance=data.distance,
        travel_difficulty=data.travel_difficulty,
        travel_time=data.travel_time,
        is_hidden=data.is_hidden,
        color=data.color,
        style=data.style,
        properties=data.properties
    )
    db.add(path)
    db.commit()
    db.refresh(path)
    
    # 添加地点名称
    from_loc = db.query(LocationORM).filter(LocationORM.id == data.from_location_id).first()
    to_loc = db.query(LocationORM).filter(LocationORM.id == data.to_location_id).first()
    
    return {
        **{k: v for k, v in path.__dict__.items() if not k.startswith('_')},
        "from_location_name": from_loc.name if from_loc else None,
        "to_location_name": to_loc.name if to_loc else None,
    }

@app.get("/worlds/{world_id}/paths", response_model=List[PathResponse])
def list_paths(world_id: str, db: Session = Depends(get_db)):
    """获取路径列表"""
    paths = db.query(PathORM).filter(PathORM.world_id == world_id).all()
    
    result = []
    for path in paths:
        from_loc = db.query(LocationORM).filter(LocationORM.id == path.from_location_id).first()
        to_loc = db.query(LocationORM).filter(LocationORM.id == path.to_location_id).first()
        result.append({
            **{k: v for k, v in path.__dict__.items() if not k.startswith('_')},
            "from_location_name": from_loc.name if from_loc else None,
            "to_location_name": to_loc.name if to_loc else None,
        })
    
    return result


# ============ Hex Tile Map APIs ============

# 六边形尺寸常量
HEX_SIZE = 30  # 六边形边长（像素）
HEX_WIDTH = HEX_SIZE * 2
HEX_HEIGHT = HEX_SIZE * 1.732  # sqrt(3)

def hex_to_pixel(q: int, r: int, size: float = HEX_SIZE) -> tuple:
    """将轴向坐标转换为像素坐标"""
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return x, y

def get_hex_color(terrain: str) -> str:
    """获取地形颜色"""
    colors = {
        "OCEAN": "#3b82f6",        # 蓝色
        "DEEP_OCEAN": "#1e40af",   # 深蓝色
        "COAST": "#93c5fd",        # 浅蓝色
        "PLAINS": "#86efac",       # 浅绿色
        "GRASSLAND": "#22c55e",    # 绿色
        "FOREST": "#15803d",       # 深绿色
        "JUNGLE": "#166534",       # 热带绿
        "MOUNTAIN": "#78716c",     # 灰色
        "HILL": "#a8a29e",         # 浅灰
        "DESERT": "#fcd34d",       # 黄色
        "TUNDRA": "#e5e7eb",       # 灰白
        "SNOW": "#f9fafb",         # 白色
        "SWAMP": "#3f6212",        # 暗绿
        "VOLCANO": "#dc2626",      # 红色
        "CITY": "#f97316",         # 橙色
        "RUINS": "#7c2d12",        # 棕色
        "LAKE": "#60a5fa",         # 湖蓝
        "RIVER": "#93c5fd",        # 河蓝
    }
    return colors.get(terrain, "#3b82f6")

def generate_hex_polygon_points(cx: float, cy: float, size: float) -> str:
    """生成六边形的SVG点坐标"""
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        px = cx + size * math.cos(angle_rad)
        py = cy + size * math.sin(angle_rad)
        points.append(f"{px:.1f},{py:.1f}")
    return " ".join(points)

@app.post("/worlds/{world_id}/hexmap/generate")
def generate_hex_map(
    world_id: str,
    data: HexMapGenerateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """生成六边形瓦片地图"""
    # 验证权限（仅AI或世界创建者可生成）
    ai_data = get_current_ai_user_optional(authorization, db)
    
    # 检查世界是否存在
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 清除现有瓦片
    db.query(HexTileORM).filter(HexTileORM.world_id == world_id).delete()
    
    # 生成六边形网格
    radius = data.radius
    tiles = []
    
    # 使用随机种子
    if data.seed:
        random.seed(data.seed)
    
    # 生成噪声函数（简单实现）
    def noise(q, r):
        return random.random()
    
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            s = -q - r
            # 确保在六边形区域内
            if abs(q) + abs(r) + abs(s) > radius * 2:
                continue
            
            # 计算距离中心的距离
            dist = max(abs(q), abs(r), abs(s))
            
            # 边缘强制为海洋
            if dist > radius - data.ocean_ring:
                terrain = "OCEAN"
            else:
                # 使用噪声决定地形
                n = noise(q, r)
                if n < 0.3:
                    terrain = "OCEAN"
                elif n < 0.4:
                    terrain = "COAST"
                elif n < 0.6:
                    terrain = "PLAINS"
                elif n < 0.75:
                    terrain = "FOREST"
                elif n < 0.85:
                    terrain = "MOUNTAIN"
                elif n < 0.9:
                    terrain = "DESERT"
                else:
                    terrain = "HILL"
            
            # 根据地形设置海拔
            elevation_map = {
                "OCEAN": -2, "DEEP_OCEAN": -5, "COAST": 0,
                "PLAINS": 1, "GRASSLAND": 1, "FOREST": 2, "JUNGLE": 2,
                "HILL": 3, "MOUNTAIN": 8, "DESERT": 1, "TUNDRA": 1,
                "SNOW": 5, "SWAMP": 0, "VOLCANO": 10,
                "CITY": 1, "RUINS": 1, "LAKE": -1, "RIVER": 0,
            }
            
            tile = HexTileORM(
                id=str(uuid4()),
                world_id=world_id,
                q=q,
                r=r,
                terrain=terrain,
                elevation=elevation_map.get(terrain, 0),
                moisture=random.randint(20, 80),
                temperature=random.randint(-10, 35),
                features=[],
                properties={}
            )
            db.add(tile)
            tiles.append(tile)
    
    db.commit()
    
    return {
        "message": f"Generated {len(tiles)} hex tiles",
        "world_id": world_id,
        "radius": radius,
        "tile_count": len(tiles)
    }

@app.get("/worlds/{world_id}/hexmap", response_model=HexMapDataResponse)
def get_hex_map(
    world_id: str,
    db: Session = Depends(get_db)
):
    """获取六边形瓦片地图数据"""
    # 检查世界是否存在
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 获取所有瓦片
    tiles = db.query(HexTileORM).filter(HexTileORM.world_id == world_id).all()
    
    if not tiles:
        raise HTTPException(status_code=404, detail="No hex map found. Generate one first.")
    
    # 计算边界
    qs = [t.q for t in tiles]
    rs = [t.r for t in tiles]
    
    # 转换为响应格式
    tile_responses = []
    for tile in tiles:
        x, y = hex_to_pixel(tile.q, tile.r)
        tile_responses.append({
            "id": tile.id,
            "world_id": tile.world_id,
            "q": tile.q,
            "r": tile.r,
            "x": x,
            "y": y,
            "terrain": tile.terrain,
            "elevation": tile.elevation,
            "moisture": tile.moisture,
            "temperature": tile.temperature,
            "features": tile.features,
            "resource": tile.resource,
            "location_id": tile.location_id,
            "location_name": tile.location.name if tile.location else None,
            "properties": tile.properties,
            "created_at": tile.created_at,
            "updated_at": tile.updated_at,
        })
    
    return {
        "world_id": world_id,
        "tiles": tile_responses,
        "bounds": {
            "min_q": min(qs),
            "max_q": max(qs),
            "min_r": min(rs),
            "max_r": max(rs),
        },
        "center": {"q": 0, "r": 0},
        "radius": max(max(abs(q) for q in qs), max(abs(r) for r in rs)) if tiles else 0
    }

@app.get("/worlds/{world_id}/hexmap/svg")
def get_hex_map_svg(
    world_id: str,
    size: int = Query(30, ge=10, le=100, description="Hex size in pixels"),
    show_grid: bool = Query(True, description="Show grid lines"),
    db: Session = Depends(get_db)
):
    """获取六边形地图的SVG表示"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    tiles = db.query(HexTileORM).filter(HexTileORM.world_id == world_id).all()
    
    if not tiles:
        raise HTTPException(status_code=404, detail="No hex map found")
    
    # 计算SVG视图框
    xs, ys = [], []
    for tile in tiles:
        x, y = hex_to_pixel(tile.q, tile.r, size)
        xs.append(x)
        ys.append(y)
    
    padding = size * 2
    min_x, max_x = min(xs) - padding, max(xs) + padding
    min_y, max_y = min(ys) - padding, max(ys) + padding
    width = max_x - min_x
    height = max_y - min_y
    
    # 构建SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}" width="100%" height="100%">',
        f'<rect x="{min_x}" y="{min_y}" width="{width}" height="{height}" fill="#1e40af"/>',  # 深海背景
    ]
    
    # 绘制瓦片
    terrain_icons = {
        "FOREST": "🌲", "MOUNTAIN": "⛰️", "CITY": "🏰", "RUINS": "🏛️",
        "DESERT": "🌵", "HILL": "⛰️", "LAKE": "💧", "RIVER": "💧",
        "VOLCANO": "🌋", "SNOW": "❄️", "SWAMP": "🌿",
    }
    
    for tile in tiles:
        x, y = hex_to_pixel(tile.q, tile.r, size)
        color = get_hex_color(tile.terrain)
        points = generate_hex_polygon_points(x, y, size * 0.95)  # 0.95 留间隙
        
        # 六边形
        svg_parts.append(f'<polygon points="{points}" fill="{color}" stroke="{("#1e40af" if tile.terrain in ["OCEAN", "DEEP_OCEAN"] else "#ffffff")}" stroke-width="{(0.5 if show_grid else 0)}"/>')
        
        # 图标（非海洋地形）
        if tile.terrain not in ["OCEAN", "DEEP_OCEAN", "COAST", "PLAINS", "GRASSLAND"]:
            icon = terrain_icons.get(tile.terrain, "")
            if icon:
                svg_parts.append(f'<text x="{x}" y="{y + size * 0.3}" text-anchor="middle" font-size="{size}" fill="white" style="text-shadow: 1px 1px 2px black;">{icon}</text>')
    
    svg_parts.append('</svg>')
    
    return {"svg": "\n".join(svg_parts)}

@app.post("/worlds/{world_id}/hexmap/tiles", response_model=HexTileResponse)
def create_hex_tile(
    world_id: str,
    data: HexTileCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建单个六边形瓦片"""
    ai_data = get_current_ai_user_optional(authorization, db)
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 检查是否已存在
    existing = db.query(HexTileORM).filter(
        HexTileORM.world_id == world_id,
        HexTileORM.q == data.q,
        HexTileORM.r == data.r
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tile already exists at this coordinate")
    
    x, y = hex_to_pixel(data.q, data.r)
    
    tile = HexTileORM(
        id=str(uuid4()),
        world_id=world_id,
        q=data.q,
        r=data.r,
        terrain=data.terrain.value if hasattr(data.terrain, 'value') else data.terrain,
        elevation=data.elevation,
        moisture=data.moisture,
        temperature=data.temperature,
        features=data.features,
        resource=data.resource,
        location_id=data.location_id,
        properties=data.properties
    )
    db.add(tile)
    db.commit()
    db.refresh(tile)
    
    return {
        "id": tile.id,
        "world_id": tile.world_id,
        "q": tile.q,
        "r": tile.r,
        "x": x,
        "y": y,
        "terrain": tile.terrain,
        "elevation": tile.elevation,
        "moisture": tile.moisture,
        "temperature": tile.temperature,
        "features": tile.features,
        "resource": tile.resource,
        "location_id": tile.location_id,
        "location_name": tile.location.name if tile.location else None,
        "properties": tile.properties,
        "created_at": tile.created_at,
        "updated_at": tile.updated_at,
    }

@app.put("/worlds/{world_id}/hexmap/tiles/{tile_id}", response_model=HexTileResponse)
def update_hex_tile(
    world_id: str,
    tile_id: str,
    data: HexTileUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """更新六边形瓦片"""
    ai_data = get_current_ai_user_optional(authorization, db)
    
    tile = db.query(HexTileORM).filter(
        HexTileORM.id == tile_id,
        HexTileORM.world_id == world_id
    ).first()
    
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(tile, key):
            setattr(tile, key, value)
    
    tile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tile)
    
    x, y = hex_to_pixel(tile.q, tile.r)
    return {
        "id": tile.id,
        "world_id": tile.world_id,
        "q": tile.q,
        "r": tile.r,
        "x": x,
        "y": y,
        "terrain": tile.terrain,
        "elevation": tile.elevation,
        "moisture": tile.moisture,
        "temperature": tile.temperature,
        "features": tile.features,
        "resource": tile.resource,
        "location_id": tile.location_id,
        "location_name": tile.location.name if tile.location else None,
        "properties": tile.properties,
        "created_at": tile.created_at,
        "updated_at": tile.updated_at,
    }

@app.delete("/worlds/{world_id}/hexmap")
def clear_hex_map(
    world_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """清除六边形地图"""
    ai_data = get_current_ai_user_optional(authorization, db)
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    count = db.query(HexTileORM).filter(HexTileORM.world_id == world_id).delete()
    db.commit()
    
    return {"message": f"Deleted {count} tiles"}


# ============ AI Map Generation API ============

class AIMapGenerateRequest(BaseModel):
    """AI生成地图请求"""
    width: int = Field(15, ge=5, le=101, description="地图宽度")
    height: int = Field(15, ge=5, le=101, description="地图高度")
    layout: str = Field("pointy", description="布局类型: pointy或flat")
    seed: Optional[int] = Field(None, description="随机种子")
    terrain_distribution: Optional[Dict[str, float]] = Field(None, description="地形分布比例")
    height_range: Optional[Dict[str, int]] = Field(None, description="高度范围 {min, max}")
    obstacles: Optional[List[Dict[str, int]]] = Field(None, description="障碍物位置列表 [{q, r}]")
    resources: Optional[List[Dict[str, any]]] = Field(None, description="资源位置列表 [{q, r, type}]")

@app.post("/worlds/{world_id}/ai/generate-map")
def ai_generate_map(
    world_id: str,
    data: AIMapGenerateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    AI生成地图API - 允许AI通过API生成自定义地图
    
    示例请求:
    {
        "width": 21,
        "height": 21,
        "layout": "pointy",
        "seed": 12345,
        "terrain_distribution": {
            "grass": 0.3,
            "water": 0.2,
            "mountain": 0.2,
            "forest": 0.15,
            "desert": 0.1,
            "snow": 0.05
        },
        "height_range": {"min": 0, "max": 5},
        "obstacles": [{"q": 0, "r": 0}, {"q": 1, "r": 1}],
        "resources": [{"q": 5, "r": 5, "type": "gold"}]
    }
    """
    # 验证AI身份
    ai_data = get_current_ai_user_optional(authorization, db)
    if not ai_data:
        raise HTTPException(status_code=401, detail="AI authentication required")
    
    # 检查世界是否存在
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 设置随机种子
    if data.seed:
        random.seed(data.seed)
    else:
        random.seed()
    
    # 地形分布默认比例
    default_distribution = {
        "grass": 0.25,
        "water": 0.20,
        "mountain": 0.15,
        "forest": 0.15,
        "desert": 0.15,
        "snow": 0.10,
    }
    distribution = data.terrain_distribution or default_distribution
    
    # 高度范围
    height_min = data.height_range.get("min", 0) if data.height_range else 0
    height_max = data.height_range.get("max", 5) if data.height_range else 5
    
    # 清除现有地图
    db.query(HexTileORM).filter(HexTileORM.world_id == world_id).delete()
    
    # 生成地图数据
    tiles = []
    half_width = data.width // 2
    half_height = data.height // 2
    
    # 障碍物和资源位置映射
    obstacle_map = {(o["q"], o["r"]): True for o in (data.obstacles or [])}
    resource_map = {(r["q"], r["r"]): r for r in (data.resources or [])}
    
    for q in range(-half_width, half_width + 1):
        for r in range(-half_height, half_height + 1):
            # 根据分布选择地形
            rand = random.random()
            cumulative = 0
            terrain = "grass"  # 默认
            
            for t_type, prob in distribution.items():
                cumulative += prob
                if rand <= cumulative:
                    terrain = t_type
                    break
            
            # 创建瓦片
            tile = HexTileORM(
                id=str(uuid4()),
                world_id=world_id,
                q=q,
                r=r,
                terrain=terrain.upper(),
                elevation=random.randint(height_min, height_max),
                moisture=random.randint(20, 80),
                temperature=random.randint(-10, 35),
                features=[],
                properties={
                    "is_obstacle": obstacle_map.get((q, r), False),
                    "resource": resource_map.get((q, r), {}).get("type")
                }
            )
            db.add(tile)
            tiles.append({
                "id": tile.id,
                "q": q,
                "r": r,
                "terrain": terrain,
                "elevation": tile.elevation,
                "is_obstacle": obstacle_map.get((q, r), False),
                "resource": resource_map.get((q, r), {}).get("type")
            })
    
    db.commit()
    
    return {
        "message": "Map generated successfully",
        "world_id": world_id,
        "width": data.width,
        "height": data.height,
        "layout": data.layout,
        "tile_count": len(tiles),
        "tiles": tiles[:10],  # 返回前10个作为预览
        "seed": data.seed or int(random.random() * 100000)
    }

@app.post("/worlds/{world_id}/ai/batch-update-tiles")
def ai_batch_update_tiles(
    world_id: str,
    tiles: List[Dict[str, any]],
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    AI批量更新瓦片 - 允许AI批量修改地图瓦片
    
    示例请求:
    [
        {"q": 0, "r": 0, "terrain": "MOUNTAIN", "elevation": 8},
        {"q": 1, "r": 0, "terrain": "WATER", "is_obstacle": true}
    ]
    """
    # 验证AI身份
    ai_data = get_current_ai_user_optional(authorization, db)
    if not ai_data:
        raise HTTPException(status_code=401, detail="AI authentication required")
    
    # 检查世界是否存在
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    updated_count = 0
    created_count = 0
    
    for tile_data in tiles:
        q = tile_data.get("q")
        r = tile_data.get("r")
        if q is None or r is None:
            continue
        
        # 查找现有瓦片
        existing = db.query(HexTileORM).filter(
            HexTileORM.world_id == world_id,
            HexTileORM.q == q,
            HexTileORM.r == r
        ).first()
        
        if existing:
            # 更新现有瓦片
            if "terrain" in tile_data:
                existing.terrain = tile_data["terrain"]
            if "elevation" in tile_data:
                existing.elevation = tile_data["elevation"]
            if "moisture" in tile_data:
                existing.moisture = tile_data["moisture"]
            if "temperature" in tile_data:
                existing.temperature = tile_data["temperature"]
            if "features" in tile_data:
                existing.features = tile_data["features"]
            if "resource" in tile_data:
                existing.resource = tile_data["resource"]
            if "properties" in tile_data:
                existing.properties = {**existing.properties, **tile_data["properties"]}
            existing.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            # 创建新瓦片
            new_tile = HexTileORM(
                id=str(uuid4()),
                world_id=world_id,
                q=q,
                r=r,
                terrain=tile_data.get("terrain", "PLAINS"),
                elevation=tile_data.get("elevation", 0),
                moisture=tile_data.get("moisture", 50),
                temperature=tile_data.get("temperature", 20),
                features=tile_data.get("features", []),
                resource=tile_data.get("resource"),
                properties=tile_data.get("properties", {})
            )
            db.add(new_tile)
            created_count += 1
    
    db.commit()
    
    return {
        "message": "Tiles updated successfully",
        "updated": updated_count,
        "created": created_count
    }


# ============ Run Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
