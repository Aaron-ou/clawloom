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
├── engine/                       # Python 世界引擎
│   ├── api/                      # FastAPI 接口
│   │   ├── server_sqlite.py      # SQLite 版服务器
│   │   └── test_api.py           # API 测试
│   ├── core/                     # 核心引擎
│   │   ├── world_engine.py       # 世界引擎主类
│   │   ├── claw_connector.py     # LLM 决策接口
│   │   ├── conflict_arbiter.py   # 冲突仲裁系统
│   │   └── event_generator.py    # 事件生成器
│   ├── models/                   # 数据模型
│   └── requirements.txt          # Python 依赖
│
├── frontend/                     # Next.js 前端
│   ├── src/
│   │   ├── app/                  # 页面路由
│   │   ├── components/           # 组件
│   │   ├── lib/api.ts            # API 客户端
│   │   └── types/                # TypeScript 类型
│   └── package.json
│
├── start_all.bat                 # Windows 启动脚本
├── start_all.sh                  # Linux/Mac 启动脚本
└── README.md
```

---

## 快速开始 | Quick Start

### 一键启动（推荐）

**Windows:**
```bash
start_all.bat
```

**Linux/Mac:**
```bash
./start_all.sh
```

### 手动启动

**1. 启动后端:**
```bash
cd engine
pip install -r requirements.txt
python -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 运行
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

**2. 启动前端（新终端）:**
```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:3000 运行

---

## 使用指南

### 1. 创建世界
打开前端界面 http://localhost:3000，点击"世界管理"，创建一个新世界。

### 2. 添加角色
进入世界后，在"角色"标签页添加角色。每个角色都有：
- 核心驱动力（生存、权力、知识等）
- 记忆（公开或秘密）
- 决策风格

### 3. 推进模拟
在"模拟控制台"标签页，选择推进的 tick 数，点击"推进模拟"。

每个 tick：
- 所有活跃角色做出决策
- 系统自动检测并解决冲突
- 生成世界事件
- 更新角色记忆

### 4. 观察演化
在"时间线"标签页查看所有发生的事件，了解故事的演化过程。

---

## 核心理念 | Core Philosophy

**人类是织布者，Claw是丝线，时间是织机。**

你设定世界的物理规则、地理、势力分布。你创造角色，赋予他们欲望、恐惧、秘密。然后你后退一步，看着他们在时间的织机上交织出你无法预料的图案。

每一个决定都留下痕迹。每一次冲突都改变关系。故事不是被写出来的——它是自己生长出来的。

---

## 技术栈 | Tech Stack

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端 | Python 3.9+ + FastAPI | Web 框架和 API |
| 数据库 | SQLite / PostgreSQL | 数据持久化 |
| ORM | SQLAlchemy 2.0 | 数据库抽象 |
| 验证 | Pydantic v2 | 数据模型和验证 |
| 前端 | Next.js 14 + React 18 | 用户界面 |
| 样式 | Tailwind CSS | CSS 框架 |
| 语言 | TypeScript | 类型安全 |

---

## API 端点

### 世界管理
- `POST /worlds` - 创建世界
- `GET /worlds` - 列出世界
- `GET /worlds/{id}` - 获取世界详情
- `DELETE /worlds/{id}` - 删除世界

### 角色管理
- `POST /worlds/{id}/roles` - 创建角色
- `GET /worlds/{id}/roles` - 列出角色
- `GET /worlds/{id}/roles/{role_id}` - 获取角色详情
- `GET /worlds/{id}/roles/{role_id}/memories` - 获取角色记忆

### 模拟控制
- `POST /worlds/{id}/tick` - 推进模拟
- `GET /worlds/{id}/state` - 获取世界状态
- `GET /worlds/{id}/timeline` - 获取时间线

### 事件
- `GET /worlds/{id}/events` - 列出事件

---

## 开发计划

- [x] 数据层 + 基础模拟
- [x] 世界引擎核心
- [x] REST API
- [x] 前端界面
- [ ] 地理位置系统
- [ ] 秘密传播机制
- [ ] 神迹干预系统
- [ ] 叙事导出功能
- [ ] LLM 集成优化

---

*播种于 2026-03-07*
