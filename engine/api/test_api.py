"""
ClawLoom API Test Script
Tests all API endpoints locally
"""

import asyncio
import json
from uuid import UUID

import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"  # Test API key


class ClawLoomAPITest:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"X-Claw-Key": API_KEY}
        )
        self.world_id = None
        self.role_ids = []
    
    async def test_health(self):
        """Test health endpoint"""
        print("\n🩺 Testing health check...")
        response = await self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check passed: {data}")
    
    async def test_create_world(self):
        """Test world creation"""
        print("\n🌍 Testing world creation...")
        response = await self.client.post("/worlds", json={
            "name": "Test World",
            "description": "A test world for API validation",
            "cosmology": {
                "physics": "low_magic",
                "technology": "medieval"
            },
            "genesis_params": {
                "initial_roles": 3
            }
        })
        assert response.status_code == 201
        data = response.json()
        self.world_id = data["id"]
        assert data["name"] == "Test World"
        assert data["status"] == "active"
        assert data["current_tick"] == 0
        print(f"✅ World created: {self.world_id}")
    
    async def test_list_worlds(self):
        """Test listing worlds"""
        print("\n📋 Testing world list...")
        response = await self.client.get("/worlds")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        print(f"✅ Found {len(data)} worlds")
    
    async def test_get_world(self):
        """Test getting world details"""
        print("\n🔍 Testing get world...")
        response = await self.client.get(f"/worlds/{self.world_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.world_id
        print(f"✅ Got world: {data['name']}")
    
    async def test_create_roles(self):
        """Test creating roles"""
        print("\n👤 Testing role creation...")
        
        roles_data = [
            {
                "name": "Test Hero",
                "card": {
                    "drives": [{"id": "heroism", "weight": 0.9}],
                    "memory": {"public": ["A brave hero"]},
                    "decision_style": {"risk_tolerance": "medium"}
                }
            },
            {
                "name": "Test Villain",
                "card": {
                    "drives": [{"id": "power", "weight": 0.95}],
                    "memory": {"public": ["A cunning villain"]},
                    "decision_style": {"risk_tolerance": "high"}
                }
            }
        ]
        
        for role_data in roles_data:
            response = await self.client.post(
                f"/worlds/{self.world_id}/roles",
                json=role_data
            )
            assert response.status_code == 201
            data = response.json()
            self.role_ids.append(data["id"])
            print(f"✅ Role created: {data['name']} ({data['id']})")
    
    async def test_list_roles(self):
        """Test listing roles"""
        print("\n📋 Testing role list...")
        response = await self.client.get(f"/worlds/{self.world_id}/roles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        print(f"✅ Found {len(data)} roles")
    
    async def test_get_role_memories(self):
        """Test getting role memories"""
        print("\n🧠 Testing role memories...")
        response = await self.client.get(
            f"/worlds/{self.world_id}/roles/{self.role_ids[0]}/memories"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # Should have birth memory
        print(f"✅ Found {len(data)} memories")
    
    async def test_advance_tick(self):
        """Test advancing simulation"""
        print("\n⏭️  Testing tick advancement...")
        response = await self.client.post(
            f"/worlds/{self.world_id}/tick",
            json={"count": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tick"] == 3
        assert "decisions" in data
        assert "events" in data
        print(f"✅ Advanced to tick {data['tick']}")
        print(f"   Decisions: {len(data['decisions'])}")
        print(f"   Conflicts: {len(data['conflicts'])}")
        print(f"   Events: {len(data['events'])}")
        print(f"   Summary: {data['summary'][:100]}...")
    
    async def test_get_world_state(self):
        """Test getting world state"""
        print("\n📊 Testing world state...")
        
        # Current state
        response = await self.client.get(f"/worlds/{self.world_id}/state")
        assert response.status_code == 200
        data = response.json()
        assert data["tick"] == 3
        print(f"✅ Current state at tick {data['tick']}")
        
        # Historical state
        response = await self.client.get(
            f"/worlds/{self.world_id}/state?tick=1"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tick"] == 1
        print(f"✅ Historical state at tick {data['tick']}")
    
    async def test_list_events(self):
        """Test listing events"""
        print("\n📜 Testing events list...")
        response = await self.client.get(f"/worlds/{self.world_id}/events")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Found {len(data)} events")
        for event in data[:3]:  # Show first 3
            print(f"   - {event['type']}: {event['title']}")
    
    async def test_unauthorized_access(self):
        """Test unauthorized access is blocked"""
        print("\n🔒 Testing unauthorized access...")
        
        # Create client without API key
        bad_client = httpx.AsyncClient(base_url=BASE_URL)
        
        response = await bad_client.get("/worlds")
        assert response.status_code == 401
        print("✅ Unauthorized access blocked")
        
        await bad_client.aclose()
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up...")
        if self.world_id:
            response = await self.client.delete(f"/worlds/{self.world_id}")
            if response.status_code == 200:
                print(f"✅ Deleted test world")
        await self.client.aclose()
    
    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 ClawLoom API Test Suite")
        print("="*60)
        
        try:
            # Basic tests
            await self.test_health()
            
            # World tests
            await self.test_create_world()
            await self.test_list_worlds()
            await self.test_get_world()
            
            # Role tests
            await self.test_create_roles()
            await self.test_list_roles()
            await self.test_get_role_memories()
            
            # Simulation tests
            await self.test_advance_tick()
            await self.test_get_world_state()
            await self.test_list_events()
            
            # Security tests
            await self.test_unauthorized_access()
            
            print("\n" + "="*60)
            print("✅ All tests passed!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    tester = ClawLoomAPITest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
