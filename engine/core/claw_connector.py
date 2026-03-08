"""
Claw Connector - LLM 决策接口
负责构建 prompt、调用 LLM、解析决策
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

try:
    from models_sqlite import Decision, EventORM
except ImportError:
    from models import Decision, EventORM


class ClawConnector:
    """
    连接 Claw (LLM) 服务的接口
    当前使用模拟实现，可替换为真实的 LLM API 调用
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or "http://localhost:8080"
        self.api_key = api_key
        self.mock_mode = api_url is None  # 无 API 时使用模拟模式
        
        # 模拟决策模板
        self.action_templates = [
            {"type": "observe", "details": "观察周围环境，收集信息"},
            {"type": "move", "details": "前往新的地点探索"},
            {"type": "interact", "details": "与其他角色交流"},
            {"type": "gather", "details": "收集资源或信息"},
            {"type": "rest", "details": "休息恢复体力"},
            {"type": "plan", "details": "制定未来行动计划"},
            {"type": "investigate", "details": "调查异常情况"},
            {"type": "defend", "details": "采取防御姿态"},
        ]
        
        self.thought_templates = [
            "局势似乎有些变化，我需要谨慎行事。",
            "这是一个机会，我应该抓住它。",
            "周围的环境让我感到不安。",
            "我需要更多信息才能做出决定。",
            "我的直觉告诉我应该这样做。",
            "根据过去的经验，这可能是最佳选择。",
            "我的目标就在眼前，不能放弃。",
            "现在的首要任务是确保安全。",
        ]
    
    async def request_decision(
        self,
        role: Any,  # RoleORM
        world_state: Any,  # WorldState
        context: Dict[str, Any]
    ) -> Decision:
        """
        向 Claw 请求角色决策
        
        Args:
            role: 角色 ORM 对象
            world_state: 当前世界状态
            context: 包含记忆、关系等上下文信息
        
        Returns:
            Decision: 角色的决策
        """
        if self.mock_mode:
            return await self._mock_decision(role, world_state, context)
        else:
            return await self._real_claw_call(role, world_state, context)
    
    async def _mock_decision(
        self,
        role: Any,
        world_state: Any,
        context: Dict[str, Any]
    ) -> Decision:
        """模拟决策生成（用于测试）"""
        
        # 根据角色状态和上下文选择合适的行动
        action_pool = self.action_templates.copy()
        
        # 根据角色健康状态调整
        if role.health < 50:
            action_pool.extend([
                {"type": "rest", "details": "身体状况不佳，需要休息"},
                {"type": "seek_help", "details": "寻找帮助或治疗"},
            ])
        
        # 根据影响力调整
        if role.influence > 70:
            action_pool.extend([
                {"type": "lead", "details": "发挥领导力，指挥他人"},
                {"type": "negotiate", "details": "进行谈判或交涉"},
            ])
        
        # 如果有记忆，可能触发反思
        memories = context.get("memories", [])
        if memories and random.random() < 0.3:
            action_pool.append({
                "type": "reflect", 
                "details": f"回想起: {memories[0][:50]}..."
            })
        
        # 随机选择行动
        action = random.choice(action_pool).copy()
        
        # 可能指定目标（如果世界中有其他角色）
        other_roles = [
            rid for rid in world_state.roles.keys() 
            if str(rid) != str(role.id)
        ]
        if other_roles and random.random() < 0.4:
            action["target"] = str(other_roles[0])
        
        # 生成思考过程
        thought = random.choice(self.thought_templates)
        if memories:
            thought += f" (我记得: {memories[0][:30]}...)"
        
        # 偶尔产生对话
        dialogue = None
        if action["type"] in ["interact", "negotiate", "lead"]:
            dialogues = [
                f"{role.name}: 我们需要谈谈。",
                f"{role.name}: 我发现了一些有趣的事情。",
                f"{role.name}: 你有什么想法？",
                f"{role.name}: 小心，可能有危险。",
            ]
            dialogue = random.choice(dialogues)
        
        return Decision(
            role_id=role.id,
            tick=world_state.tick,
            thought=thought,
            action=action,
            dialogue=dialogue
        )
    
    async def _real_claw_call(
        self,
        role: Any,
        world_state: Any,
        context: Dict[str, Any]
    ) -> Decision:
        """
        真实的 LLM 调用
        TODO: 实现实际的 HTTP API 调用
        """
        # 构建 prompt
        prompt = self._build_prompt(role, world_state, context)
        
        # TODO: 调用实际的 LLM API
        # response = await self._call_llm_api(prompt)
        
        # 临时回退到模拟模式
        return await self._mock_decision(role, world_state, context)
    
    def _build_prompt(
        self,
        role: Any,
        world_state: Any,
        context: Dict[str, Any]
    ) -> str:
        """构建 LLM prompt"""
        
        # 提取角色卡信息
        card = role.card or {}
        drives = card.get("drives", [])
        decision_style = card.get("decision_style", {})
        
        prompt = f"""# 角色决策请求

## 角色信息
- 名称: {role.name}
- 健康: {role.health}/100
- 影响力: {role.influence}/100
- 状态: {role.status}

## 驱动力
{json.dumps(drives, ensure_ascii=False, indent=2)}

## 决策风格
{json.dumps(decision_style, ensure_ascii=False, indent=2)}

## 当前世界状态
- Tick: {world_state.tick}
- 活跃角色数: {len(world_state.roles)}

## 近期记忆
"""
        memories = context.get("memories", [])
        for i, mem in enumerate(memories[:5], 1):
            prompt += f"{i}. {mem}\n"
        
        prompt += """
## 任务
基于以上信息，决定你的下一步行动。请提供：
1. thought: 你的思考过程（角色内心独白）
2. action: 行动类型和细节
3. target: 目标对象（如果有）
4. dialogue: 要说的话（如果有）

请以 JSON 格式返回决策。
"""
        return prompt
    
    async def generate_summary(
        self,
        tick: int,
        events: List[EventORM],
        world_changes: Dict[str, Any]
    ) -> str:
        """生成 tick 摘要"""
        if not events:
            return f"第 {tick} 轮：世界平静地运转着"
        
        event_types = {}
        for e in events:
            etype = e.type if hasattr(e, 'type') else 'unknown'
            event_types[etype] = event_types.get(etype, 0) + 1
        
        summaries = []
        if 'CONFLICT' in event_types:
            summaries.append(f"发生了 {event_types['CONFLICT']} 次冲突")
        if 'NEGOTIATION' in event_types:
            summaries.append(f"进行了 {event_types['NEGOTIATION']} 次谈判")
        if 'DISCOVERY' in event_types:
            summaries.append(f"有 {event_types['DISCOVERY']} 个新发现")
        if 'COMMUNICATION' in event_types:
            summaries.append(f"发生了 {event_types['COMMUNICATION']} 次交流")
        
        if summaries:
            return f"第 {tick} 轮：{', '.join(summaries)}"
        else:
            return f"第 {tick} 轮：世界在变化中"
    
    async def generate_role_thoughts(
        self,
        role: Any,
        recent_events: List[EventORM]
    ) -> str:
        """
        生成角色的内心独白
        用于前端展示角色的想法
        """
        if not recent_events:
            return f"{role.name} 正在思考当前的情况..."
        
        event = recent_events[0]
        thoughts = [
            f"{role.name} 回想着最近发生的事情...",
            f"{role.name} 对 {event.title} 有自己的看法。",
            f"{role.name} 在考虑下一步该怎么做。",
            f"{role.name} 感到局势正在发生变化。",
        ]
        return random.choice(thoughts)


