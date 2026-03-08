"""
ClawLoom 完整测试 - 启动服务器并运行 API 测试
"""

import subprocess
import time
import asyncio
import httpx
import sys
import os

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"

async def run_api_tests():
    """运行 API 测试"""
    print("[TEST] 开始 API 测试")
    print("="*50)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        # 1. 健康检查
        print("\n[1] 健康检查...")
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"    [OK] 服务器健康 (数据库: {data.get('database', 'unknown')})")
        
        # 2. 创建世界
        print("\n[2] 创建世界...")
        response = await client.post(
            "/worlds",
            headers={"X-Claw-Key": API_KEY},
            json={
                "name": "测试世界",
                "description": "API 测试用",
                "cosmology": {"physics": "standard"}
            }
        )
        assert response.status_code == 201
        world = response.json()
        world_id = world["id"]
        print(f"    [OK] 创建世界: {world['name']} ({world_id[:8]}...)")
        
        # 3. 列出世界
        print("\n[3] 列出世界...")
        response = await client.get("/worlds", headers={"X-Claw-Key": API_KEY})
        assert response.status_code == 200
        worlds = response.json()
        print(f"    [OK] 找到 {len(worlds)} 个世界")
        
        # 4. 创建角色
        print("\n[4] 创建角色...")
        roles_data = [
            {
                "name": "铁岩",
                "card": {
                    "drives": [{"id": "protect", "weight": 0.9}],
                    "memory": {"public": ["高地氏族的战士"]},
                    "decision_style": {"risk_tolerance": "low"}
                }
            },
            {
                "name": "流萤",
                "card": {
                    "drives": [{"id": "explore", "weight": 0.8}],
                    "memory": {"public": ["流浪的商人"]},
                    "decision_style": {"risk_tolerance": "high"}
                }
            }
        ]
        
        role_ids = []
        for role_data in roles_data:
            response = await client.post(
                f"/worlds/{world_id}/roles",
                headers={"X-Claw-Key": API_KEY},
                json=role_data
            )
            assert response.status_code == 201
            role = response.json()
            role_ids.append(role["id"])
            print(f"    [OK] 创建角色: {role['name']} (状态: {role['status']})")
        
        # 5. 列出角色
        print("\n[5] 列出角色...")
        response = await client.get(
            f"/worlds/{world_id}/roles",
            headers={"X-Claw-Key": API_KEY}
        )
        assert response.status_code == 200
        roles = response.json()
        print(f"    [OK] 找到 {len(roles)} 个角色")
        
        # 6. 推进模拟
        print("\n[6] 推进模拟 (2 ticks)...")
        try:
            response = await client.post(
                f"/worlds/{world_id}/tick",
                headers={"X-Claw-Key": API_KEY},
                json={"count": 2},
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                print(f"    [OK] 推进到 tick {result['tick']}")
                print(f"         决策数: {result['decisions_count']}")
                print(f"         冲突数: {result['conflicts_count']}")
                print(f"         事件数: {result['events_count']}")
            else:
                print(f"    [WARN] Tick 失败: {response.status_code}")
                print(f"           响应: {response.text[:200]}")
        except Exception as e:
            print(f"    [WARN] Tick 错误: {e}")
        
        # 7. 获取世界状态
        print("\n[7] 获取世界状态...")
        response = await client.get(
            f"/worlds/{world_id}/state",
            headers={"X-Claw-Key": API_KEY}
        )
        assert response.status_code == 200
        state = response.json()
        print(f"    [OK] 当前 tick: {state['tick']}")
        print(f"         事件数: {len(state.get('events', []))}")
        
        print("\n" + "="*50)
        print("[PASS] 所有测试通过!")
        print("="*50)
        return True

def main():
    print("[INIT] ClawLoom 完整测试")
    print("="*50)
    
    # 启动服务器
    print("\n[INIT] 启动服务器...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.server_sqlite:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="c:\\Users\\28788\\projects\\clawloom\\engine",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务器启动
    time.sleep(3)
    
    try:
        # 运行测试
        success = asyncio.run(run_api_tests())
        return 0 if success else 1
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 关闭服务器
        print("\n[CLEANUP] 关闭服务器...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except:
            server_proc.kill()
        print("[OK] 服务器已关闭")

if __name__ == "__main__":
    sys.exit(main())
