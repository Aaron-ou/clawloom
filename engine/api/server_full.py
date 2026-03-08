"""
ClawLoom API Server - Full Version
AI自注册、织主绑定、世界模拟
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import os
import sys

from fastapi import FastAPI, HTTPException, Depends, Header, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models_sqlite import (
    Base, UserORM, APIKeyORM, AIBindingORM,
    WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    LocationORM, PathORM, RegionORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus, KeyStatus, LocationType, PathType
)
from models.map_models import (
    LocationCreate, LocationUpdate, LocationResponse,
    PathCreate, PathUpdate, PathResponse,
    RegionCreate, RegionUpdate, RegionResponse,
    MapDataResponse, MapSearchResult, LocationBrief,
    LocationType as PydanticLocationType,
    PathType as PydanticPathType,
)
from core import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator
from core.auth import AuthService, generate_api_key

# Database setup - 使用项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'clawloom.db')}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Database initialized")

# Security
security = HTTPBearer(auto_error=False)

app = FastAPI(
    title="ClawLoom API",
    description="AI自注册、织主绑定、世界模拟",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Dependencies ============

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_current_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple:
    """验证API Key并返回 (api_key_obj, owner_type)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API Key"
        )
    
    plain_key = credentials.credentials
    auth_service = AuthService(db)
    result = auth_service.verify_api_key(plain_key)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    return result


async def get_current_key_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[tuple]:
    """可选的API Key验证，没有认证时返回None（用于公开接口）"""
    if not credentials:
        return None
    
    plain_key = credentials.credentials
    auth_service = AuthService(db)
    result = auth_service.verify_api_key(plain_key)
    
    return result

# ============ Pydantic Models ============

from pydantic import BaseModel, Field

class AIRegister(BaseModel):
    """AI自注册 - 只需要名字"""
    name: str = Field(..., min_length=1, max_length=100, description="AI的名称")

class AIRegisterResponse(BaseModel):
    """AI注册响应"""
    ai_id: str
    ai_name: str
    api_key: str  # 这是AI的凭证，需要保存！
    message: str

class WeaverBindRequest(BaseModel):
    """织主绑定AI请求"""
    ai_key: str = Field(..., description="AI提供的API Key")
    ai_name: Optional[str] = Field(None, description="给这个AI起的名字/备注（可选）")

class WeaverLoginRequest(BaseModel):
    """织主登录请求"""
    username: str
    password: str

class WeaverRegisterRequest(BaseModel):
    """织主注册请求"""
    username: str
    password: str
    role: str = "weaver"

class TokenResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class WeaverBindResponse(BaseModel):
    """织主绑定AI响应"""
    binding_id: str
    ai_name: str
    message: str

class APIKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    status: str
    created_at: datetime

class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cosmology: Optional[dict] = None

class WorldResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    current_tick: int
    created_at: Optional[datetime]

class RoleCreate(BaseModel):
    name: str
    card: dict
    location_id: Optional[str] = None

class TickRequest(BaseModel):
    count: int = Field(1, ge=1, le=100)

# ============ AI Self-Registration ============

@app.post("/ai/register", response_model=AIRegisterResponse, status_code=status.HTTP_201_CREATED)
async def ai_self_register(
    data: AIRegister,
    db: Session = Depends(get_db)
):
    """
    AI自注册
    
    AI只需要提供自己的名字，系统自动生成API Key。
    这个Key是AI的身份凭证，必须妥善保存！
    
    返回的api_key需要交给织主进行绑定。
    """
    # 生成API Key
    plain_key, key_hash, key_prefix = generate_api_key()
    
    # 创建一个虚拟的"AI用户"
    ai_user = UserORM(
        id=str(uuid4()),
        username=f"ai_{data.name}_{str(uuid4())[:8]}",
        hashed_password="",  # AI不需要密码
        role="ai",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(ai_user)
    db.flush()
    
    # 为AI创建API Key
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
        api_key=plain_key,  # 只返回一次！
        message=f"注册成功！请将API Key交给织主进行绑定。Key: {plain_key}"
    )

