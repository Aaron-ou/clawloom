# ClawLoom AI 快速入门

5分钟上手ClawLoom世界模拟平台。

## 第一步：启动服务

```bash
# 后端（Python）
cd engine
python -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000

# 前端（Node.js，新终端）
cd frontend
npm run dev
```

## 第二步：创建你的第一个世界

```bash
curl -X POST http://localhost:8000/worlds \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{"name": "我的第一个世界", "description": "测试世界"}'
```

## 第三步：添加角色

```bash
# 保存world_id，替换{world_id}
curl -X POST http://localhost:8000/worlds/{world_id}/roles \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{
    "name": "勇者",
    "card": {
      "drives": [{"id": "heroism", "weight": 0.9}],
      "memory": {"public": ["立志成为英雄"]},
      "decision_style": {"risk_tolerance": "high"}
    }
  }'
```

## 第四步：推进模拟

```bash
curl -X POST http://localhost:8000/worlds/{world_id}/tick \
  -H "Content-Type: application/json" \
  -H "X-Claw-Key: test-key" \
  -d '{"count": 5}'
```

## 第五步：查看结果

打开浏览器访问 http://localhost:3000

或者API方式：
```bash
# 查看时间线
curl http://localhost:8000/worlds/{world_id}/timeline \
  -H "X-Claw-Key: test-key"

# 查看事件
curl http://localhost:8000/worlds/{world_id}/events \
  -H "X-Claw-Key: test-key"
```

## 核心概念速查

| 概念 | 说明 | 示例 |
|------|------|------|
| **World** | 一个独立宇宙 | 沙漠王国、赛博朋克城市 |
| **Role** | AI驱动的角色 | 勇者、魔王、商人 |
| **Tick** | 时间单位 | 世界的一次"心跳" |
| **Event** | 发生的事件 | 战斗、对话、发现 |
| **Conflict** | 角色间冲突 | 争夺资源、战斗 |

## 角色卡模板

```json
{
  "drives": [
    {"id": "survival", "weight": 1.0},
    {"id": "power", "weight": 0.7},
    {"id": "knowledge", "weight": 0.5}
  ],
  "memory": {
    "public": ["公开信息"],
    "secrets": ["只有角色知道的秘密"]
  },
  "decision_style": {
    "risk_tolerance": "high"
  }
}
```

## Python代码示例

```python
import httpx

async def quick_demo():
    async with httpx.AsyncClient() as client:
        headers = {"X-Claw-Key": "test-key"}
        base = "http://localhost:8000"
        
        # 1. 创建世界
        r = await client.post(f"{base}/worlds", headers=headers, 
                             json={"name": "测试世界"})
        world_id = r.json()["id"]
        
        # 2. 添加角色
        await client.post(f"{base}/worlds/{world_id}/roles", 
                         headers=headers,
                         json={"name": "英雄", "card": {"drives": [{"id": "heroism", "weight": 0.9}], "memory": {"public": []}, "decision_style": {"risk_tolerance": "high"}}})
        
        # 3. 推进10个tick
        r = await client.post(f"{base}/worlds/{world_id}/tick",
                             headers=headers, json={"count": 10})
        result = r.json()
        print(f"Tick {result['tick']}: {result['summary']}")
        
        # 4. 查看事件
        r = await client.get(f"{base}/worlds/{world_id}/events", 
                            headers=headers)
        for e in r.json():
            print(f"  - {e['title']}")

# asyncio.run(quick_demo())
```

## 下一步

阅读完整指南：[AI_GUIDE.md](AI_GUIDE.md)

查看API文档：http://localhost:8000/docs
