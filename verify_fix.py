"""
验证修复脚本
测试注册功能和文档访问
"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def test_backend():
    """测试后端API"""
    print("=" * 60)
    print("测试后端API")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # 1. 健康检查
        print("\n[1] 健康检查...")
        try:
            r = await client.get(f"{BASE_URL}/health")
            if r.status_code == 200:
                print(f"  ✓ 后端运行正常: {r.json()}")
            else:
                print(f"  ✗ 健康检查失败: {r.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ 无法连接后端: {e}")
            return False
        
        # 2. 注册功能
        print("\n[2] 测试注册功能...")
        try:
            r = await client.post(
                f"{BASE_URL}/auth/register",
                json={"username": "test_user_123", "password": "test_pass"}
            )
            if r.status_code == 201:
                data = r.json()
                print(f"  ✓ 注册成功!")
                print(f"  ✓ 获得API Key: {data['access_token'][:30]}...")
                return data['access_token']
            elif r.status_code == 400 and "已存在" in r.text:
                print(f"  ⚠ 用户已存在（这是正常的）")
                return "existing_user"
            else:
                print(f"  ✗ 注册失败: {r.status_code} - {r.text}")
                return False
        except Exception as e:
            print(f"  ✗ 注册出错: {e}")
            return False

async def test_docs():
    """测试文档文件"""
    print("\n" + "=" * 60)
    print("测试文档文件")
    print("=" * 60)
    
    docs = [
        "/docs/AI_QUICKSTART.md",
        "/docs/AI_GUIDE.md",
        "/docs/AGENTS.md",
        "/docs/README.md"
    ]
    
    async with httpx.AsyncClient() as client:
        all_ok = True
        for doc in docs:
            print(f"\n[ ] 检查 {doc}...")
            try:
                r = await client.get(f"{FRONTEND_URL}{doc}")
                if r.status_code == 200:
                    content_length = len(r.text)
                    if content_length > 100:
                        print(f"  ✓ 文档正常 ({content_length} 字节)")
                    else:
                        print(f"  ✗ 文档内容太短 ({content_length} 字节)")
                        all_ok = False
                else:
                    print(f"  ✗ 无法访问: {r.status_code}")
                    all_ok = False
            except Exception as e:
                print(f"  ✗ 错误: {e}")
                all_ok = False
        
        return all_ok

async def main():
    print("ClawLoom 修复验证")
    print("确保前后端都已启动！")
    print()
    
    # 测试后端
    api_key = await test_backend()
    
    # 测试文档
    docs_ok = await test_docs()
    
    # 汇总
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    print(f"注册功能: {'✓ 正常' if api_key else '✗ 失败'}")
    print(f"文档访问: {'✓ 正常' if docs_ok else '✗ 失败'}")
    print()
    
    if api_key and docs_ok:
        print("✓ 所有修复已验证通过！")
        return 0
    else:
        print("✗ 仍有部分功能异常，请检查：")
        if not api_key:
            print("  - 后端是否已启动？")
            print("  - 数据库表是否正确创建？")
        if not docs_ok:
            print("  - 前端是否已启动？")
            print("  - 文档文件是否在 public/docs/ 目录？")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
