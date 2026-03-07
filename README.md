# ClawLoom 爪织

> 播种角色，编织世界，观察演化，导出故事

---

## 简介 | Introduction

**中文**

ClawLoom（爪织）是一个AI驱动的世界推演与叙事生成平台。人类作为创世者设定规则、播种角色，AI角色（Claw）作为世界居民自主决策、互动演化，最终形成可导出为小说、剧本、漫画或短剧的故事世界。

核心特性：
- **数据驱动的世界** —— 所有状态存储于数据库，每tick生成快照，支持回溯与分支
- **单Claw多角色** —— 一个AI实例通过角色卡切换扮演多个角色，高效且角色间理解一致
- **观察者模式** —— 人类是世界的观察者，通过"神迹"系统有限干预：启示、事件、化身、新种子
- **涌现叙事** —— 无需预设剧本，故事从角色互动中自然涌现

**English**

ClawLoom is an AI-driven world simulation and narrative generation platform. Humans act as creators who set rules and seed characters, while AI characters (Claws) inhabit the world, making autonomous decisions and evolving through interactions, ultimately forming story worlds that can be exported as novels, screenplays, comics, or short dramas.

Core features:
- **Data-Driven Worlds** — All states stored in database with per-tick snapshots, supporting time travel and branching
- **Single Claw, Multiple Roles** — One AI instance plays multiple characters via role cards, efficient and consistent
- **Observer Mode** — Humans observe the world and intervene through limited "miracles": revelations, events, avatars, new seeds
- **Emergent Narrative** — No preset scripts; stories emerge naturally from character interactions

---

## 项目结构

```
clawloom/
│
├── prototype/                    # 原型验证
│   ├── world.md                  # 裂谷三地世界设定
│   ├── roles/                    # 角色卡
│   ├── 银泪泉干涸之日.md         # 基于模拟的小说
│   └── VALIDATION.md             # 验证结论
│
├── ARCHITECTURE_3.0.md           # 架构设计文档
│
└── engine/                       # Python世界引擎
    ├── models/                   # 数据模型
    ├── core/world_engine.py      # 世界引擎核心
    └── main.py                   # 入口演示
```

---

## 核心理念 | Core Philosophy

**人类是织布者，Claw是丝线，时间是织机。**

你设定世界的物理规则、地理、势力分布。你创造角色，赋予他们欲望、恐惧、秘密。然后你后退一步，看着他们在时间的织机上交织出你无法预料的图案。

每一个决定都留下痕迹。每一次冲突都改变关系。故事不是被写出来的——它是自己生长出来的。

---

## 快速开始 | Quick Start

```bash
cd clawloom/engine
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:pass@localhost:5432/clawloom"
export OPENCLAW_URL="http://localhost:8080"
python main.py
```

---

## 技术栈 | Tech Stack

- **Backend**: Python + SQLAlchemy + FastAPI
- **Database**: PostgreSQL + PostGIS
- **AI**: OpenClaw / LLM API
- **Frontend**: Next.js + React (planned)

---

*播种于 2026-03-07*
