"""
Clinical interpreter for assessment significance and recommendations.

=== 临床解释处理流程 ===
本文件实现了从评估结果到临床解释和建议的完整转换流程，主要分为以下阶段：

【核心方法: assess_clinical_significance】
    输入: 当前评估结果 + 基线结果（可选）+ 历史结果（可选）
    过程: 初始化 → 基线变化计算 → 风险评估 → 建议生成 → 监控优先级确定
    输出: 完整临床评估字典

【辅助方法】
    - _assess_risk_level: 风险评估（自杀意念、严重症状、快速恶化）
    - _generate_clinical_recommendations: 临床建议生成（多层次建议）
    - _determine_monitoring_priority: 监控优先级确定
    - analyze_longitudinal_trends: 纵向趋势分析
    - generate_clinical_summary: 临床摘要生成
    - interpret_xxx_result: 单量表结果解释（简化版）
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.models.assessment import (
    AssessmentResult, PHQ9Result, GAD7Result, PSS10Result, 
    AssessmentSession, SeverityLevel
)
from src.models.persona import Persona
from src.core.experiment_config import experiment_config


logger = logging.getLogger(__name__)


class ClinicalInterpreter:
    """
    【临床解释器】
    
    职责: 将评估结果转换为可操作的临床解释、风险评估和建议
    
    核心功能:
    1. 临床意义评估: 计算与基线的变化，判断临床重要性
    2. 风险评估: 检测自杀意念、严重症状、快速恶化等风险
    3. 建议生成: 根据风险级别和临床意义生成分级建议
    4. 趋势分析: 分析多次评估的纵向变化趋势
    5. 摘要生成: 生成综合临床摘要
    """
    
    def __init__(self):
        """初始化临床解释器，加载配置阈值"""
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """
        【配置加载】从配置文件加载临床阈值和风险标准
        
        加载内容:
        1. 临床意义阈值（minimal_change, moderate_change, severe_change）
        2. 风险评估标准（自杀意念、严重症状、快速恶化阈值）
        """
        config = experiment_config.get_config("clinical_thresholds")
        
        # ===== 临床意义阈值配置 =====
        # 用于判断评估结果相对于基线的变化是否具有临床意义
        self.clinical_thresholds = config.get("clinical_significance", {
            "phq9": {
                "minimal_change": 5.0,
                "moderate_change": 10.0,
                "severe_change": 15.0
            },
            "gad7": {
                "minimal_change": 5.0,
                "moderate_change": 10.0,
                "severe_change": 15.0
            },
            "pss10": {
                "minimal_change": 5.0,
                "moderate_change": 10.0,
                "severe_change": 15.0
            }
        })
        
        # ===== 风险评估标准配置 =====
        # 用于识别高风险情况和需要紧急干预的案例
        self.risk_criteria = config.get("risk_assessment", {
            "suicidal_ideation": {
                "phq9_item_9_threshold": 2,  # Score of 2 or 3 on suicidal ideation item
                "critical_threshold": 2
            },
            "severe_symptoms": {
                "phq9_total": 20,
                "gad7_total": 20,
                "pss10_total": 25
            },
            "rapid_deterioration": {
                "weekly_increase": 10,  # 10+ point increase in a week
                "monthly_increase": 15   # 15+ point increase in a month
            }
        })
    
    def assess_clinical_significance(self, current_result: AssessmentResult, 
                                   baseline_result: Optional[AssessmentResult] = None,
                                   previous_results: Optional[List[AssessmentResult]] = None) -> Dict[str, Any]:
        """
        【核心方法】评估评估结果的临床意义
        
        处理流程:
        Stage 1: 初始化评估字典（默认值）
        Stage 2: 计算基线变化（如果有基线数据）
        Stage 3: 评估风险级别（调用 _assess_risk_level）
        Stage 4: 生成临床建议（调用 _generate_clinical_recommendations）
        Stage 5: 确定监控优先级（调用 _determine_monitoring_priority）
        
        Args:
            current_result: 当前评估结果
            baseline_result: 基线评估结果（可选，用于计算变化）
            previous_results: 历史评估结果列表（可选，用于趋势分析）
            
        Returns:
            Dict[str, Any]: 完整临床评估字典，包含风险级别、建议、监控优先级等
        """
        try:
            # ===== Stage 1: 初始化评估字典 =====
            # 设置所有字段的默认值，后续阶段会逐步填充
            assessment = {
                "is_clinically_significant": False,  # 默认无临床意义
                "significance_level": "none",         # 默认无显著变化
                "change_magnitude": 0.0,              # 默认变化幅度为 0
                "trend_direction": "stable",          # 默认趋势稳定
                "risk_level": "low",                  # 默认低风险
                "clinical_recommendations": [],       # 建议列表（待填充）
                "risk_factors": [],                   # 风险因素列表（待填充）
                "monitoring_priority": "routine"      # 默认常规监控
            }
            
            # ===== Stage 2: 计算基线变化（如果有基线数据）=====
            if baseline_result:
                change = current_result.total_score - baseline_result.total_score
                assessment["change_magnitude"] = abs(change)
                assessment["trend_direction"] = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
                
                # Determine significance level
                thresholds = self.clinical_thresholds.get(current_result.assessment_type, {})
                if abs(change) >= thresholds.get("severe_change", 15):
                    assessment["significance_level"] = "severe"
                    assessment["is_clinically_significant"] = True
                elif abs(change) >= thresholds.get("moderate_change", 10):
                    assessment["significance_level"] = "moderate"
                    assessment["is_clinically_significant"] = True
                elif abs(change) >= thresholds.get("minimal_change", 5):
                    assessment["significance_level"] = "minimal"
                    assessment["is_clinically_significant"] = True
            
            # ===== Stage 3: 评估风险级别 =====
            # 调用辅助方法评估当前结果的风险级别
            # 检查：自杀意念、严重症状、快速恶化
            risk_assessment = self._assess_risk_level(current_result, previous_results)
            assessment["risk_level"] = risk_assessment["risk_level"]      # 风险级别（critical/high/moderate/low）
            assessment["risk_factors"] = risk_assessment["risk_factors"]  # 风险因素列表
            
            # ===== Stage 4: 生成临床建议 =====
            # 根据风险级别、临床意义、评估类型等生成分层建议
            recommendations = self._generate_clinical_recommendations(
                current_result, assessment, risk_assessment
            )
            assessment["clinical_recommendations"] = recommendations
            
            # ===== Stage 5: 确定监控优先级 =====
            # 根据风险级别和临床意义确定监控的紧急程度
            assessment["monitoring_priority"] = self._determine_monitoring_priority(assessment)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing clinical significance: {e}")
            return {"error": str(e)}
    
    def _assess_risk_level(self, result: AssessmentResult, 
                          previous_results: Optional[List[AssessmentResult]] = None) -> Dict[str, Any]:
        """
        【风险评估】评估当前评估结果的风险级别
        
        处理流程:
        Stage 1: 初始化风险评估字典（默认低风险）
        Stage 2: 检查自杀意念（仅 PHQ-9，触发 critical 级别）
        Stage 3: 检查严重症状（总分阈值，触发 high 级别）
        Stage 4: 检查快速恶化（需要历史数据，触发 moderate 级别）
        
        风险级别优先级:
        - critical: 自杀意念（最高优先级）
        - high: 严重症状
        - moderate: 快速恶化
        - low: 默认（无风险）
        
        Args:
            result: 当前评估结果
            previous_results: 历史评估结果列表（可选，用于检测快速恶化）
            
        Returns:
            Dict[str, Any]: 风险评估字典，包含风险级别、风险因素、各类型风险标志
        """
        # ===== Stage 1: 初始化风险评估字典 =====
        # 默认所有风险为 False，风险级别为 low
        risk_assessment = {
            "risk_level": "low",              # 默认低风险
            "risk_factors": [],               # 风险因素列表（待填充）
            "suicidal_risk": False,           # 自杀意念风险标志
            "severe_symptom_risk": False,     # 严重症状风险标志
            "rapid_deterioration_risk": False # 快速恶化风险标志
        }
        
        try:
            # ===== Stage 2: 检查自杀意念（最高优先级）=====
            # ⚠️ 仅适用于 PHQ-9，Item 9 ≥ 2 立即触发 critical 级别
            if isinstance(result, PHQ9Result):
                suicidal_threshold = self.risk_criteria.get("suicidal_ideation", {}).get("phq9_item_9_threshold", 2)
                if result.suicidal_ideation_score >= suicidal_threshold:
                    risk_assessment["suicidal_risk"] = True
                    risk_assessment["risk_factors"].append("suicidal_ideation")
                    risk_assessment["risk_level"] = "critical"
            
            # ===== Stage 3: 检查严重症状 =====
            # 检查总分是否达到严重症状阈值（PHQ-9/GAD-7: ≥20, PSS-10: ≥25）
            severe_symptoms = self.risk_criteria.get("severe_symptoms", {})
            threshold_key = f"{result.assessment_type}_total"  # 如 "phq9_total"
            
            if result.total_score >= severe_symptoms.get(threshold_key, 20):
                # 检测到严重症状：如果没有 critical 风险，则设为 high 级别
                risk_assessment["severe_symptom_risk"] = True
                risk_assessment["risk_factors"].append("severe_symptoms")
                
                # 优先级保护：如果已经是 critical（自杀意念），不降级
                if risk_assessment["risk_level"] != "critical":
                    risk_assessment["risk_level"] = "high"
            
            # ===== Stage 4: 检查快速恶化 =====
            # 需要至少 2 个历史评估结果才能检测快速恶化
            if previous_results and len(previous_results) >= 2:
                # Stage 4.1: 获取最近的评估结果
                recent_results = sorted(previous_results, key=lambda x: x.simulation_day)[-2:]
                
                if len(recent_results) >= 2:
                    # Stage 4.2: 计算最近的变化
                    change = result.total_score - recent_results[0].total_score
                    rapid_threshold = self.risk_criteria.get("rapid_deterioration", {}).get("weekly_increase", 10)
                    
                    # Stage 4.3: 判断是否快速恶化（增加 ≥ 10 分）
                    if change >= rapid_threshold:
                        # 检测到快速恶化：如果没有 critical 或 high 风险，则设为 moderate 级别
                        risk_assessment["rapid_deterioration_risk"] = True
                        risk_assessment["risk_factors"].append("rapid_deterioration")
                        
                        # 优先级保护：如果已有更高风险级别，不降级
                        if risk_assessment["risk_level"] not in ["critical", "high"]:
                            risk_assessment["risk_level"] = "moderate"
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return risk_assessment
    
    def _generate_clinical_recommendations(self, result: AssessmentResult, 
                                         assessment: Dict[str, Any],
                                         risk_assessment: Dict[str, Any]) -> List[str]:
        """
        【建议生成】根据评估结果生成分层的临床建议
        
        处理流程:
        Stage 1: 基于风险级别的建议（critical/high/moderate/low）
        Stage 2: 基于临床意义的建议（severe/moderate/minimal）
        Stage 3: 基于评估类型的建议（PHQ-9/GAD-7/PSS-10 特定建议）
        Stage 4: 基于趋势的建议（恶化/改善/稳定）
        Stage 5: 默认建议（如果前面没有生成建议）
        
        建议优先级:
        1. 风险级别建议（最紧急）
        2. 临床意义建议
        3. 评估类型建议
        4. 趋势建议
        5. 默认建议
        """
        recommendations = []
        
        try:
            # ===== Stage 1: 基于风险级别的建议（最高优先级）=====
            if risk_assessment["risk_level"] == "critical":
                recommendations.append("Immediate clinical evaluation required")
                recommendations.append("Safety assessment and monitoring")
                if "suicidal_ideation" in risk_assessment["risk_factors"]:
                    recommendations.append("Crisis intervention services recommended")
            
            elif risk_assessment["risk_level"] == "high":
                # ⚠️ 高风险：紧急评估
                recommendations.append("Urgent clinical evaluation recommended")
                recommendations.append("Consider medication evaluation")
                recommendations.append("Weekly monitoring required")
            
            elif risk_assessment["risk_level"] == "moderate":
                # 中等风险：定期评估
                recommendations.append("Clinical evaluation within 1-2 weeks")
                recommendations.append("Implement coping strategies")
                recommendations.append("Bi-weekly monitoring")
            
            # ===== Stage 2: 基于临床意义的建议 =====
            # 如果评估结果具有临床意义，添加相应建议
            if assessment["is_clinically_significant"]:
                if assessment["significance_level"] == "severe":
                    # 严重变化：立即干预
                    recommendations.append("Immediate intervention recommended")
                elif assessment["significance_level"] == "moderate":
                    # 中等变化：一周内评估
                    recommendations.append("Clinical evaluation within 1 week")
                elif assessment["significance_level"] == "minimal":
                    # 最小变化：继续监测
                    recommendations.append("Monitor for continued changes")
            
            # ===== Stage 3: 基于评估类型的建议 =====
            # 根据具体的评估类型（PHQ-9/GAD-7/PSS-10）生成针对性建议
            if isinstance(result, PHQ9Result):
                # PHQ-9 特定建议：抑郁症相关
                if result.severity_level in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]:
                    recommendations.append("Consider antidepressant medication evaluation")
                    recommendations.append("Psychotherapy referral recommended")
                
                if result.total_score >= 15:
                    recommendations.append("Functional impairment likely - assess daily activities")
            
            elif isinstance(result, GAD7Result):
                # GAD-7 特定建议：焦虑症相关
                if result.severity_level in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]:
                    recommendations.append("Consider anti-anxiety medication evaluation")
                    recommendations.append("Cognitive behavioral therapy recommended")
                
                if result.total_score >= 15:
                    recommendations.append("Assess impact on work and relationships")
            
            elif isinstance(result, PSS10Result):
                # PSS-10 特定建议：压力相关
                if result.severity_level in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]:
                    recommendations.append("Stress management intervention recommended")
                    recommendations.append("Lifestyle modification counseling")
                
                if result.total_score >= 20:
                    recommendations.append("Assess coping mechanisms and support systems")
            
            # ===== Stage 4: 基于趋势的建议 =====
            # 根据症状变化趋势（恶化/改善）生成相应建议
            if assessment["trend_direction"] == "increasing":
                # 症状恶化：需要密切监测
                recommendations.append("Monitor for continued deterioration")
                
                # 如果恶化幅度 ≥ 10 分，考虑调整药物
                if assessment["change_magnitude"] >= 10:
                    recommendations.append("Consider medication adjustment")
            
            elif assessment["trend_direction"] == "decreasing":
                # 症状改善：维持当前治疗
                recommendations.append("Continue current treatment plan")
                recommendations.append("Monitor for sustained improvement")
            
            # ===== Stage 5: 默认建议 =====
            # 如果前面所有阶段都没有生成建议，添加默认建议
            if not recommendations:
                recommendations.append("Continue routine monitoring")
                recommendations.append("Maintain current treatment plan")
            
        except Exception as e:
            logger.error(f"Error generating clinical recommendations: {e}")
            recommendations.append("Clinical consultation recommended")
        
        return recommendations
    
    def _determine_monitoring_priority(self, assessment: Dict[str, Any]) -> str:
        """
        【监控优先级】根据评估结果确定监控的紧急程度
        
        优先级级别:
        - immediate: 关键风险（critical），需要立即监控
        - urgent: 高风险（high），需要紧急监控
        - elevated: 有临床意义，需要提升监控频率
        - routine: 默认，常规监控
        """
        if assessment["risk_level"] == "critical":
            # 关键风险：立即监控
            return "immediate"
        elif assessment["risk_level"] == "high":
            # 高风险：紧急监控
            return "urgent"
        elif assessment["is_clinically_significant"]:
            # 有临床意义：提升监控频率
            return "elevated"
        else:
            # 默认：常规监控
            return "routine"
    
    def analyze_longitudinal_trends(self, results: List[AssessmentResult]) -> Dict[str, Any]:
        """
        【纵向趋势分析】分析多次评估结果的长期变化趋势
        
        处理流程:
        Stage 1: 数据验证和排序
        Stage 2: 计算总体趋势（趋势方向、趋势幅度）
        Stage 3: 计算稳定性（方差分析）
        Stage 4: 检测变化点（显著变化的时间点）
        
        Args:
            results: 评估结果列表（至少需要 2 个结果）
            
        Returns:
            Dict[str, Any]: 趋势分析字典，包含趋势方向、幅度、稳定性、变化点等
        """
        try:
            # ===== Stage 1: 数据验证和排序 =====
            # 至少需要 2 个评估结果才能进行趋势分析
            if len(results) < 2:
                return {"error": "Insufficient data for trend analysis"}
            
            # 按 simulation_day 排序，确保时间顺序正确
            sorted_results = sorted(results, key=lambda x: x.simulation_day)
            
            # ===== Stage 2: 计算总体趋势 =====
            # 初始化分析字典
            analysis = {
                "trend_direction": "stable",      # 趋势方向（increasing/decreasing/stable）
                "trend_magnitude": 0.0,           # 趋势幅度（绝对值）
                "stability_score": 0.0,           # 稳定性分数（0-1，越高越稳定）
                "change_points": [],              # 变化点列表（显著变化的时间点）
                "periods_of_change": [],          # 变化期间列表（保留字段，待扩展）
                "overall_trajectory": "stable"    # 总体轨迹（improving/deteriorating/stable）
            }
            
            # Stage 2.1: 计算首尾分数变化
            first_score = sorted_results[0].total_score
            last_score = sorted_results[-1].total_score
            score_change = last_score - first_score
            
            analysis["trend_magnitude"] = abs(score_change)  # 趋势幅度（绝对值）
            
            # Stage 2.2: 判断趋势方向和总体轨迹
            if score_change > 5:
                # 分数增加 > 5 分：症状恶化
                analysis["trend_direction"] = "increasing"
                analysis["overall_trajectory"] = "deteriorating"
            elif score_change < -5:
                # 分数减少 > 5 分：症状改善
                analysis["trend_direction"] = "decreasing"
                analysis["overall_trajectory"] = "improving"
            # 否则：稳定（-5 ≤ change ≤ 5）
            
            # ===== Stage 3: 计算稳定性 =====
            # 通过计算方差的倒数来评估稳定性（方差越小，稳定性越高）
            scores = [r.total_score for r in sorted_results]
            mean_score = sum(scores) / len(scores)  # 平均分数
            
            # 计算方差
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            
            # 稳定性分数：使用 1/(1+variance) 公式，范围 [0, 1]
            # 方差为 0 → 稳定性分数为 1（完全稳定）
            # 方差越大 → 稳定性分数越接近 0（不稳定）
            analysis["stability_score"] = 1.0 / (1.0 + variance)
            
            # ===== Stage 4: 检测变化点 =====
            # 检测相邻评估之间是否有显著变化（变化幅度 ≥ 5 分）
            for i in range(1, len(sorted_results)):
                change = sorted_results[i].total_score - sorted_results[i-1].total_score
                
                if abs(change) >= 5:  # 显著变化阈值
                    # 记录变化点信息
                    analysis["change_points"].append({
                        "day": sorted_results[i].simulation_day,        # 变化发生的日期
                        "change_magnitude": change,                     # 变化幅度（可正可负）
                        "previous_score": sorted_results[i-1].total_score,  # 变化前分数
                        "current_score": sorted_results[i].total_score      # 变化后分数
                    })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing longitudinal trends: {e}")
            return {"error": str(e)}
    
    def generate_clinical_summary(self, session: AssessmentSession) -> Dict[str, Any]:
        """
        【临床摘要生成】为评估会话生成综合临床摘要
        
        处理流程:
        Stage 1: 初始化摘要字典
        Stage 2: 分析每个评估结果（PHQ-9/GAD-7/PSS-10）
        Stage 3: 生成整体建议和监控计划
        
        Args:
            session: 评估会话对象（包含多个评估结果）
            
        Returns:
            Dict[str, Any]: 临床摘要字典，包含整体严重度、风险、建议等
        """
        try:
            # ===== Stage 1: 初始化摘要字典 =====
            summary = {
                "session_id": session.session_id,
                "persona_id": session.persona_id,
                "simulation_day": session.simulation_day,
                "overall_severity": session.get_overall_severity().value,  # 整体严重度
                "composite_scores": session.get_composite_score(),         # 综合分数
                "clinical_interpretations": {},                             # 各量表解释（待填充）
                "risk_assessment": {
                    "overall_risk": "low",      # 整体风险（默认低风险）
                    "risk_factors": [],         # 风险因素列表（待填充）
                    "critical_alerts": []       # 关键警报列表（待填充）
                },
                "recommendations": [],          # 建议列表（待填充）
                "monitoring_plan": "routine"    # 监控计划（默认常规）
            }
            
            # ===== Stage 2: 分析每个评估结果 =====
            # 遍历会话中的所有评估结果，提取关键信息
            for result in session.get_all_results():
                if isinstance(result, PHQ9Result):
                    summary["clinical_interpretations"]["depression"] = {
                        "score": result.total_score,
                        "severity": result.severity_level.value,
                        "suicidal_risk": "high" if result.suicidal_ideation_score >= 2 else "low"
                    }
                    
                    if result.suicidal_ideation_score >= 2:
                        summary["risk_assessment"]["critical_alerts"].append("Suicidal ideation present")
                        summary["risk_assessment"]["overall_risk"] = "critical"
                
                elif isinstance(result, GAD7Result):
                    summary["clinical_interpretations"]["anxiety"] = {
                        "score": result.total_score,
                        "severity": result.severity_level.value
                    }
                
                elif isinstance(result, PSS10Result):
                    summary["clinical_interpretations"]["stress"] = {
                        "score": result.total_score,
                        "severity": result.severity_level.value
                    }
            
            # Generate overall recommendations
            if summary["overall_severity"] in ["moderate", "severe"]:
                summary["recommendations"].append("Comprehensive clinical evaluation recommended")
                summary["monitoring_plan"] = "elevated"
            
            if summary["risk_assessment"]["overall_risk"] == "critical":
                summary["recommendations"].insert(0, "Immediate clinical intervention required")
                summary["monitoring_plan"] = "immediate"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating clinical summary: {e}")
            return {"error": str(e)}
    
    def interpret_phq9_result(self, result: PHQ9Result) -> Dict[str, Any]:
        """
        【简化版 PHQ-9 解释】提供 PHQ-9 评估结果的简化临床解释
        
        注意: 这是简化版本，主要用于快速解释。
        完整评估请使用 assess_clinical_significance() 方法。
        
        处理流程:
        Stage 1: 初始化解释字典
        Stage 2: 基于严重度的解释映射
        Stage 3: 自杀意念检测（关键风险）
        Stage 4: 附加风险因素检测
        
        Args:
            result: PHQ9Result 对象
            
        Returns:
            Dict[str, Any]: 简化临床解释字典
        """
        # ===== Stage 1: 初始化解释字典 =====
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",          # 待填充
            "recommendations": [],           # 待填充
            "risk_factors": [],              # 待填充
            "suicidal_risk": "low"          # 默认低风险
        }
        
        # ===== Stage 2: 基于严重度的解释映射 =====
        # 根据严重度等级生成对应的临床含义和建议
        if result.severity_level == SeverityLevel.MINIMAL:
            interpretation["clinical_meaning"] = "Minimal depressive symptoms"
            interpretation["recommendations"] = ["Continue monitoring", "Maintain current routine"]
        elif result.severity_level == SeverityLevel.MILD:
            interpretation["clinical_meaning"] = "Mild depressive symptoms"
            interpretation["recommendations"] = ["Consider lifestyle changes", "Monitor for worsening"]
        elif result.severity_level == SeverityLevel.MODERATE:
            interpretation["clinical_meaning"] = "Moderate depressive symptoms"
            interpretation["recommendations"] = ["Consider professional evaluation", "Implement coping strategies"]
        else:  # Severe
            interpretation["clinical_meaning"] = "Severe depressive symptoms"
            interpretation["recommendations"] = ["Immediate professional evaluation recommended", "Safety assessment needed"]
        
        # ===== Stage 3: 自杀意念检测（关键风险）=====
        # ⚠️ 安全优先：即使总分不高，Item 9 ≥ 2 也需要立即关注
        if result.suicidal_ideation_score >= 2:
            interpretation["suicidal_risk"] = "high"  # ⚠️ 风险升级
            interpretation["risk_factors"].append("Suicidal ideation present")
            # 将安全评估建议插入到首位（最高优先级）
            interpretation["recommendations"].insert(0, "Immediate safety assessment required")
        
        # ===== Stage 4: 附加风险因素检测 =====
        # 检测高严重度症状（总分 ≥ 20）
        if result.total_score >= 20:
            interpretation["risk_factors"].append("High depression severity")
        
        return interpretation
    
    def interpret_gad7_result(self, result: GAD7Result) -> Dict[str, Any]:
        """
        【简化版 GAD-7 解释】提供 GAD-7 评估结果的简化临床解释
        
        处理流程与 interpret_phq9_result 类似，但不包含自杀意念检测
        """
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",
            "recommendations": [],
            "risk_factors": []
        }
        
        # ===== Stage 2: 基于严重度的解释映射 =====
        if result.severity_level == SeverityLevel.MINIMAL:
            interpretation["clinical_meaning"] = "Minimal anxiety symptoms"
            interpretation["recommendations"] = ["Continue monitoring", "Maintain current routine"]
        elif result.severity_level == SeverityLevel.MILD:
            interpretation["clinical_meaning"] = "Mild anxiety symptoms"
            interpretation["recommendations"] = ["Consider stress management", "Monitor for worsening"]
        elif result.severity_level == SeverityLevel.MODERATE:
            interpretation["clinical_meaning"] = "Moderate anxiety symptoms"
            interpretation["recommendations"] = ["Consider professional evaluation", "Implement relaxation techniques"]
        else:  # Severe
            interpretation["clinical_meaning"] = "Severe anxiety symptoms"
            interpretation["recommendations"] = ["Immediate professional evaluation recommended", "Consider medication evaluation"]
        
        # ===== Stage 4: 附加风险因素检测 =====
        if result.total_score >= 20:
            interpretation["risk_factors"].append("High anxiety severity")
        
        return interpretation
    
    def interpret_pss10_result(self, result: PSS10Result) -> Dict[str, Any]:
        """
        【简化版 PSS-10 解释】提供 PSS-10 评估结果的简化临床解释
        
        处理流程与 interpret_gad7_result 类似，但使用 PSS-10 特定的阈值
        """
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",
            "recommendations": [],
            "risk_factors": []
        }
        
        # ===== Stage 2: 基于严重度的解释映射 =====
        if result.severity_level == SeverityLevel.MINIMAL:
            interpretation["clinical_meaning"] = "Minimal perceived stress"
            interpretation["recommendations"] = ["Continue current stress management", "Maintain healthy routines"]
        elif result.severity_level == SeverityLevel.MILD:
            interpretation["clinical_meaning"] = "Mild perceived stress"
            interpretation["recommendations"] = ["Consider stress management techniques", "Monitor stress levels"]
        elif result.severity_level == SeverityLevel.MODERATE:
            interpretation["clinical_meaning"] = "Moderate perceived stress"
            interpretation["recommendations"] = ["Implement stress reduction strategies", "Consider professional support"]
        else:  # Severe
            interpretation["clinical_meaning"] = "Severe perceived stress"
            interpretation["recommendations"] = ["Immediate stress management intervention", "Professional evaluation recommended"]
        
        # Additional risk factors
        if result.total_score >= 25:
            interpretation["risk_factors"].append("High stress levels")
        
        return interpretation


# Global clinical interpreter instance
clinical_interpreter = ClinicalInterpreter() 