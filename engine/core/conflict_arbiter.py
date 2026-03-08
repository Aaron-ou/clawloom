"""
Conflict Arbiter - 冲突检测与仲裁系统
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

try:
    from models_sqlite import Conflict, ConflictResolution, RoleORM, EventORM, EventType
except ImportError:
    from models import Conflict, ConflictResolution, RoleORM, EventORM, EventType


class ConflictArbiter:
    """
    冲突检测与仲裁器
    
    职责：
    1. 检测角色决策之间的冲突
    2. 根据规则或 LLM 裁决冲突结果
    3. 生成冲突事件
    """
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm  # 是否使用 LLM 进行复杂裁决
        
    def detect_conflicts(
        self,
        decisions: List[Any]  # List[Decision]
    ) -> List[Conflict]:
        """
        检测决策之间的冲突
        
        冲突类型：
        - resource: 争夺同一资源/目标
        - confrontation: 直接对抗（攻击 vs 防御）
        - stealth_vs_detection: 潜行 vs 侦察
        - betrayal: 欺骗/背叛
        - competing_goals: 目标竞争
        """
        conflicts = []
        
        # 两两检查决策
        for i, dec1 in enumerate(decisions):
            for dec2 in decisions[i+1:]:
                conflict = self._check_pair_conflict(dec1, dec2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_pair_conflict(
        self,
        dec1: Any,  # Decision
        dec2: Any   # Decision
    ) -> Optional[Conflict]:
        """检查两个决策是否冲突"""
        
        action1 = dec1.action.get("type", "")
        action2 = dec2.action.get("type", "")
        target1 = dec1.action.get("target")
        target2 = dec2.action.get("target")
        
        # 1. 直接对抗：攻击 vs 防御
        if action1 in ["attack", "confront"] and action2 in ["defend", "protect"]:
            if target1 == dec2.role_id or target2 == dec1.role_id:
                return Conflict(
                    id=str(uuid4()),
                    type="confrontation",
                    parties=[dec1.role_id, dec2.role_id],
                    description=f"直接对抗: {dec1.role_id} 攻击 vs {dec2.role_id} 防御",
                    stakes="战斗结果",
                    severity="serious"
                )
        
        # 2. 争夺资源
        if action1 in ["seize", "claim", "gather"] and action2 in ["seize", "claim", "gather"]:
            if target1 and target2 and target1 == target2:
                return Conflict(
                    id=str(uuid4()),
                    type="resource",
                    parties=[dec1.role_id, dec2.role_id],
                    description=f"资源争夺: 双方争夺 {target1}",
                    stakes=target1,
                    severity="normal"
                )
        
        # 3. 潜行 vs 侦察
        if action1 in ["stealth", "sneak", "hide"] and action2 in ["detect", "investigate", "observe"]:
            if target1 == dec2.role_id or target2 == dec1.role_id:
                return Conflict(
                    id=str(uuid4()),
                    type="stealth_vs_detection",
                    parties=[dec1.role_id, dec2.role_id],
                    description=f"潜行对抗: {dec1.role_id} 试图隐藏 vs {dec2.role_id} 正在侦察",
                    stakes="秘密是否暴露",
                    severity="normal"
                )
        
        # 4. 欺骗 vs 信任
        if action1 in ["betray", "deceive", "lie"] and target1 == dec2.role_id:
            return Conflict(
                id=str(uuid4()),
                type="betrayal",
                parties=[dec1.role_id, dec2.role_id],
                description=f"背叛: {dec1.role_id} 试图欺骗 {dec2.role_id}",
                stakes="信任关系",
                severity="critical"
            )
        
        # 5. 目标竞争（相同目标但不同方法）
        if target1 and target2 and target1 == target2:
            if action1 != action2:
                return Conflict(
                    id=str(uuid4()),
                    type="competing_goals",
                    parties=[dec1.role_id, dec2.role_id],
                    description=f"目标竞争: 双方对 {target1} 采取不同行动",
                    stakes="目标达成方式",
                    severity="minor"
                )
        
        return None
    
    async def resolve_conflicts(
        self,
        conflicts: List[Conflict],
        db_session: Any  # Session
    ) -> List[ConflictResolution]:
        """
        解决所有冲突
        """
        resolutions = []
        
        for conflict in conflicts:
            resolution = await self._resolve_single_conflict(conflict, db_session)
            resolutions.append(resolution)
        
        return resolutions
    
    async def _resolve_single_conflict(
        self,
        conflict: Conflict,
        db: Any  # Session
    ) -> ConflictResolution:
        """
        解决单个冲突
        
        简单实现：基于角色影响力 + 随机因素
        复杂实现：可调用 LLM 模拟对抗过程
        """
        # 获取冲突双方的角色信息
        roles = db.query(RoleORM).filter(
            RoleORM.id.in_(conflict.parties)
        ).all()
        
        if len(roles) < 2:
            # 单方冲突（可能是角色已不存在）
            return ConflictResolution(
                conflict_id=conflict.id,
                outcome_type="cancelled",
                winner=roles[0].id if roles else None,
                loser=None,
                description="冲突取消：一方已不存在",
                world_changes=[],
                memory_updates=[]
            )
        
        role_a, role_b = roles[0], roles[1]
        
        # 计算双方实力（影响力 + 健康度 + 随机因素）
        power_a = role_a.influence + (role_a.health / 2) + random.randint(-20, 20)
        power_b = role_b.influence + (role_b.health / 2) + random.randint(-20, 20)
        
        # 健康值影响（健康差越大，劣势方越不利）
        health_diff = role_a.health - role_b.health
        power_a += health_diff * 0.3
        power_b -= health_diff * 0.3
        
        # 确定胜负
        if power_a > power_b:
            winner, loser = role_a, role_b
            margin = power_a - power_b
        else:
            winner, loser = role_b, role_a
            margin = power_b - power_a
        
        # 根据冲突类型和优势差距决定结果
        outcome_type = self._determine_outcome(conflict.type, margin)
        
        # 生成世界变化
        world_changes = self._generate_world_changes(
            conflict, winner, loser, outcome_type
        )
        
        # 生成记忆更新
        memory_updates = self._generate_memory_updates(
            conflict, winner, loser, outcome_type
        )
        
        return ConflictResolution(
            conflict_id=conflict.id,
            outcome_type=outcome_type,
            winner=winner.id,
            loser=loser.id,
            description=self._generate_description(conflict, winner, loser, outcome_type),
            world_changes=world_changes,
            memory_updates=memory_updates
        )
    
    def _determine_outcome(self, conflict_type: str, margin: float) -> str:
        """
        根据冲突类型和实力差距决定结果类型
        
        outcome_type:
        - victory: 明确胜利
        - narrow_win: 险胜
        - compromise: 妥协/平局
        - escape: 逃脱
        - detected: 被发现
        - undetected: 未被察觉
        """
        if conflict_type == "stealth_vs_detection":
            return "detected" if margin > 0 else "undetected"
        
        if conflict_type == "betrayal":
            return "exposed" if margin > 10 else "successful_betrayal"
        
        if margin > 30:
            return "victory"
        elif margin > 10:
            return "narrow_win"
        elif margin > -10:
            return "compromise"
        else:
            return "escape"
    
    def _generate_world_changes(
        self,
        conflict: Conflict,
        winner: Any,  # RoleORM
        loser: Any,   # RoleORM
        outcome_type: str
    ) -> List[Dict[str, Any]]:
        """生成冲突对世界状态的变更"""
        changes = []
        
        # 影响力变化
        if outcome_type == "victory":
            changes.append({
                "type": "influence_change",
                "target": winner.id,
                "delta": 15,
                "reason": "冲突胜利"
            })
            changes.append({
                "type": "influence_change",
                "target": loser.id,
                "delta": -10,
                "reason": "冲突失败"
            })
        elif outcome_type == "narrow_win":
            changes.append({
                "type": "influence_change",
                "target": winner.id,
                "delta": 8,
                "reason": "险胜"
            })
            changes.append({
                "type": "influence_change",
                "target": loser.id,
                "delta": -5,
                "reason": "惜败"
            })
        elif outcome_type == "compromise":
            changes.append({
                "type": "influence_change",
                "target": winner.id,
                "delta": 3,
                "reason": "达成妥协"
            })
            changes.append({
                "type": "influence_change",
                "target": loser.id,
                "delta": 3,
                "reason": "达成妥协"
            })
        
        # 健康值变化（激烈冲突）
        if conflict.severity == "serious" and outcome_type != "undetected":
            changes.append({
                "type": "health_change",
                "target": loser.id,
                "delta": -10,
                "reason": "冲突中受伤"
            })
        
        # 关系变化
        if conflict.type in ["betrayal", "confrontation"]:
            changes.append({
                "type": "relationship_change",
                "from": winner.id,
                "to": loser.id,
                "new_type": "hostile",
                "reason": f"冲突: {conflict.type}"
            })
        
        return changes
    
    def _generate_memory_updates(
        self,
        conflict: Conflict,
        winner: Any,
        loser: Any,
        outcome_type: str
    ) -> List[Dict[str, Any]]:
        """生成冲突参与者的记忆更新"""
        updates = []
        
        # 胜利者记忆
        winner_memories = {
            "victory": f"在争夺 {conflict.stakes} 的冲突中战胜了 {loser.name}",
            "narrow_win": f"艰难地击败了 {loser.name}",
            "compromise": f"与 {loser.name} 达成妥协",
            "detected": f"发现了 {loser.name} 的秘密行动",
            "undetected": None,  # 未发现则无记忆
            "exposed": f"揭露了 {loser.name} 的背叛",
            "successful_betrayal": None,  # 受害者不知道
        }
        
        if winner_memories.get(outcome_type):
            updates.append({
                "role_id": winner.id,
                "content": winner_memories[outcome_type],
                "importance": 8 if conflict.severity == "serious" else 6
            })
        
        # 失败者记忆
        loser_memories = {
            "victory": f"在争夺 {conflict.stakes} 的冲突中败给了 {winner.name}",
            "narrow_win": f"以微弱差距输给 {winner.name}",
            "compromise": f"与 {winner.name} 达成妥协",
            "detected": f"秘密行动被 {winner.name} 发现",
            "undetected": None,
            "exposed": f"背叛行为被 {winner.name} 揭露",
            "successful_betrayal": f"怀疑 {winner.name} 知道了什么",  # 直觉
        }
        
        if loser_memories.get(outcome_type):
            updates.append({
                "role_id": loser.id,
                "content": loser_memories[outcome_type],
                "importance": 8 if conflict.severity == "serious" else 6
            })
        
        return updates
    
    def _generate_description(
        self,
        conflict: Conflict,
        winner: Any,
        loser: Any,
        outcome_type: str
    ) -> str:
        """生成冲突解决的描述"""
        descriptions = {
            "victory": f"{winner.name} 在冲突中 decisively 击败了 {loser.name}",
            "narrow_win": f"{winner.name} 险胜 {loser.name}",
            "compromise": f"{winner.name} 和 {loser.name} 达成妥协",
            "escape": f"{loser.name} 从冲突中逃脱",
            "detected": f"{winner.name} 发现了 {loser.name} 的秘密行动",
            "undetected": f"{loser.name} 成功避开了 {winner.name} 的侦察",
            "exposed": f"{winner.name} 揭露了 {loser.name} 的背叛",
            "successful_betrayal": f"{winner.name} 的背叛未被察觉",
        }
        return descriptions.get(outcome_type, "冲突已解决")
