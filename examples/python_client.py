"""
ClawLoom Python 客户端示例

展示如何使用Python与ClawLoom API交互
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class World:
    id: str
    name: str
    status: str
    current_tick: int

@dataclass
class Role:
    id: str
    name: str
    status: str
    health: int
    influence: int

@dataclass
class Event:
    id: str
    tick: int
    type: str
    title: str
    description: str

class ClawLoomClient:
    """ClawLoom API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Claw-Key": self.api_key
        }
    
    async def close(self):
        await self.client.aclose()
    
    # ===== 世界管理 =====
    
    async def create_world(self, name: str, description: str = "") -> World:
        """创建新世界"""
        response = await self.client.post(
            f"{self.base_url}/worlds",
            headers=self._headers(),
            json={"name": name, "description": description}
        )
        response.raise_for_status()
        data = response.json()
        return World(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            current_tick=data["current_tick"]
        )
    
    async def list_worlds(self) -> List[World]:
        """列出所有世界"""
        response = await self.client.get(
            f"{self.base_url}/worlds",
            headers=self._headers()
        )
        response.raise_for_status()
        return [
            World(
                id=w["id"],
                name=w["name"],
                status=w["status"],
                current_tick=w["current_tick"]
            )
            for w in response.json()
        ]
    
    async def delete_world(self, world_id: str):
        """删除世界"""
        response = await self.client.delete(
            f"{self.base_url}/worlds/{world_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    # ===== 角色管理 =====
    
    async def create_role(
        self,
        world_id: str,
        name: str,
        drives: List[Dict[str, Any]],
        public_memory: List[str],
        risk_tolerance: str = "medium"
    ) -> Role:
        """创建角色"""
        card = {
            "drives": drives,
            "memory": {"public": public_memory},
            "decision_style": {"risk_tolerance": risk_tolerance}
        }
        
        response = await self.client.post(
            f"{self.base_url}/worlds/{world_id}/roles",
            headers=self._headers(),
            json={"name": name, "card": card}
        )
        response.raise_for_status()
        data = response.json()
        return Role(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            health=data["health"],
            influence=data["influence"]
        )
    
    async def list_roles(self, world_id: str) -> List[Role]:
        """列出世界中的所有角色"""
        response = await self.client.get(
            f"{self.base_url}/worlds/{world_id}/roles",
            headers=self._headers()
        )
        response.raise_for_status()
        return [
            Role(
                id=r["id"],
                name=r["name"],
                status=r["status"],
                health=r["health"],
                influence=r["influence"]
            )
            for r in response.json()
        ]
    
    # ===== 模拟控制 =====
    
    async def advance_tick(self, world_id: str, count: int = 1) -> Dict[str, Any]:
        """推进模拟"""
        response = await self.client.post(
            f"{self.base_url}/worlds/{world_id}/tick",
            headers=self._headers(),
            json={"count": count}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_timeline(self, world_id: str) -> List[Dict[str, Any]]:
        """获取时间线"""
        response = await self.client.get(
            f"{self.base_url}/worlds/{world_id}/timeline",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["timeline"]
    
    async def list_events(
        self,
        world_id: str,
        tick: Optional[int] = None,
        limit: int = 100
    ) -> List[Event]:
        """列出事件"""
        params = f"?limit={limit}"
        if tick is not None:
            params += f"&tick={tick}"
        
        response = await self.client.get(
            f"{self.base_url}/worlds/{world_id}/events{params}",
            headers=self._headers()
        )
        response.raise_for_status()
        return [
            Event(
                id=e["id"],
                tick=e["tick"],
                type=e["type"],
                title=e["title"],
                description=e["description"]
            )
            for e in response.json()
        ]


# ===== 使用示例 =====

async def example_1_simple_story():
    """示例1：创建一个简单的两角色故事"""
    client = ClawLoomClient()
    
    try:
        # 1. 创建世界
        world = await client.create_world(
            name="沙漠绿洲",
            description="资源稀缺引发的争斗"
        )
        print(f"创建世界: {world.name} ({world.id})")
        
        # 2. 创建守护者
        guardian = await client.create_role(
            world_id=world.id,
            name="绿洲守护者",
            drives=[
                {"id": "protect", "weight": 0.95},
                {"id": "survival", "weight": 0.7}
            ],
            public_memory=["守护这片绿洲已经十年", "精通水源管理"],
            risk_tolerance="low"
        )
        print(f"创建角色: {guardian.name}")
        
        # 3. 创建流浪者
        wanderer = await client.create_role(
            world_id=world.id,
            name="饥渴的流浪者",
            drives=[
                {"id": "survival", "weight": 1.0},
                {"id": "wealth", "weight": 0.5}
            ],
            public_memory=["穿越沙漠三天三夜", "极度缺水"],
            risk_tolerance="high"
        )
        print(f"创建角色: {wanderer.name}")
        
        # 4. 推进模拟
        print("\n开始模拟...")
        for i in range(5):
            result = await client.advance_tick(world.id, count=1)
            print(f"\n  Tick {result['tick']}: {result['summary']}")
            print(f"  决策: {result['decisions_count']} | 冲突: {result['conflicts_count']} | 事件: {result['events_count']}")
            
            if result['events']:
                for event in result['events']:
                    print(f"    [{event['type']}] {event['title']}")
        
        # 5. 查看最终状态
        roles = await client.list_roles(world.id)
        print("\n角色最终状态:")
        for role in roles:
            print(f"  {role.name}: 健康{role.health} | 影响力{role.influence} | {role.status}")
        
        # 6. 获取完整时间线
        timeline = await client.get_timeline(world.id)
        print("\n故事时间线:")
        for entry in timeline:
            if entry['event_count'] > 0:
                print(f"  Tick {entry['tick']}: {entry['summary']}")
        
        return world.id
        
    finally:
        await client.close()


async def example_2_batch_creation():
    """示例2：批量创建角色并观察互动"""
    client = ClawLoomClient()
    
    try:
        # 创建世界
        world = await client.create_world(
            name="王国议会",
            description="不同派系争夺权力"
        )
        print(f"创建世界: {world.name}")
        
        # 角色模板
        characters = [
            ("保守派领袖", "stability", "low"),
            ("改革派先锋", "change", "high"),
            ("中立调停者", "balance", "medium"),
            ("阴谋家", "power", "high"),
        ]
        
        # 批量创建
        for name, drive, risk in characters:
            await client.create_role(
                world_id=world.id,
                name=name,
                drives=[{"id": drive, "weight": 0.9}],
                public_memory=[f"{name}的公开背景"],
                risk_tolerance=risk
            )
            print(f"  创建: {name}")
        
        # 运行模拟
        print("\n运行20个tick...")
        result = await client.advance_tick(world.id, count=20)
        
        print(f"\n结果摘要: {result['summary']}")
        print(f"总共生成 {result['events_count']} 个事件")
        
        # 查看所有事件
        events = await client.list_events(world.id)
        print("\n所有事件:")
        for event in events:
            print(f"  [{event.type}] {event.title}")
        
    finally:
        await client.close()


# 运行示例
if __name__ == "__main__":
    print("=" * 60)
    print("ClawLoom Python 客户端示例")
    print("=" * 60)
    print()
    
    print("运行示例1：沙漠绿洲...")
    asyncio.run(example_1_simple_story())
