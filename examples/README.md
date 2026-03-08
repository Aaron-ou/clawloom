# ClawLoom 示例

这个目录包含使用ClawLoom的各种示例代码。

## 可用示例

### Python

- **python_client.py** - 完整的Python API客户端和使用示例
  - 简单两角色故事
  - 批量角色创建
  - 故事导出

### 运行示例

```bash
# 确保后端已启动
cd ../engine
python -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000

# 运行Python示例
cd ../examples
python python_client.py
```

## 示例场景

### 场景1：资源争夺
- 世界：沙漠绿洲
- 角色：守护者 vs 流浪者
- 驱动力：保护 vs 生存
- 预期：冲突、谈判或合作

### 场景2：权力斗争
- 世界：王国议会
- 角色：保守派、改革派、中立者、阴谋家
- 驱动力：稳定 vs 变革
- 预期：联盟、背叛、政治博弈

### 场景3：冒险故事
- 世界：魔法大陆
- 角色：勇者、导师、同伴、反派
- 驱动力：英雄主义 vs 野心
- 预期：成长、冲突、最终对决

## 编写自己的示例

参考 `python_client.py` 中的 `ClawLoomClient` 类，它封装了所有常用API。

基本模式：
```python
client = ClawLoomClient()

# 创建世界
world = await client.create_world(name="我的世界")

# 添加角色
role = await client.create_role(
    world_id=world.id,
    name="我的角色",
    drives=[{"id": "my_drive", "weight": 0.8}],
    public_memory=["背景故事"]
)

# 推进模拟
result = await client.advance_tick(world.id, count=10)

# 获取结果
events = await client.list_events(world.id)
```

## 贡献

欢迎提交你自己的示例！请确保：
1. 代码有清晰的注释
2. 包含预期的运行结果
3. 说明这个示例展示的特定功能
