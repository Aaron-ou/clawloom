#!/usr/bin/env python3
"""
Quick test to verify the API server works
Uses SQLite instead of PostgreSQL for easy local testing
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override settings to use SQLite
os.environ["DATABASE_URL"] = "sqlite:///./clawloom_test.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Create test database
engine = create_engine("sqlite:///./clawloom_test.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
print("✅ Test database created")

# Quick API test
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def quick_test():
    """Quick API smoke test"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Health check
        response = await client.get("/health")
        assert response.status_code == 200
        print(f"✅ Health check: {response.json()}")
        
        # Create world
        response = await client.post(
            "/worlds",
            headers={"X-Claw-Key": "test-key"},
            json={
                "name": "Quick Test World",
                "description": "Testing the API"
            }
        )
        assert response.status_code == 201
        world = response.json()
        world_id = world["id"]
        print(f"✅ Created world: {world['name']} ({world_id})")
        
        # Create role
        response = await client.post(
            f"/worlds/{world_id}/roles",
            headers={"X-Claw-Key": "test-key"},
            json={
                "name": "Test Hero",
                "card": {
                    "drives": [{"id": "test", "weight": 0.5}],
                    "memory": {"public": ["A test character"]}
                }
            }
        )
        assert response.status_code == 201
        role = response.json()
        print(f"✅ Created role: {role['name']}")
        
        # Advance tick
        response = await client.post(
            f"/worlds/{world_id}/tick",
            headers={"X-Claw-Key": "test-key"},
            json={"count": 1}
        )
        assert response.status_code == 200
        result = response.json()
        print(f"✅ Advanced to tick {result['tick']}")
        print(f"   Events: {len(result['events'])}")
        
        # Get state
        response = await client.get(
            f"/worlds/{world_id}/state",
            headers={"X-Claw-Key": "test-key"}
        )
        assert response.status_code == 200
        state = response.json()
        print(f"✅ Got world state at tick {state['tick']}")
        
        print("\n✅ All smoke tests passed!")

if __name__ == "__main__":
    print("🧪 ClawLoom API Quick Test")
    print("="*50)
    
    # Check if server is running
    import subprocess
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8000/health"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 or "healthy" not in result.stdout:
        print("❌ Server is not running!")
        print("   Start it with: ./start_server.sh")
        sys.exit(1)
    
    print("✅ Server is running\n")
    
    # Run tests
    asyncio.run(quick_test())
    
    # Cleanup
    print("\n🧹 Cleaning up test database...")
    if os.path.exists("clawloom_test.db"):
        os.remove("clawloom_test.db")
    print("✅ Done!
)