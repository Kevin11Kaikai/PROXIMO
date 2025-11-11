"""
PROXIMO Assessment API - Simplified interface for clinical assessments.

This module provides a simple, clean API for conducting psychiatric assessments:
    proximo.assessment.assess(scale, responses)

It encapsulates the complexity of:
- psychiatric_scales.py (validation and scoring)
- clinical_interpreter.py (clinical interpretation and risk assessment)
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

from src.assessment.psychiatric_scales import AssessmentOrchestrator
from src.models.assessment import (
    PHQ9Result, GAD7Result, PSS10Result, SeverityLevel
)
from src.models.persona import Persona, PersonaBaseline, PersonaState


logger = logging.getLogger(__name__)


# 全局 orchestrator 实例（单例模式，提高性能）
_orchestrator = None


def _get_orchestrator() -> AssessmentOrchestrator:
    """获取全局 orchestrator 实例（单例模式）"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AssessmentOrchestrator()
    return _orchestrator


def _create_minimal_persona(persona_id: Optional[str] = None) -> Persona:
    """
    创建一个最小的 Persona 对象用于评估
    
    注意: 这个 Persona 只包含评估所需的最小信息，
    不包含完整的个性特征和记忆。
    """
    persona_id = persona_id or f"assess_{uuid.uuid4().hex[:8]}"
    
    # 创建最小基线配置
    baseline = PersonaBaseline(
        name="Assessment User",
        age=30,
        occupation="Unknown",
        background="Assessment-only persona",
        openness=0.5,
        conscientiousness=0.5,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.5,
        baseline_phq9=0.0,
        baseline_gad7=0.0,
        baseline_pss10=0.0
    )
    
    # 创建最小状态配置
    state = PersonaState(
        persona_id=persona_id,
        simulation_day=0,
        last_assessment_day=-1
    )
    
    return Persona(baseline=baseline, state=state)


