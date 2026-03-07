"""
Quick API test for SQLite server
"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"

async def run_tests():
    """Run quick API tests"""
    print("🧪 ClawLoom SQLite API Test")
    print("="*50)
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Health check
        print("\n1. Health check...")
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✅ Server healthy (database: {data.get('database', 'unknown')})")
        
        # Create world
        print("\n2. Creating world...")
        response = await client.post(
            "/worlds",
            headers={"X-Claw-Key": API_KEY},
            json={
                "name": "Test World",
                "description": "Testing the API",
                "cosmology": {"physics": "test"}
            }
        )
        assert response.status_code == 201
        world = response.json()
        world_id = world["id"]
        print(f"   ✅ Created world: {world['name']} ({world_id[:8]}...)")
        
        # List worlds
        print("\n3. Listing worlds...")
        response = await client.get("/worlds", headers={"X-Claw-Key": API_KEY})
        assert response.status_code == 200
        worlds = response.json()
        print(f"   ✅ Found {len(worlds)} world(s)")
        
        # Create roles
        print("\n4. Creating roles...")
        role_ids = []
        for name in ["Hero", "Villain"]:
            response = await client.post(
                f"/worlds/{world_id}/roles",
                headers={"X-Claw-Key": API_KEY},
                json={
                    "name": name,
                    "card": {
                        "drives": [{"id": "test", "weight": 0.5}],
                        "memory": {"public": [f"A {name.lower()}"]},
                        "decision_style": {"risk_tolerance": "medium"}
                    }
                }
            )
            assert response.status_code == 201
            role = response.json()
            role_ids.append(role["id"])
            print(f"   ✅ Created role: {role['name']}")
        
        # List roles
        print("\n5. Listing roles...")
        response = await client.get(
            f"/worlds/{world_id}/roles",
            headers={"X-Claw-Key": API_KEY}
        )
        assert response.status_code == 200
        roles = response.json()
        print(f"   ✅ Found {len(roles)} role(s)")
        
        # Advance tick (may fail if Claw connector has issues)
        print("\n6. Advancing simulation...")
        try:
            response = await client.post(
                f"/worlds/{world_id}/tick",
                headers={"X-Claw-Key": API_KEY},
                json={"count": 2},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Advanced to tick {result['tick']}")
                print(f"      Events: {result['events_count']}")
            else:
                print(f"   ⚠️  Tick failed: {response.status_code}")
                print(f"      Response: {response.text[:100]}")
        except Exception as e:
            print(f"   ⚠️  Tick error: {e}")
        
        # Get world state
        print("\n7. Getting world state...")
        response = await client.get(
            f"/worlds/{world_id}/state",
            headers={"X-Claw-Key": API_KEY}
        )
        assert response.status_code == 200
        state = response.json()
        print(f"   ✅ State at tick {state['tick']}")
        
        print("\n" + "="*50)
        print("✅ All basic tests passed!")
        print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