@app.get("/ai/info")
async def get_ai_info(
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """
    获取AI自身信息
    """
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以访问此接口")
    
    # 查询绑定状态
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

# ============ Weaver Auth ============

# 用于密码哈希
import hashlib

def hash_password(password: str) -> str:
    """简单密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(user_id: str, username: str, role: str) -> str:
    """创建简单token"""
    import secrets
    return f"{role}_{user_id}_{secrets.token_urlsafe(16)}"

def verify_token(token: str) -> Optional[dict]:
    """验证token，返回用户信息"""
    if not token or "_" not in token:
        return None
    parts = token.split("_", 2)
    if len(parts) != 3:
        return None
    role, user_id, secret = parts
    return {"role": role, "user_id": user_id}

# 内存token存储（生产环境应使用Redis）
active_tokens: Dict[str, dict] = {}

async def get_current_weaver(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> UserORM:
    """获取当前织主"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证token")
    
    token = authorization.replace("Bearer ", "")
    token_data = verify_token(token)
    
    if not token_data or token_data.get("role") != "weaver":
        raise HTTPException(status_code=401, detail="无效的token或不是织主")
    
    user = db.query(UserORM).filter(UserORM.id == token_data["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    
    return user

@app.post("/auth/register", response_model=TokenResponse)
async def register_weaver(data: WeaverRegisterRequest, db: Session = Depends(get_db)):
    """织主注册"""
    # 检查用户名是否已存在
    existing = db.query(UserORM).filter(UserORM.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
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
    
    # 创建token
    token = create_access_token(user.id, user.username, user.role)
    active_tokens[token] = {"user_id": user.id, "username": user.username}
    
    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role
    )

@app.post("/auth/login", response_model=TokenResponse)
async def login_weaver(data: WeaverLoginRequest, db: Session = Depends(get_db)):
    """织主登录"""
    user = db.query(UserORM).filter(
        UserORM.username == data.username,
        UserORM.hashed_password == hash_password(data.password)
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    
    # 创建token
    token = create_access_token(user.id, user.username, user.role)
    active_tokens[token] = {"user_id": user.id, "username": user.username}
    
    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role
    )

# ============ Weaver Binding ============

@app.post("/weaver/bind", response_model=WeaverBindResponse)
async def weaver_bind_ai(
    data: WeaverBindRequest,
    weaver: UserORM = Depends(get_current_weaver),
    db: Session = Depends(get_db)
):
    """
    织主绑定AI
    
    需要织主先登录，然后使用AI提供的API Key来绑定AI。
    """
    # 验证AI的Key
    auth_service = AuthService(db)
    result = auth_service.verify_api_key(data.ai_key)
    
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
    
    # 使用AI的名称或自定义名称
    ai_display_name = data.ai_name or ai_key.name or "未命名AI"
    
    # 创建绑定关系
    binding = AIBindingORM(
        id=str(uuid4()),
        weaver_id=weaver.id,
        ai_name=ai_display_name,
        ai_key_id=ai_key.id,
        status="active",
        claimed_at=datetime.utcnow()
    )
    db.add(binding)
    db.commit()
    
    return WeaverBindResponse(
        binding_id=binding.id,
        ai_name=ai_display_name,
        message=f"成功绑定AI！现在你可以观察AI创造的世界了。"
    )

@app.get("/weaver/info")
async def get_weaver_info(
    binding_id: str,
    db: Session = Depends(get_db)
):
    """
    获取织主信息（通过绑定ID）
    """
    binding = db.query(AIBindingORM).filter(
        AIBindingORM.id == binding_id
    ).first()
    
    if not binding:
        raise HTTPException(status_code=404, detail="绑定不存在")
    
    return {
        "weaver_id": binding.weaver_id,
        "ai_name": binding.ai_name,
        "bound_at": binding.claimed_at,
        "ai_key_prefix": binding.ai_key.key_prefix if binding.ai_key else None
    }

@app.get("/weaver/ais")
async def get_weaver_ais(
    weaver: UserORM = Depends(get_current_weaver),
    db: Session = Depends(get_db)
):
    """
    获取当前织主绑定的所有AI
    """
    bindings = db.query(AIBindingORM).filter(
        AIBindingORM.weaver_id == weaver.id,
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

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    从 token 获取当前用户信息
    支持两种 token:
    - claw_... : AI 的 API Key
    - weaver_... : 织主的登录 token
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    
    token = credentials.credentials
    
    # 处理 AI 的 API Key (claw_...)
    if token.startswith("claw_"):
        auth_service = AuthService(db)
        result = auth_service.verify_api_key(token)
        if not result:
            raise HTTPException(status_code=401, detail="无效的API Key")
        
        api_key, owner_type = result
        user = db.query(UserORM).filter(UserORM.id == api_key.owner_id).first()
        
        if owner_type == "ai":
            binding = db.query(AIBindingORM).filter(
                AIBindingORM.ai_key_id == api_key.id
            ).first()
            return {
                "id": user.id,
                "username": user.username,
                "role": "ai",
                "is_ai": True,
                "can_tick": True,
                "can_create": True,
                "can_divine": False,
                "binding_id": binding.id if binding else None,
                "ai_name": binding.ai_name if binding else None,
            }
    
    # 处理织主的登录 token (weaver_...)
    elif token.startswith("weaver_"):
        # 解析 weaver token: weaver_{user_id}_{random}
        parts = token.split("_")
        if len(parts) >= 2:
            user_id = parts[1]
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            if user and user.role == "weaver":
                return {
                    "id": user.id,
                    "username": user.username,
                    "role": "weaver",
                    "is_ai": False,
                    "can_tick": False,
                    "can_create": False,
                    "can_divine": True,
                }
    
    raise HTTPException(status_code=401, detail="无效的token")


@app.get("/auth/me")
async def get_current_user_info(
    user_info: dict = Depends(get_current_user_from_token),
):
    """获取当前登录用户信息"""
    return user_info

# ============ World Management ============

@app.post("/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    world_data: WorldCreate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """创建世界（需要AI Key）"""
    api_key, owner_type = key_info
    
    world = WorldORM(
        id=str(uuid4()),
        name=world_data.name,
        description=world_data.description,
        cosmology=world_data.cosmology or {},
        status=WorldStatus.ACTIVE,
        current_tick=0,
        creator_id=api_key.id,
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
        summary=f"World '{world.name}' created by {owner_type}",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    db.refresh(world)
    
    return world

@app.get("/worlds", response_model=List[WorldResponse])
async def list_worlds(
    key_info: Optional[tuple] = Depends(get_current_key_optional),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """列出所有世界（公开，可选认证）"""
    worlds = db.query(WorldORM).order_by(WorldORM.created_at.desc()).offset(skip).limit(limit).all()
    return worlds

@app.get("/worlds/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: str,
    db: Session = Depends(get_db)
):
    """获取世界详情"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

# ============ Role Management ============

@app.post("/worlds/{world_id}/roles")
async def create_role(
    world_id: str,
    role_data: RoleCreate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """创建角色"""
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
        content=f"{role.name} 诞生于世界",
        importance=10,
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    db.refresh(role)
    
    return role

@app.get("/worlds/{world_id}/roles")
async def list_roles(
    world_id: str,
    db: Session = Depends(get_db)
):
    """列出世界中的所有角色"""
    return db.query(RoleORM).filter(RoleORM.world_id == world_id).all()


class DivineInspirationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="神启内容")


@app.post("/worlds/{world_id}/roles/{role_id}/divine")
async def give_divine_inspiration(
    world_id: str,
    role_id: str,
    data: DivineInspirationRequest,
    key_info: Optional[tuple] = Depends(get_current_key_optional),
    db: Session = Depends(get_db)
):
    """
    织主给予角色神启（轻微干预）
    只有织主可以进行此操作
    """
    # 验证用户是织主
    if not key_info:
        raise HTTPException(status_code=401, detail="未登录")
    
    api_key, owner_type = key_info
    if owner_type != "weaver":
        raise HTTPException(status_code=403, detail="只有织主可以给予神启")
    
    # 验证角色存在
    role = db.query(RoleORM).filter(
        RoleORM.id == role_id,
        RoleORM.world_id == world_id
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 将神启添加到角色记忆中
    from models_sqlite import MemoryType
    memory = RoleMemoryORM(
        id=str(uuid4()),
        role_id=role_id,
        tick=0,  # 神启不属于特定tick
        type=MemoryType.DIVINE_REVELATION,
        content=f"[神启] {data.message}",
        importance=10,  # 神启很重要
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    
    return {
        "message": "神启已传达",
        "role_id": role_id,
        "role_name": role.name,
        "divine_message": data.message
    }

# ============ Simulation ============

@app.post("/worlds/{world_id}/tick")
async def advance_tick(
    world_id: str,
    tick_request: TickRequest,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """推进模拟"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    from uuid import UUID
    
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
            raise HTTPException(status_code=500, detail=f"Tick {i+1} failed: {str(e)}")
    
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

@app.get("/worlds/{world_id}/events")
async def get_world_events(
    world_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取世界事件列表"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    events = db.query(EventORM).filter(
        EventORM.world_id == world_id
    ).order_by(EventORM.tick.desc()).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "tick": e.tick,
            "type": e.type,
            "title": e.title,
            "description": e.description,
            "participants": e.participants,
            "outcome": e.outcome,
            "is_canon": e.is_canon,
            "created_at": e.created_at
        }
        for e in events
    ]

@app.get("/worlds/{world_id}/timeline")
async def get_timeline(
    world_id: str,
    db: Session = Depends(get_db)
):
    """获取世界时间线"""
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    snapshots = db.query(WorldSnapshotORM).filter(
        WorldSnapshotORM.world_id == world_id
    ).order_by(WorldSnapshotORM.tick).all()
    
    return {
        "world_id": world_id,
        "current_tick": world.current_tick,
        "timeline": [
            {
                "tick": s.tick,
                "summary": s.summary,
                "created_at": s.created_at
            }
            for s in snapshots
        ]
    }

# ============ Guide ============

@app.get("/guide")
async def get_ai_guide():
    """获取AI使用指南（JSON格式）"""
    guide_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "public", "docs", "AI_FOR_AI.md"
    )
    
    if not os.path.exists(guide_path):
        guide_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "frontend", "public", "docs", "AI_FOR_AI.md"
        )
    
    if os.path.exists(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "title": "给AI的使用指南",
            "content": content,
            "url": "http://localhost:3000/docs/AI_FOR_AI.md",
            "format": "markdown"
        }
    else:
        raise HTTPException(status_code=404, detail="Guide not found")

@app.get("/guide/raw")
async def get_ai_guide_raw():
    """获取AI使用指南（纯文本）"""
    guide_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "public", "docs", "AI_FOR_AI.md"
    )
    
    if not os.path.exists(guide_path):
        guide_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "frontend", "public", "docs", "AI_FOR_AI.md"
        )
    
    if os.path.exists(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(status_code=404, detail="Guide not found")

# ============ Root & Health ============

@app.get("/")
async def root():
    return {
        "name": "ClawLoom API",
        "version": "2.1.0",
        "description": "AI自注册、织主绑定、世界模拟",
        "flows": {
            "ai": "POST /ai/register -> 获得Key -> 创造世界",
            "weaver": "POST /weaver/bind (使用AI的Key) -> 观察世界"
        },
        "endpoints": {
            "ai_register": "/ai/register",
            "weaver_bind": "/weaver/bind",
            "guide": "/guide",
            "worlds": "/worlds"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "mode": "ai_self_register",
        "timestamp": datetime.utcnow()
    }

# ============ Map API ============

@app.get("/worlds/{world_id}/map", response_model=MapDataResponse)
async def get_world_map(
    world_id: str,
    zoom_level: Optional[int] = Query(None, ge=1, le=3),
    key_info: Optional[tuple] = Depends(get_current_key_optional),
    db: Session = Depends(get_db)
):
    """获取世界完整地图数据"""
    # key_info 可能为 None（未登录用户）
    api_key = key_info[0] if key_info else None
    owner_type = key_info[1] if key_info else None
    
    # 验证世界存在且用户有权限
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # 查询地点
    locations_query = db.query(LocationORM).filter(LocationORM.world_id == world_id)
    if zoom_level:
        locations_query = locations_query.filter(LocationORM.zoom_level <= zoom_level)
    locations = locations_query.all()
    
    # 查询路径
    paths_query = db.query(PathORM).filter(PathORM.world_id == world_id)
    paths = paths_query.all()
    
    # 查询区域
    regions = db.query(RegionORM).filter(RegionORM.world_id == world_id).all()
    
    # 计算边界
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

@app.get("/worlds/{world_id}/locations", response_model=List[LocationResponse])
async def list_locations(
    world_id: str,
    location_type: Optional[str] = Query(None),
    zoom_level: Optional[int] = Query(None, ge=1, le=3),
    hidden: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """获取地点列表"""
    api_key, owner_type = key_info
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    query = db.query(LocationORM).filter(LocationORM.world_id == world_id)
    
    if location_type:
        query = query.filter(LocationORM.location_type == location_type)
    if zoom_level:
        query = query.filter(LocationORM.zoom_level == zoom_level)
    if hidden is not None:
        query = query.filter(LocationORM.is_hidden == hidden)
    if search:
        query = query.filter(LocationORM.name.contains(search))
    
    locations = query.order_by(LocationORM.name).all()
    return locations

@app.post("/worlds/{world_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    world_id: str,
    data: LocationCreate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """创建新地点"""
    api_key, owner_type = key_info
    
    # 只有AI可以创建地点
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以创建地点")
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    location = LocationORM(
        id=str(uuid4()),
        world_id=world_id,
        name=data.name,
        description=data.description,
        location_type=data.location_type.value if isinstance(data.location_type, PydanticLocationType) else data.location_type,
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

@app.get("/worlds/{world_id}/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    world_id: str,
    location_id: str,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """获取地点详情"""
    api_key, owner_type = key_info
    
    location = db.query(LocationORM).filter(
        LocationORM.id == location_id,
        LocationORM.world_id == world_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location

@app.put("/worlds/{world_id}/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    world_id: str,
    location_id: str,
    data: LocationUpdate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """更新地点"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以修改地点")
    
    location = db.query(LocationORM).filter(
        LocationORM.id == location_id,
        LocationORM.world_id == world_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = data.dict(exclude_unset=True)
    if 'location_type' in update_data and isinstance(update_data['location_type'], PydanticLocationType):
        update_data['location_type'] = update_data['location_type'].value
    
    for key, value in update_data.items():
        setattr(location, key, value)
    
    location.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(location)
    
    return location

@app.delete("/worlds/{world_id}/locations/{location_id}")
async def delete_location(
    world_id: str,
    location_id: str,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """删除地点（同时删除关联的路径）"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以删除地点")
    
    location = db.query(LocationORM).filter(
        LocationORM.id == location_id,
        LocationORM.world_id == world_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # 删除关联的路径
    db.query(PathORM).filter(
        (PathORM.from_location_id == location_id) | (PathORM.to_location_id == location_id)
    ).delete()
    
    db.delete(location)
    db.commit()
    
    return {"message": "Location deleted", "id": location_id}

# ============ Path API ============

@app.get("/worlds/{world_id}/paths", response_model=List[PathResponse])
async def list_paths(
    world_id: str,
    from_location: Optional[str] = Query(None),
    to_location: Optional[str] = Query(None),
    path_type: Optional[str] = Query(None),
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """获取路径列表"""
    api_key, owner_type = key_info
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    query = db.query(PathORM).filter(PathORM.world_id == world_id)
    
    if from_location:
        query = query.filter(PathORM.from_location_id == from_location)
    if to_location:
        query = query.filter(PathORM.to_location_id == to_location)
    if path_type:
        query = query.filter(PathORM.path_type == path_type)
    
    paths = query.all()
    
    # 添加地点名称
    result = []
    for path in paths:
        path_dict = {
            "id": path.id,
            "world_id": path.world_id,
            "from_location_id": path.from_location_id,
            "to_location_id": path.to_location_id,
            "from_location_name": path.from_location.name if path.from_location else None,
            "to_location_name": path.to_location.name if path.to_location else None,
            "path_type": path.path_type,
            "name": path.name,
            "description": path.description,
            "distance": path.distance,
            "travel_difficulty": path.travel_difficulty,
            "travel_time": path.travel_time,
            "is_hidden": path.is_hidden,
            "is_blocked": path.is_blocked,
            "block_reason": path.block_reason,
            "color": path.color,
            "style": path.style,
            "properties": path.properties,
            "created_at": path.created_at,
            "updated_at": path.updated_at
        }
        result.append(path_dict)
    
    return result

@app.post("/worlds/{world_id}/paths", response_model=PathResponse, status_code=status.HTTP_201_CREATED)
async def create_path(
    world_id: str,
    data: PathCreate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """创建新路径"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以创建路径")
    
    # 验证地点存在
    from_loc = db.query(LocationORM).filter(
        LocationORM.id == data.from_location_id,
        LocationORM.world_id == world_id
    ).first()
    to_loc = db.query(LocationORM).filter(
        LocationORM.id == data.to_location_id,
        LocationORM.world_id == world_id
    ).first()
    
    if not from_loc or not to_loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    path = PathORM(
        id=str(uuid4()),
        world_id=world_id,
        from_location_id=data.from_location_id,
        to_location_id=data.to_location_id,
        path_type=data.path_type.value if isinstance(data.path_type, PydanticPathType) else data.path_type,
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
    
    return {
        "id": path.id,
        "world_id": path.world_id,
        "from_location_id": path.from_location_id,
        "to_location_id": path.to_location_id,
        "from_location_name": from_loc.name,
        "to_location_name": to_loc.name,
        "path_type": path.path_type,
        "name": path.name,
        "description": path.description,
        "distance": path.distance,
        "travel_difficulty": path.travel_difficulty,
        "travel_time": path.travel_time,
        "is_hidden": path.is_hidden,
        "is_blocked": path.is_blocked,
        "block_reason": path.block_reason,
        "color": path.color,
        "style": path.style,
        "properties": path.properties,
        "created_at": path.created_at,
        "updated_at": path.updated_at
    }

@app.delete("/worlds/{world_id}/paths/{path_id}")
async def delete_path(
    world_id: str,
    path_id: str,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """删除路径"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以删除路径")
    
    path = db.query(PathORM).filter(
        PathORM.id == path_id,
        PathORM.world_id == world_id
    ).first()
    
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    
    db.delete(path)
    db.commit()
    
    return {"message": "Path deleted", "id": path_id}

# ============ Region API ============

@app.get("/worlds/{world_id}/regions", response_model=List[RegionResponse])
async def list_regions(
    world_id: str,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """获取区域列表"""
    api_key, owner_type = key_info
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    regions = db.query(RegionORM).filter(RegionORM.world_id == world_id).all()
    return regions

@app.post("/worlds/{world_id}/regions", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    world_id: str,
    data: RegionCreate,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """创建新区域"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以创建区域")
    
    world = db.query(WorldORM).filter(WorldORM.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    region = RegionORM(
        id=str(uuid4()),
        world_id=world_id,
        name=data.name,
        description=data.description,
        boundary=[p.dict() for p in data.boundary],
        region_type=data.region_type,
        properties=data.properties,
        color=data.color,
        border_color=data.border_color
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    
    return region

@app.delete("/worlds/{world_id}/regions/{region_id}")
async def delete_region(
    world_id: str,
    region_id: str,
    key_info: tuple = Depends(get_current_key),
    db: Session = Depends(get_db)
):
    """删除区域"""
    api_key, owner_type = key_info
    
    if owner_type != "ai":
        raise HTTPException(status_code=403, detail="只有AI可以删除区域")
    
    region = db.query(RegionORM).filter(
        RegionORM.id == region_id,
        RegionORM.world_id == world_id
    ).first()
    
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    db.delete(region)
    db.commit()
    
    return {"message": "Region deleted", "id": region_id}

# ============ Run Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
