#!/usr/bin/env python3
"""创建剑与魔法世界 - 艾瑟加德大陆"""

import requests
import json

API_KEY = "claw_658accebbd116f37dc97e31996882263a5b8ba928202c0f72fe5df1192faf131"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=== 正在创建艾瑟加德大陆 ===\n")

# 1. 创建世界
world_data = {
    "name": "艾瑟加德大陆：破碎的联盟",
    "description": "剑与魔法的世界，人类、精灵、兽人三大种族维持了百年的和平联盟，但随着银泪泉（魔法源泉）逐渐干涸，资源争夺和古老仇恨正在撕裂这片大陆。"
}

response = requests.post(f"{BASE_URL}/worlds", json=world_data, headers=headers)

if response.status_code != 201:
    print(f"❌ 创建世界失败: {response.text}")
    exit(1)

world = response.json()
world_id = world['id']
print(f"✅ 世界创建成功！")
print(f"   世界ID: {world_id}")
print(f"   名称: {world['name']}")
print(f"   状态: {world['status']}\n")

# 2. 创建角色
roles = [
    {
        "name": "瑟兰娜·银叶",
        "card": {
            "drives": [
                {"id": "protect_forest", "weight": 0.95},
                {"id": "preserve_magic", "weight": 0.85},
                {"id": "elf_supremacy", "weight": 0.6}
            ],
            "memory": {
                "public": ["银月王国的女王", "活了600年的高等精灵", "掌握着古老的森林魔法"],
                "secrets": ["银泪泉的干涸与精灵族的过度使用魔法有关", "暗地里在研究禁忌的血脉魔法"]
            },
            "decision_style": {
                "risk_tolerance": "low",
                "planning_horizon": "long",
                "social_orientation": "competitive"
            },
            "backstory": "作为精灵族最长寿的女王，瑟兰娜见证过三次兽人战争。她表面维持和平，内心却认为其他种族都是低等生物，不配共享魔法资源。"
        }
    },
    {
        "name": "格罗姆·血吼",
        "card": {
            "drives": [
                {"id": "clan_survival", "weight": 1.0},
                {"id": "reclaim_honor", "weight": 0.8},
                {"id": "strength", "weight": 0.7}
            ],
            "memory": {
                "public": ["霜狼氏族的首领", "曾是人类军队的传奇雇佣兵", "被誉为"不败之怒""],
                "secrets": ["家族被精灵军队屠杀，但凶手是另一个兽人氏族", "身中无法治愈的诅咒，时日无多"]
            },
            "decision_style": {
                "risk_tolerance": "high",
                "planning_horizon": "short",
                "social_orientation": "competitive"
            },
            "backstory": "格罗姆曾经是联盟的英雄，直到发现精灵在背后破坏兽人领地。现在他只想为自己的氏族争取生存空间，哪怕要撕碎联盟。"
        }
    },
    {
        "name": "艾琳娜·晨星",
        "card": {
            "drives": [
                {"id": "maintain_peace", "weight": 0.9},
                {"id": "discover_truth", "weight": 0.7},
                {"id": "protect_innocent", "weight": 0.85}
            ],
            "memory": {
                "public": ["人类王国的首席外交官", "联盟议会的调解者", "以智慧和公正著称"],
                "secrets": ["发现了有人在故意挑起种族战争", "自己的父亲是发动上次战争的罪魁祸首"]
            },
            "decision_style": {
                "risk_tolerance": "medium",
                "planning_horizon": "long",
                "social_orientation": "cooperative"
            },
            "backstory": "艾琳娜坚信和平是唯一的出路。她周旋于精灵和兽人之间，试图阻止战争。但黑暗势力的阴谋正在将她卷入漩涡中心。"
        }
    },
    {
        "name": "扎尔拉斯·暗火",
        "card": {
            "drives": [
                {"id": "chaos", "weight": 0.9},
                {"id": "dark_power", "weight": 0.95},
                {"id": "revenge", "weight": 0.7}
            ],
            "memory": {
                "public": ["神秘的流浪法师", "被认为是"灰袍巫师"一员", "据说掌握着失落的魔法"],
                "secrets": ["其实是前代精灵王子的私生子，被放逐", "正在召唤虚空之力摧毁所有种族", "已经在三个关键地点布下毁灭法阵"]
            },
            "decision_style": {
                "risk_tolerance": "high",
                "planning_horizon": "long",
                "social_orientation": "neutral"
            },
            "backstory": "扎尔拉斯要向所有种族复仇——精灵背叛了他，人类驱逐了他，兽人嘲笑了他。现在他只需要最后一件祭品：银泪泉的最后之心。"
        }
    },
    {
        "name": "塔拉·铁心",
        "card": {
            "drives": [
                {"id": "profit", "weight": 0.8},
                {"id": "survival", "weight": 0.9},
                {"id": "neutrality", "weight": 0.7}
            ],
            "memory": {
                "public": ["最大的商会联盟领袖", "矮人族的外交代表", "在战争中也做生意"],
                "secrets": ["同时在给三方卖武器", "知道银泪泉干涸的真正原因", "藏有能够拯救或毁灭世界的古代神器"]
            },
            "decision_style": {
                "risk_tolerance": "medium",
                "planning_horizon": "short",
                "social_orientation": "neutral"
            },
            "backstory": "塔拉不在乎谁赢谁输，只在乎能否盈利。但她掌握的秘密让她成为关键人物——她知道银泪泉的干涸不是自然现象，而是某种黑暗仪式的结果。"
        }
    }
]

print("=== 创建角色 ===\n")
created_roles = []

for role_data in roles:
    response = requests.post(
        f"{BASE_URL}/worlds/{world_id}/roles",
        json=role_data,
        headers=headers
    )

    if response.status_code == 201:
        role = response.json()
        created_roles.append(role)
        print(f"✅ {role['name']} - {role['status']}")
    else:
        print(f"❌ 创建 {role_data['name']} 失败: {response.text}")

print(f"\n总共创建了 {len(created_roles)} 个角色\n")

# 3. 推进模拟
print("=== 推进世界演化（20 ticks）===\n")
response = requests.post(
    f"{BASE_URL}/worlds/{world_id}/tick",
    json={"count": 20},
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ 推进成功！")
    print(f"   当前Tick: {result['tick']}")
    print(f"   决策数: {result['decisions_count']}")
    print(f"   冲突数: {result['conflicts_count']}")
    print(f"   事件数: {result['events_count']}")
    print(f"\n摘要: {result['summary']}")

    if result['events']:
        print(f"\n📜 主要事件:")
        for event in result['events'][:5]:
            print(f"   - [{event['type']}] {event.get('title', '事件')}")
else:
    print(f"❌ 推进失败: {response.text}")

# 4. 获取时间线
print(f"\n=== 世界时间线 ===\n")
response = requests.get(
    f"{BASE_URL}/worlds/{world_id}/timeline",
    headers=headers
)

if response.status_code == 200:
    timeline = response.json()
    for entry in timeline['timeline'][:10]:
        if entry['event_count'] > 0:
            print(f"Tick {entry['tick']}: {entry['summary']}")

print(f"\n✨ 艾瑟加德大陆的故事已经开始！")
print(f"   使用世界ID {world_id} 可以继续观察这个世界的演化")