async def assess(
    scale: Literal["phq9", "gad7", "pss10"],
    responses: List[str],
    persona_id: Optional[str] = None,
    simulation_day: int = 0
) -> Dict[str, Any]:
    """
    PROXIMO Assessment API - 简洁的评估接口
    
    这个函数封装了完整的评估流程：
    1. 输入验证与标准化 (psychiatric_scales.py)
    2. 分数计算与结果生成 (AssessmentOrchestrator)
    3. 临床解释与风险评估 (clinical_interpreter.py)
    
    Args:
        scale: 量表类型 ("phq9", "gad7", "pss10")
        responses: 原始回答列表
            - PHQ-9: 需要 9 个回答
            - GAD-7: 需要 7 个回答
            - PSS-10: 需要 10 个回答
        persona_id: 可选的 persona ID（用于结果标识）
        simulation_day: 可选的模拟天数（默认为 0）
    
    Returns:
        Dict[str, Any]: 完整的评估结果，包含：
            - total_score: 总分
            - severity_level: 严重度级别 (minimal/mild/moderate/severe)
            - parsed_scores: 每题分数列表
            - clinical_interpretation: 临床解释（包含 recommendations, risk_factors）
            - risk_level: 风险级别 (critical/high/moderate/low) - 如果使用完整解释器
            - suicidal_risk: 自杀意念风险 (仅 PHQ-9)
            - flags: 风险标志（suicidal_ideation, severe_symptoms 等）
    
    Example:
        >>> import asyncio
        >>> from proximo.assessment import assess
        >>> 
        >>> responses = [
        ...     "0", "not at all", "several days", "2", 
        ...     "2", "1", "1", "2", "2"  # PHQ-9 需要 9 个回答
        ... ]
        >>> result = asyncio.run(assess("phq9", responses))
        >>> print(result["total_score"])  # 总分
        >>> print(result["severity_level"])  # 严重度
        >>> print(result["clinical_interpretation"]["recommendations"])  # 建议
        >>> print(result["flags"]["suicidal_ideation"])  # 自杀意念标志
    """
    try:
        # ===== 参数验证 =====
        valid_scales = ["phq9", "gad7", "pss10"]
        if scale not in valid_scales:
            raise ValueError(f"Invalid scale: {scale}. Must be one of {valid_scales}")
        
        # 验证回答数量
        expected_counts = {
            "phq9": 9,
            "gad7": 7,
            "pss10": 10
        }
        expected_count = expected_counts[scale]
        if len(responses) != expected_count:
            raise ValueError(
                f"{scale.upper()} requires {expected_count} responses, "
                f"got {len(responses)}"
            )
        
        # ===== 创建最小 Persona 对象 =====
        persona = _create_minimal_persona(persona_id)
        persona.state.simulation_day = simulation_day
        
        # ===== 执行评估 =====
        orchestrator = _get_orchestrator()
        
        if scale == "phq9":
            result = await orchestrator.conduct_phq9_assessment(persona, responses)
        elif scale == "gad7":
            result = await orchestrator.conduct_gad7_assessment(persona, responses)
        elif scale == "pss10":
            result = await orchestrator.conduct_pss10_assessment(persona, responses)
        else:
            raise ValueError(f"Unsupported scale: {scale}")
        
        if result is None:
            return {
                "success": False,
                "error": "Assessment failed - validation error or insufficient data"
            }
        
        # ===== 提取关键信息 =====
        assessment_result = {
            "success": True,
            "scale": scale,
            "total_score": result.total_score,
            "severity_level": result.severity_level.value,  # 转为字符串
            "parsed_scores": result.parsed_scores,
            "raw_responses": result.raw_responses,
        }
        
        # ===== 添加临床解释 =====
        if result.clinical_interpretation:
            assessment_result["clinical_interpretation"] = result.clinical_interpretation
        else:
            # 如果没有临床解释，创建一个基本的
            assessment_result["clinical_interpretation"] = {
                "severity_level": result.severity_level.value,
                "total_score": result.total_score,
                "recommendations": [],
                "risk_factors": []
            }
        
        # ===== 提取风险标志（flags）=====
        flags = {}
        
        # PHQ-9 特殊处理
        if isinstance(result, PHQ9Result):
            flags["suicidal_ideation"] = result.has_suicidal_ideation()
            flags["suicidal_ideation_score"] = result.suicidal_ideation_score
            assessment_result["suicidal_risk"] = (
                "high" if result.has_suicidal_ideation() else "low"
            )
        
        # 严重症状标志
        if scale == "phq9" or scale == "gad7":
            flags["severe_symptoms"] = result.total_score >= 20
        elif scale == "pss10":
            flags["severe_symptoms"] = result.total_score >= 25
        
        assessment_result["flags"] = flags
        
        # ===== 添加风险级别（从临床解释中提取）=====
        if result.clinical_interpretation:
            # 如果有完整的临床解释，尝试提取风险级别
            interpretation = result.clinical_interpretation
            if "suicidal_risk" in interpretation:
                assessment_result["risk_level"] = (
                    "critical" if interpretation["suicidal_risk"] == "high" else "low"
                )
            elif result.total_score >= 20:
                assessment_result["risk_level"] = "high"
            elif result.total_score >= 10:
                assessment_result["risk_level"] = "moderate"
            else:
                assessment_result["risk_level"] = "low"
        
        return assessment_result
        
    except ValueError as e:
        logger.error(f"Validation error in assess(): {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error in assess(): {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Assessment failed: {str(e)}"
        }


def assess_sync(
    scale: Literal["phq9", "gad7", "pss10"],
    responses: List[str],
    persona_id: Optional[str] = None,
    simulation_day: int = 0
) -> Dict[str, Any]:
    """
    同步版本的 assess() 函数（内部使用 asyncio 运行）
    
    注意: 虽然这是同步接口，但内部仍使用异步实现。
    如果需要高性能，建议使用异步版本 assess()。
    
    如果已经在异步环境中运行，请直接使用 assess() 函数。
    """
    import asyncio
    
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_running_loop()
        # 如果已经有运行中的事件循环，抛出错误
        raise RuntimeError(
            "Cannot use assess_sync() in an async context. "
            "Please use await assess() instead."
        )
    except RuntimeError as e:
        # 如果没有运行中的事件循环，创建新的
        if "Cannot use assess_sync()" in str(e):
            raise e
        # 创建新的事件循环
        return asyncio.run(assess(scale, responses, persona_id, simulation_day))


# ===== 便捷函数 =====

async def assess_phq9(responses: List[str], **kwargs) -> Dict[str, Any]:
    """便捷函数：评估 PHQ-9"""
    return await assess("phq9", responses, **kwargs)


async def assess_gad7(responses: List[str], **kwargs) -> Dict[str, Any]:
    """便捷函数：评估 GAD-7"""
    return await assess("gad7", responses, **kwargs)


async def assess_pss10(responses: List[str], **kwargs) -> Dict[str, Any]:
    """便捷函数：评估 PSS-10"""
    return await assess("pss10", responses, **kwargs)

