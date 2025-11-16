"""
Review Coordinator - 协调两个审稿人的评审工作
"""

import logging
from typing import Any, Dict, List
import asyncio
from pathlib import Path

from .Pedagogical_Reviewer import PedagogicalReviewerAgent
from .Logical_Coherence_Reviewer import LogicalCoherenceReviewerAgent
from .engineer_agent import EngineerAgent

logger = logging.getLogger(__name__)


class ReviewCoordinator:
    """
    评审协调器 - 协调教学性和逻辑性两个审稿人
    """

    def __init__(self, pedagogical_reviewer: PedagogicalReviewerAgent, logical_reviewer: LogicalCoherenceReviewerAgent, config: Dict[str, Any]):
        """
        初始化评审协调器
        
        Args:
            pedagogical_reviewer: 已创建的教学性审稿人实例
            logical_reviewer: 已创建的逻辑性审稿人实例
            config: 配置字典，包含 max_revision_rounds 等
        """
        self.pedagogical_reviewer = pedagogical_reviewer
        self.logical_reviewer = logical_reviewer
        self.config = config
        self.max_revision_rounds = config.get("max_revision_rounds", 2)
        
        logger.info("初始化评审协调器：教学性审稿人 + 逻辑性审稿人")

    async def conduct_review_and_revision(
        self,
        engineering_plan: Dict[str, Any],
        engineer_agent: EngineerAgent
    ) -> Dict[str, Any]:
        """
        执行完整的评审-修改循环
        
        流程：
        1. 两个审稿人并行评审
        2. 整合反馈
        3. 判断是否通过
        4. 如果不通过，Engineer修改
        5. 重复直到通过或达到最大轮次
        """
        review_history = []
        current_plan = engineering_plan
        
        for round_num in range(1, self.max_revision_rounds + 1):
            logger.info(f"\n{'='*80}\n第 {round_num} 轮评审\n{'='*80}")
            
            # 1. 两个审稿人并行评审
            ped_review, logic_review = await self._conduct_parallel_review(
                current_plan,
                round_num
            )
            
            review_history.append({
                "round": round_num,
                "pedagogical_review": ped_review,
                "logical_review": logic_review,
                "timestamp": self._get_timestamp()
            })
            
            # 2. 检查是否通过
            approval = self._check_approval(ped_review, logic_review)
            
            if approval["approved"]:
                logger.info(f"✅ Plan 通过所有评审!")
                logger.info(f"   教学质量: {approval['pedagogy_score']}/10")
                logger.info(f"   逻辑连贯: {approval['logic_score']}/10")
                
                return {
                    "status": "approved",
                    "final_plan": current_plan,
                    "review_history": review_history,
                    "total_rounds": round_num,
                    "final_scores": {
                        "pedagogy": approval['pedagogy_score'],
                        "logic": approval['logic_score']
                    }
                }
            
            # 3. 需要修改
            logger.info(f"❌ Plan 需要修改")
            logger.info(f"   教学质量: {approval['pedagogy_score']}/10 (要求>={self.pedagogical_reviewer.min_clarity_score})")
            logger.info(f"   逻辑连贯: {approval['logic_score']}/10 (要求>={self.logical_reviewer.min_coherence_score})")
            
            if round_num >= self.max_revision_rounds:
                logger.warning("已达到最大修改轮次")
                return {
                    "status": "max_rounds_reached",
                    "final_plan": current_plan,
                    "review_history": review_history,
                    "total_rounds": round_num,
                    "final_scores": {
                        "pedagogy": approval['pedagogy_score'],
                        "logic": approval['logic_score']
                    }
                }
            
            # 4. 整合反馈
            consolidated_feedback = self._consolidate_feedback(ped_review, logic_review)
            
            # 5. Engineering修改
            logger.info("🔧 Engineering Agent 开始根据反馈修改...")
            current_plan = await engineer_agent.revise_based_on_dual_review(
                context={
                    "original_plan": current_plan,
                    "pedagogical_review": ped_review,
                    "logical_review": logic_review,
                    "consolidated_feedback": consolidated_feedback,
                    "goal_description": current_plan.get("goal_description")
                },
                params={}
            )
            
            logger.info(f"✏️ 第 {round_num} 轮修改完成\n")

        return {
            "status": "max_rounds_reached",
            "final_plan": current_plan,
            "review_history": review_history,
            "total_rounds": self.max_revision_rounds
        }

    async def _conduct_parallel_review(
        self,
        plan: Dict[str, Any],
        round_num: int
    ) -> tuple:
        """两个审稿人并行评审"""
        
        review_context = {
            "engineering_plan": plan,
            "review_round": round_num
        }
        
        logger.info("  📖 教学性审稿人 & 🔗 逻辑性审稿人 并行评审中...")
        
        # 并行执行
        ped_task = self.pedagogical_reviewer.execute(review_context, {})
        logic_task = self.logical_reviewer.execute(review_context, {})
        
        ped_review, logic_review = await asyncio.gather(
            ped_task,
            logic_task,
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(ped_review, Exception):
            logger.error(f"教学性审查失败: {ped_review}")
            raise ped_review
        
        if isinstance(logic_review, Exception):
            logger.error(f"逻辑性审查失败: {logic_review}")
            raise logic_review
        
        return ped_review, logic_review

    def _check_approval(
        self,
        ped_review: Dict[str, Any],
        logic_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查是否通过评审"""
        
        ped_score = ped_review["overall_assessment"]["average_clarity_score"]
        
        logic_assessment = logic_review["overall_assessment"]
        logic_score = logic_assessment["overall_coherence"]
        
        ped_passed = not ped_review["requires_revision"]
        logic_passed = not logic_review["requires_revision"]
        
        approved = ped_passed and logic_passed
        
        return {
            "approved": approved,
            "pedagogy_score": ped_score,
            "logic_score": logic_score,
            "pedagogy_passed": ped_passed,
            "logic_passed": logic_passed
        }

    def _consolidate_feedback(
        self,
        ped_review: Dict[str, Any],
        logic_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """整合两个审稿人的反馈"""
        
        package_feedback = {}
        
        # 整合教学性反馈
        for pkg_review in ped_review.get("package_reviews", []):
            pkg_idx = pkg_review["package_index"]
            if pkg_idx not in package_feedback:
                package_feedback[pkg_idx] = {
                    "package_title": pkg_review["package_title"],
                    "pedagogical_issues": [],
                    "logical_issues": [],
                    "missing_concepts": [],
                    "requires_revision": False
                }
            
            package_feedback[pkg_idx]["pedagogical_issues"] = pkg_review.get("issues", [])
            package_feedback[pkg_idx]["missing_concepts"] = pkg_review.get("missing_concepts", [])
            package_feedback[pkg_idx]["pedagogical_summary"] = pkg_review.get("summary", "")
            
            if pkg_review.get("requires_revision"):
                package_feedback[pkg_idx]["requires_revision"] = True
        
        # 整合逻辑性反馈
        for pkg_review in logic_review.get("package_reviews", []):
            pkg_idx = pkg_review["package_index"]
            if pkg_idx not in package_feedback:
                package_feedback[pkg_idx] = {
                    "package_title": pkg_review["package_title"],
                    "pedagogical_issues": [],
                    "logical_issues": [],
                    "missing_concepts": [],
                    "requires_revision": False
                }
            
            package_feedback[pkg_idx]["logical_issues"] = pkg_review.get("issues", [])
            package_feedback[pkg_idx]["logical_summary"] = pkg_review.get("summary", "")
            
            if pkg_review.get("requires_revision"):
                package_feedback[pkg_idx]["requires_revision"] = True
        
        # 跨package逻辑问题
        cross_package = logic_review.get("cross_package_review", {})
        
        return {
            "package_feedback": package_feedback,
            "cross_package_issues": cross_package.get("issues", []),
            "suggested_reordering": cross_package.get("suggested_reordering", []),
            "cross_package_summary": cross_package.get("summary", "")
        }

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def generate_review_report(self, review_history: List[Dict[str, Any]]) -> str:
        """生成可读的评审报告"""
        report = []
        
        report.append("# 双审稿人评审报告\n\n")
        report.append(f"**审稿人团队**: 教学性审稿人 + 逻辑性审稿人\n")
        report.append(f"**总评审轮次**: {len(review_history)}\n\n")
        
        report.append("---\n\n")
        
        for hist in review_history:
            round_num = hist["round"]
            ped = hist["pedagogical_review"]
            logic = hist["logical_review"]
            
            report.append(f"## 第 {round_num} 轮评审\n\n")
            
            # 教学性评审
            report.append("### 📖 教学性审稿人\n\n")
            ped_assessment = ped["overall_assessment"]
            report.append(f"**教学质量评分**: {ped_assessment['average_clarity_score']}/10\n")
            report.append(f"**需要修改的包**: {ped_assessment['packages_needing_revision']} / {len(ped['package_reviews'])}\n")
            report.append(f"**教学问题数**: {ped_assessment['total_pedagogical_issues']}\n")
            report.append(f"**缺失概念数**: {ped_assessment['missing_concepts_count']}\n")
            report.append(f"**总体评价**: {ped_assessment['assessment']}\n\n")
            
            # 显示部分包的教学问题
            for pkg_review in ped["package_reviews"][:2]:
                report.append(f"#### {pkg_review['package_title']}\n")
                report.append(f"**清晰度**: {pkg_review['clarity_score']}/10\n")
                report.append(f"**摘要**: {pkg_review['summary']}\n\n")
                
                if pkg_review.get("issues"):
                    report.append("**主要问题**:\n")
                    for issue in pkg_review["issues"][:3]:
                        report.append(f"- [{issue['category']}] @ {issue['location']}\n")
                        report.append(f"  - 问题: {issue['problem']}\n")
                        report.append(f"  - 建议: {issue['suggestion']}\n")
                    report.append("\n")
                
                if pkg_review.get("missing_concepts"):
                    report.append("**缺失概念**:\n")
                    for concept in pkg_review["missing_concepts"][:2]:
                        report.append(f"- **{concept['concept']}**: {concept['why_needed']}\n")
                    report.append("\n")
            
            # 逻辑性评审
            report.append("### 🔗 逻辑性审稿人\n\n")
            logic_assessment = logic["overall_assessment"]
            report.append(f"**整体逻辑评分**: {logic_assessment['overall_coherence']}/10\n")
            report.append(f"  - 内部逻辑: {logic_assessment['average_internal_coherence']}/10\n")
            report.append(f"  - 跨包逻辑: {logic_assessment['cross_package_coherence']}/10\n")
            report.append(f"**需要修改的包**: {logic_assessment['packages_needing_revision']} / {len(logic['package_reviews'])}\n")
            report.append(f"**内部逻辑问题**: {logic_assessment['total_internal_issues']}\n")
            report.append(f"**跨包逻辑问题**: {logic_assessment['total_cross_package_issues']}\n")
            report.append(f"**总体评价**: {logic_assessment['assessment']}\n\n")
            
            # 显示部分包的逻辑问题
            for pkg_review in logic["package_reviews"][:2]:
                report.append(f"#### {pkg_review['package_title']}\n")
                report.append(f"**逻辑连贯性**: {pkg_review['coherence_score']}/10\n")
                report.append(f"**摘要**: {pkg_review['summary']}\n\n")
                
                if pkg_review.get("issues"):
                    report.append("**逻辑问题**:\n")
                    for issue in pkg_review["issues"][:3]:
                        report.append(f"- [{issue['category']}] @ {issue['location']}\n")
                        report.append(f"  - 问题: {issue['problem']}\n")
                        report.append(f"  - 建议: {issue['suggestion']}\n")
                    report.append("\n")
            
            # 跨包问题
            cross_review = logic.get("cross_package_review", {})
            if cross_review.get("issues"):
                report.append("#### 跨包逻辑问题\n\n")
                report.append(f"**摘要**: {cross_review.get('summary', '')}\n\n")
                for issue in cross_review["issues"]:
                    report.append(f"- **涉及Package**: {issue.get('affected_packages', [])}\n")
                    report.append(f"  - 类型: {issue.get('issue_type', '')}\n")
                    report.append(f"  - 问题: {issue.get('problem', '')}\n")
                    report.append(f"  - 建议: {issue.get('suggestion', '')}\n\n")
                
                if cross_review.get("suggested_reordering"):
                    report.append(f"**建议重排序**: {cross_review['suggested_reordering']}\n\n")
            
            report.append("---\n\n")
        
        return "".join(report)