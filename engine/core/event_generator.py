"""
Event Generator - 事件生成系统
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

try:
    from models_sqlite import EventORM, EventType, ConflictResolution
except ImportError:
    from models import EventORM, EventType, ConflictResolution


class EventGenerator:
    """
    事件生成器
    
    将决策、冲突结果转化为可观察的世界事件
    支持不同类型事件的生成和格式化
    """
    
    def __init__(self):
        self.event_id_counter = 0
    
    def generate_events(
        self,
        world_id: str,
        tick: int,
        decisions: List[Any],      # List[Decision]
        resolutions: List[ConflictResolution],
        roles_info: Dict[str, Any]  # 角色信息缓存 {role_id: role_object}
    ) -> List[EventORM]:
        """
        生成所有事件
        
        Args:
            world_id: 世界 ID
            tick: 当前 tick
            decisions: 所有角色决策
            resolutions: 冲突解决结果
            roles_info: 角色信息字典
        
        Returns:
            List[EventORM]: 生成的事件列表
        """
        events = []
        
        # 1. 从决策生成事件
        for decision in decisions:
            event = self._decision_to_event(decision, world_id, tick, roles_info)
            if event:
                events.append(event)
        
        # 2. 从冲突解决生成事件
        for resolution in resolutions:
            event = self._resolution_to_event(resolution, world_id, tick, roles_info)
            if event:
                events.append(event)
        
        # 3. 可能触发的随机环境事件
        if random.random() < 0.1:  # 10% 概率
            event = self._generate_random_event(world_id, tick)
            if event:
                events.append(event)
        
        return events
    
    def _decision_to_event(
        self,
        decision: Any,  # Decision
        world_id: str,
        tick: int,
        roles_info: Dict[str, Any]
    ) -> Optional[EventORM]:
        """将单个决策转换为事件"""
        
        action_type = decision.action.get("type", "")
        
        # 只有特定行动类型会生成可见事件
        event_worthy_actions = [
            "attack", "negotiate", "discover", "move",
            "interact", "lead", "betray", "defend"
        ]
        
        if action_type not in event_worthy_actions:
            return None
        
        # 获取角色信息
        role = roles_info.get(decision.role_id)
        role_name = role.name if role else "未知角色"
        
        # 构建事件
        event_type = self._map_action_to_event_type(action_type)
        
        title_templates = {
            "attack": ["发起攻击", "展开袭击", "发动攻势"],
            "negotiate": ["进行谈判", "外交接触", "商议事宜"],
            "discover": ["重要发现", "发现秘密", "探索成果"],
            "move": ["转移位置", "离开原地", "前往新地"],
            "interact": ["与他人互动", "社交活动", "角色交流"],
            "lead": ["发挥领导力", "指挥行动", "领袖行为"],
            "betray": ["背叛行为", "暗地行动", "秘密谋划"],
            "defend": ["采取防御", "保护行动", "守卫行为"],
        }
        
        titles = title_templates.get(action_type, ["行动"])
        title = random.choice(titles)
        
        # 构建描述
        target_name = ""
        target_id = decision.action.get("target")
        if target_id:
            target = roles_info.get(target_id)
            target_name = target.name if target else "某人"
        
        description = f"{role_name} "
        if target_name:
            description += f"对 {target_name} "
        description += decision.action.get("details", "采取了行动")
        
        if decision.thought:
            description += f"。想法: {decision.thought[:100]}"
        
        # 构建参与者列表（确保所有ID都是字符串）
        participants = [str(decision.role_id)]
        if target_id:
            participants.append(str(target_id))
        
        return EventORM(
            id=str(uuid4()),
            world_id=world_id,
            tick=tick,
            type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            title=f"{role_name}: {title}",
            description=description,
            participants=participants,
            outcome={
                "action": decision.action,
                "dialogue": decision.dialogue,
                "thought_excerpt": decision.thought[:50] if decision.thought else None
            },
            is_canon=True,
            created_at=datetime.utcnow()
        )
    
    def _resolution_to_event(
        self,
        resolution: ConflictResolution,
        world_id: str,
        tick: int,
        roles_info: Dict[str, Any]
    ) -> Optional[EventORM]:
        """将冲突解决结果转换为事件"""
        
        # 只有显著结果才生成事件
        if resolution.outcome_type in ["undetected", "cancelled"]:
            return None
        
        winner = roles_info.get(resolution.winner)
        loser = roles_info.get(resolution.loser) if resolution.loser else None
        
        winner_name = winner.name if winner else "某人"
        loser_name = loser.name if loser else "某人"
        
        # 根据结果类型确定事件类型和标题
        outcome_event_types = {
            "victory": EventType.CONFLICT,
            "narrow_win": EventType.CONFLICT,
            "compromise": EventType.NEGOTIATION,
            "escape": EventType.MOVEMENT,
            "detected": EventType.DISCOVERY,
            "exposed": EventType.CONFLICT,
            "successful_betrayal": EventType.COMMUNICATION,
        }
        
        event_type = outcome_event_types.get(
            resolution.outcome_type, 
            EventType.NATURAL
        )
        
        # 构建标题
        title_templates = {
            "victory": f"冲突: {winner_name} 战胜 {loser_name}",
            "narrow_win": f"冲突: {winner_name} 险胜 {loser_name}",
            "compromise": f"和解: {winner_name} 与 {loser_name} 达成妥协",
            "escape": f"逃脱: {loser_name} 成功脱身",
            "detected": f"发现: {winner_name} 识破秘密",
            "exposed": f"揭露: {winner_name} 揭发了 {loser_name}",
            "successful_betrayal": f"背叛: {winner_name} 的阴谋",
        }
        
        title = title_templates.get(
            resolution.outcome_type,
            f"冲突解决: {resolution.outcome_type}"
        )
        
        # 构建描述
        description = resolution.description
        
        # 添加结果影响描述
        changes_desc = []
        for change in resolution.world_changes:
            if change and change.get("type") == "influence_change":
                target = roles_info.get(change["target"])
                target_name = target.name if target else "某人"
                delta = change.get("delta", 0)
                if delta > 0:
                    changes_desc.append(f"{target_name} 影响力 +{delta}")
                else:
                    changes_desc.append(f"{target_name} 影响力 {delta}")
        
        if changes_desc:
            description += " 影响: " + ", ".join(changes_desc)
        
        # 构建参与者（确保都是字符串）
        participants = [str(resolution.winner)]
        if resolution.loser:
            participants.append(str(resolution.loser))
        
        return EventORM(
            id=str(uuid4()),
            world_id=world_id,
            tick=tick,
            type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            title=title,
            description=description,
            participants=participants,
            outcome={
                "resolution_type": resolution.outcome_type,
                "world_changes": resolution.world_changes,
                "winner": str(resolution.winner) if resolution.winner else None,
                "loser": str(resolution.loser) if resolution.loser else None
            },
            is_canon=True,
            created_at=datetime.utcnow()
        )
    
    def _generate_random_event(
        self,
        world_id: str,
        tick: int
    ) -> Optional[EventORM]:
        """生成随机环境事件"""
        
        random_events = [
            {
                "type": EventType.NATURAL,
                "title": "天气变化",
                "description": "天空突然阴沉，似乎要下雨了。"
            },
            {
                "type": EventType.NATURAL,
                "title": "风向转变",
                "description": "一阵奇怪的风从北方吹来。"
            },
            {
                "type": EventType.NATURAL,
                "title": "野兽出没",
                "description": "附近传来了野兽的嚎叫声。"
            },
            {
                "type": EventType.NATURAL,
                "title": "流星划过",
                "description": "一颗明亮的流星划过夜空。"
            },
        ]
        
        event_data = random.choice(random_events)
        
        return EventORM(
            id=str(uuid4()),
            world_id=world_id,
            tick=tick,
            type=event_data["type"].value if hasattr(event_data["type"], 'value') else str(event_data["type"]),
            title=event_data["title"],
            description=event_data["description"],
            participants=[],
            outcome={"random": True},
            is_canon=True,
            created_at=datetime.utcnow()
        )
    
    def _map_action_to_event_type(self, action_type: str) -> EventType:
        """映射行动类型到事件类型"""
        mapping = {
            "attack": EventType.CONFLICT,
            "confront": EventType.CONFLICT,
            "defend": EventType.CONFLICT,
            "negotiate": EventType.NEGOTIATION,
            "interact": EventType.COMMUNICATION,
            "speak": EventType.COMMUNICATION,
            "discover": EventType.DISCOVERY,
            "investigate": EventType.DISCOVERY,
            "move": EventType.MOVEMENT,
            "gather": EventType.NATURAL,
            "rest": EventType.NATURAL,
            "observe": EventType.NATURAL,
            "lead": EventType.COMMUNICATION,
            "betray": EventType.CONFLICT,
        }
        return mapping.get(action_type, EventType.NATURAL)
    
    def generate_milestone_event(
        self,
        world_id: str,
        tick: int,
        milestone_type: str,
        description: str,
        affected_roles: List[str]
    ) -> EventORM:
        """
        生成里程碑事件
        用于标记世界中的重要转折点
        """
        milestone_titles = {
            "world_creation": "世界诞生",
            "first_contact": "首次接触",
            "major_conflict": "重大冲突",
            "alliance_formed": "联盟建立",
            "secret_revealed": "秘密揭露",
            "character_death": "角色死亡",
            "era_change": "时代更迭",
        }
        
        title = milestone_titles.get(milestone_type, "重要事件")
        
        return EventORM(
            id=str(uuid4()),
            world_id=world_id,
            tick=tick,
            type=EventType.DIVINE.value if hasattr(EventType.DIVINE, 'value') else "DIVINE",
            title=f"[里程碑] {title}",
            description=description,
            participants=affected_roles,
            outcome={"milestone": True, "type": milestone_type},
            is_canon=True,
            created_at=datetime.utcnow()
        )