class PromptBuilder:
    """
    Prompt 构建器
    用于构建结构化的 LLM prompt
    """
    
    @staticmethod
    def build_role_card_prompt(role_card: Dict[str, Any]) -> str:
        """从角色卡构建 prompt 片段"""
        sections = []
        
        # 身份
        if "identity" in role_card:
            identity = role_card["identity"]
            sections.append(f"身份: {identity.get('name', '未知')}")
            sections.append(f"背景: {identity.get('background', '未知')}")
        
        # 驱动力
        if "drives" in role_card:
            sections.append("核心驱动力:")
            for drive in role_card["drives"]:
                sections.append(f"  - {drive.get('id')}: 权重 {drive.get('weight', 0.5)}")
        
        # 记忆
        if "memory" in role_card:
            memory = role_card["memory"]
            if "public" in memory:
                sections.append(f"公开记忆: {memory['public']}")
            if "secrets" in memory:
                sections.append(f"秘密: {len(memory['secrets'])} 个")
        
        # 决策风格
        if "decision_style" in role_card:
            style = role_card["decision_style"]
            sections.append(f"决策风格: 风险承受力 {style.get('risk_tolerance', 'medium')}")
        
        return "\n".join(sections)
    
    @staticmethod
    def build_world_context_prompt(world_state: Any) -> str:
        """构建世界上下文 prompt"""
        sections = [
            f"当前时间: 第 {world_state.tick} 轮",
            f"活跃角色数: {len(world_state.roles)}",
        ]
        
        if world_state.global_events:
            sections.append("近期重大事件:")
            for event in world_state.global_events[-3:]:
                sections.append(f"  - {event.get('title', '未知事件')}")
        
        return "\n".join(sections)
