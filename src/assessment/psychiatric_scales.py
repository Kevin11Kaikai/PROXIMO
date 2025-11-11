"""
Enhanced psychiatric scale implementations with clinical validation.

=== 三阶段处理流程 ===
本文件实现了从原始回答到临床解释的完整评估流程，分为三个阶段：

【Stage 1: 输入验证与标准化 (PsychiatricScaleValidator)】
    输入: 原始文本回答（如 "0", "not at all", "several days"）
    过程: 文本清理 → 数字提取/语义映射 → 校验
    输出: 标准化分数 (0-3 或 0-4)

【Stage 2: 评估编排与结果生成 (AssessmentOrchestrator)】
    输入: Persona 对象 + 回答列表
    过程: 批量校验 → 总分计算 → 严重度分级 → 特殊字段提取 → 结果对象构建
    输出: 完整评估结果对象 (PHQ9Result/GAD7Result/PSS10Result)

【Stage 3: 临床解释与风险评估 (ClinicalInterpreter)】
    输入: 评估结果对象
    过程: 严重度解释映射 → 关键风险检测 → 建议生成
    输出: 临床解释字典 (包含推荐、风险因素等)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from src.models.assessment import (
    PHQ9Result, GAD7Result, PSS10Result, SeverityLevel
)
from src.models.persona import Persona


logger = logging.getLogger(__name__)


class PsychiatricScaleValidator:
    """
    【Stage 1: 输入验证与标准化】
    
    职责: 将多样化的原始文本回答转换为标准化的数字分数
    
    核心功能:
    1. 文本清理与预处理（去除空格、统一大小写）
    2. 数字提取（优先策略：直接从文本中提取 0-3 或 0-4）
    3. 语义映射（备选策略：将自然语言映射到分数）
    4. 容错处理（校验失败返回 None）
    
    输出格式: Tuple[bool, Optional[int]]
        - (True, 0-3): 校验成功，返回分数
        - (False, None): 校验失败
    """
    
    # 临床阈值和验证规则（用于后续阶段的严重度分级）
    PHQ9_THRESHOLDS = {
        "minimal": 5,
        "mild": 10, 
        "moderate": 15,
        "severe": 20
    }
    
    GAD7_THRESHOLDS = {
        "minimal": 5,
        "mild": 10,
        "moderate": 15, 
        "severe": 20
    }
    
    PSS10_THRESHOLDS = {
        "minimal": 13,
        "mild": 16,
        "moderate": 19,
        "severe": 22
    }
    
    # PSS-10 反向计分项（在 Stage 2 中使用）
    # 这些题目的高分表示低压力，需要反向计分以确保方向一致
    PSS10_REVERSE_ITEMS = [4, 5, 7, 8]  # 1-indexed
    
    @classmethod
    def validate_phq9_response(cls, response: str, question_index: int) -> Tuple[bool, Optional[int]]:
        """
        【Stage 1】校验单个 PHQ-9 回答并返回分数
        
        处理流程:
        1. 文本清理: 去除空格、转为小写
        2. 数字提取: 使用正则表达式提取 0-3 范围内的数字（优先策略）
        3. 语义映射: 如果没有数字，则匹配文本关键词（备选策略）
        4. 异常处理: 校验失败返回 (False, None)
        
        Args:
            response: 原始回答文本（如 "0", "not at all", "several days"）
            question_index: 题目序号（0-indexed，用于日志记录）
            
        Returns:
            Tuple[bool, Optional[int]]: (校验是否成功, 分数值)
        """
        try:
            # ===== Stage 1.1: 文本清理与预处理 =====
            response = response.strip().lower()  # 去除空格，统一大小写
            
            # ===== Stage 1.2: 数字提取（优先策略）=====
            # 使用正则表达式提取完整单词边界内的数字，确保只匹配 0-3
            import re
            numbers = re.findall(r'\b[0-3]\b', response)
            
            if numbers:
                score = int(numbers[0])
                if 0 <= score <= 3:
                    return True, score  # 成功提取数字并验证范围
            
            # ===== Stage 1.3: 文本语义映射（备选策略）=====
            # 将自然语言关键词映射到分数
            # 支持同义词: "never" = "not at all" = "0"
            score_map = {
                "not at all": 0, "never": 0, "0": 0,
                "several days": 1, "sometimes": 1, "1": 1,
                "more than half the days": 2, "often": 2, "2": 2,
                "nearly every day": 3, "always": 3, "3": 3
            }
            
            # 子串匹配：支持 "sometimes I feel..." 这类包含关键词的长文本
            for text, score in score_map.items():
                if text in response:
                    return True, score
            
            # ===== Stage 1.4: 校验失败 =====
            return False, None
            
        except Exception as e:
            # 容错处理：记录错误但不中断程序
            logger.error(f"Error validating PHQ-9 response: {e}")
            return False, None
    
    @classmethod
    def validate_gad7_response(cls, response: str, question_index: int) -> Tuple[bool, Optional[int]]:
        """
        【Stage 1】校验单个 GAD-7 回答并返回分数
        
        处理流程与 validate_phq9_response 相同，但使用 GAD-7 的语义映射表
        """
        try:
            # ===== Stage 1.1: 文本清理 =====
            response = response.strip().lower()
            
            # ===== Stage 1.2: 数字提取 =====
            import re
            numbers = re.findall(r'\b[0-3]\b', response)
            
            if numbers:
                score = int(numbers[0])
                if 0 <= score <= 3:
                    return True, score
            
            # ===== Stage 1.3: 文本语义映射 =====
            score_map = {
                "not at all": 0, "never": 0, "0": 0,
                "several days": 1, "sometimes": 1, "1": 1,
                "more than half the days": 2, "often": 2, "2": 2,
                "nearly every day": 3, "always": 3, "3": 3
            }
            
            for text, score in score_map.items():
                if text in response:
                    return True, score
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error validating GAD-7 response: {e}")
            return False, None
    
    @classmethod
    def validate_pss10_response(cls, response: str, question_index: int) -> Tuple[bool, Optional[int]]:
        """
        【Stage 1】校验单个 PSS-10 回答并返回分数
        
        注意: PSS-10 是 5 级量表（0-4），而 PHQ-9/GAD-7 是 4 级量表（0-3）
        """
        try:
            # ===== Stage 1.1: 文本清理 =====
            response = response.strip().lower()
            
            # ===== Stage 1.2: 数字提取（PSS-10 范围是 0-4）=====
            import re
            numbers = re.findall(r'\b[0-4]\b', response)
            
            if numbers:
                score = int(numbers[0])
                if 0 <= score <= 4:
                    return True, score
            
            # ===== Stage 1.3: 文本语义映射（5 级量表）=====
            score_map = {
                "never": 0, "0": 0,
                "almost never": 1, "1": 1,
                "sometimes": 2, "2": 2,
                "fairly often": 3, "3": 3,
                "very often": 4, "4": 4
            }
            
            for text, score in score_map.items():
                if text in response:
                    return True, score
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error validating PSS-10 response: {e}")
            return False, None
    
    @classmethod
    def calculate_pss10_score(cls, raw_scores: List[int]) -> int:
        """
        【Stage 2 辅助方法】计算 PSS-10 总分（含反向计分）
        
        为什么需要反向计分？
        - PSS-10 的部分题目是正向表述（如"我能掌控我的生活"）
        - 这些题目的高分应该表示低压力，而不是高压力
        - 反向计分确保所有题目方向一致：高分 = 高压力
        
        反向计分规则:
        - 题目 4, 5, 7, 8（索引 3, 4, 6, 7）需要反向计分
        - 反向公式: 反向分 = 4 - 原分
        - 示例: 原分 0 → 反向 4, 原分 4 → 反向 0
        
        Args:
            raw_scores: 10 个题目的原始分数列表
            
        Returns:
            int: 总分（0-40）
        """
        if len(raw_scores) != 10:
            raise ValueError(f"PSS-10 requires exactly 10 scores, got {len(raw_scores)}")
        
        total_score = 0
        for i, score in enumerate(raw_scores):
            # 对反向计分项（索引 3, 4, 6, 7）应用反向计分
            if i in [3, 4, 6, 7]:  # 对应题目 4, 5, 7, 8
                total_score += (4 - score)  # 反向: 0->4, 1->3, 2->2, 3->1, 4->0
            else:
                total_score += score
        
        return total_score


class ClinicalInterpreter:
    """
    【Stage 3: 临床解释与风险评估】
    
    职责: 将评估结果对象转换为可操作的临床解释和风险评估
    
    核心功能:
    1. 严重度解释映射: 根据严重度等级生成临床含义和建议
    2. 关键风险检测: 检测自杀意念（PHQ-9 Item 9 ≥ 2）
    3. 附加风险因素: 检测高严重度症状（总分阈值）
    4. 建议生成: 根据风险级别提供渐进式建议
    
    输出格式: Dict[str, Any]
        包含: severity_level, total_score, clinical_meaning, 
              recommendations, risk_factors, suicidal_risk (仅 PHQ-9)
    """
    
    @classmethod
    def interpret_phq9_result(cls, result: PHQ9Result) -> Dict[str, Any]:
        """
        【Stage 3】生成 PHQ-9 评估结果的临床解释
        
        处理流程:
        1. 初始化解释字典
        2. 根据严重度等级映射临床含义和建议
        3. 检测自杀意念（Item 9 ≥ 2）- 关键风险！
        4. 检测高严重度症状（总分 ≥ 20）
        
        Args:
            result: PHQ9Result 对象（包含总分、严重度、自杀意念分数等）
            
        Returns:
            Dict[str, Any]: 临床解释字典
        """
        # ===== Stage 3.1: 基础解释生成 =====
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",
            "recommendations": [],
            "risk_factors": [],
            "suicidal_risk": "low"  # 默认为低风险
        }
        
        # ===== Stage 3.2: 严重度解释映射 =====
        # 根据严重度等级生成渐进式建议（严重度越高，建议越紧急）
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
        
        # ===== Stage 3.3: 关键风险检测 - 自杀意念 =====
        # ⚠️ 安全优先：即使总分不高，Item 9 ≥ 2 也需要立即关注
        # Item 9 分数含义:
        # - 0分: "完全没有" 自杀想法
        # - 1分: "几天" 有自杀想法 → 需要关注
        # - 2分: "超过一半天" 有自杀想法 → 高风险 ⚠️
        # - 3分: "几乎每天" 有自杀想法 → 极高风险 ⚠️
        if result.suicidal_ideation_score >= 2:
            interpretation["suicidal_risk"] = "high"
            interpretation["risk_factors"].append("Suicidal ideation present")
            # 将安全评估建议插入到首位（最高优先级）
            interpretation["recommendations"].insert(0, "Immediate safety assessment required")
        
        # ===== Stage 3.4: 附加风险因素检测 =====
        # 检测高严重度症状（总分 ≥ 20）
        if result.total_score >= 20:
            interpretation["risk_factors"].append("High depression severity")
        
        return interpretation
    
    @classmethod
    def interpret_gad7_result(cls, result: GAD7Result) -> Dict[str, Any]:
        """
        【Stage 3】生成 GAD-7 评估结果的临床解释
        
        处理流程与 interpret_phq9_result 类似，但不包含自杀意念检测
        """
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",
            "recommendations": [],
            "risk_factors": []
        }
        
        # ===== Stage 3.2: 严重度解释映射 =====
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
        
        # ===== Stage 3.4: 附加风险因素检测 =====
        if result.total_score >= 20:
            interpretation["risk_factors"].append("High anxiety severity")
        
        return interpretation
    
    @classmethod
    def interpret_pss10_result(cls, result: PSS10Result) -> Dict[str, Any]:
        """
        【Stage 3】生成 PSS-10 评估结果的临床解释
        
        处理流程与 interpret_gad7_result 类似，但使用 PSS-10 特定的阈值
        """
        interpretation = {
            "severity_level": result.severity_level.value,
            "total_score": result.total_score,
            "clinical_meaning": "",
            "recommendations": [],
            "risk_factors": []
        }
        
        # ===== Stage 3.2: 严重度解释映射 =====
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
        
        # ===== Stage 3.4: 附加风险因素检测 =====
        # PSS-10 的高风险阈值是 25（而非 20）
        if result.total_score >= 25:
            interpretation["risk_factors"].append("High stress levels")
        
        return interpretation


class AssessmentOrchestrator:
    """
    【Stage 2: 评估编排与结果生成】
    
    职责: 协调 Stage 1（校验）和 Stage 3（解释），生成完整的评估结果
    
    核心功能:
    1. 批量校验: 调用 Stage 1 对所有回答进行校验
    2. 总分计算: 累加所有分数（PSS-10 需反向计分）
    3. 严重度分级: 根据总分映射严重度等级
    4. 特殊字段提取: 提取关键字段（如 PHQ-9 的 Item 9 自杀意念）
    5. 结果对象构建: 创建完整的评估结果对象
    6. 临床解释附加: 调用 Stage 3 生成临床解释
    
    依赖:
    - self.validator: PsychiatricScaleValidator (Stage 1)
    - self.interpreter: ClinicalInterpreter (Stage 3)
    """
    
    def __init__(self):
        """初始化评估编排器，创建 Stage 1 和 Stage 3 的实例"""
        self.validator = PsychiatricScaleValidator()  # Stage 1: 校验器
        self.interpreter = ClinicalInterpreter()      # Stage 3: 解释器
        
        # 评估时间表（用于调度功能）
        self.assessment_schedules = {
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30
        }
    
    async def conduct_phq9_assessment(self, persona: Persona, 
                                    responses: List[str]) -> Optional[PHQ9Result]:
        """
        【Stage 2】执行完整的 PHQ-9 评估流程
        
        端到端流程:
        1. Stage 1: 批量校验所有回答 → 得到标准化分数列表
        2. Stage 2: 计算总分、严重度分级、提取特殊字段
        3. Stage 2: 构建结果对象
        4. Stage 3: 生成临床解释并附加到结果对象
        
        Args:
            persona: Persona 对象（包含身份、时间等信息）
            responses: 9 个原始回答文本列表
            
        Returns:
            Optional[PHQ9Result]: 完整的评估结果对象，或 None（如果校验失败）
        """
        try:
            # ===== Stage 2.1: 批量校验与分数收集 =====
            # 调用 Stage 1 对每个回答进行校验
            validated_scores = []
            for i, response in enumerate(responses):
                is_valid, score = self.validator.validate_phq9_response(response, i)
                if is_valid and score is not None:
                    validated_scores.append(score)
                else:
                    # 容错处理：无效回答使用保守值 0 分
                    logger.warning(f"Invalid PHQ-9 response {i+1}: {response}")
                    validated_scores.append(0)  # 保守回退策略
            
            # ===== Stage 2.2: 回答数量验证 =====
            # PHQ-9 必须包含 9 个回答，不完整则返回 None
            if len(validated_scores) != 9:
                logger.error(f"PHQ-9 requires 9 responses, got {len(validated_scores)}")
                return None
            
            # ===== Stage 2.3: 总分计算 =====
            # PHQ-9 是简单累加，范围 0-27
            total_score = sum(validated_scores)
            
            # ===== Stage 2.4: 严重度分级 =====
            # 根据总分映射严重度等级（MINIMAL/MILD/MODERATE/SEVERE）
            severity_level = PHQ9Result.calculate_severity(total_score)
            
            # ===== Stage 2.5: 特殊字段提取 =====
            # 提取第 9 题（自杀意念）分数 - 关键风险因子
            # 索引 8 = 第 9 题（0-indexed）
            suicidal_ideation_score = validated_scores[8]
            
            # ===== Stage 2.6: 结果对象构建 =====
            # 创建完整的 PHQ9Result 对象，包含所有评估信息
            result = PHQ9Result(
                assessment_id=f"{persona.state.persona_id}_phq9_{persona.state.simulation_day}",
                persona_id=persona.state.persona_id,
                assessment_type="phq9",
                simulation_day=persona.state.simulation_day,
                raw_responses=responses,           # 保留原始输入（可追溯）
                parsed_scores=validated_scores,    # 标准化分数
                total_score=total_score,           # 总分
                severity_level=severity_level,     # 严重度等级
                suicidal_ideation_score=suicidal_ideation_score,  # 特殊字段
                depression_severity=severity_level
            )
            
            # ===== Stage 2.7: 临床解释附加 =====
            # 调用 Stage 3 生成临床解释并附加到结果对象
            result.clinical_interpretation = self.interpreter.interpret_phq9_result(result)
            
            logger.info(f"Completed PHQ-9 assessment for {persona.baseline.name}: {total_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error conducting PHQ-9 assessment: {e}")
            return None
    
    async def conduct_gad7_assessment(self, persona: Persona, 
                                    responses: List[str]) -> Optional[GAD7Result]:
        """
        【Stage 2】执行完整的 GAD-7 评估流程
        
        处理流程与 conduct_phq9_assessment 类似，但：
        - GAD-7 需要 7 个回答（而非 9 个）
        - 不包含自杀意念检测（无特殊字段提取）
        """
        try:
            # ===== Stage 2.1: 批量校验与分数收集 =====
            validated_scores = []
            for i, response in enumerate(responses):
                is_valid, score = self.validator.validate_gad7_response(response, i)
                if is_valid and score is not None:
                    validated_scores.append(score)
                else:
                    logger.warning(f"Invalid GAD-7 response {i+1}: {response}")
                    validated_scores.append(0)  # 保守回退策略
            
            # ===== Stage 2.2: 回答数量验证 =====
            if len(validated_scores) != 7:  # GAD-7 需要 7 个回答
                logger.error(f"GAD-7 requires 7 responses, got {len(validated_scores)}")
                return None
            
            # ===== Stage 2.3: 总分计算 =====
            total_score = sum(validated_scores)  # GAD-7 范围 0-21
            
            # ===== Stage 2.4: 严重度分级 =====
            severity_level = GAD7Result.calculate_severity(total_score)
            
            # ===== Stage 2.6: 结果对象构建 =====
            # GAD-7 无特殊字段（如自杀意念）
            result = GAD7Result(
                assessment_id=f"{persona.state.persona_id}_gad7_{persona.state.simulation_day}",
                persona_id=persona.state.persona_id,
                assessment_type="gad7",
                simulation_day=persona.state.simulation_day,
                raw_responses=responses,
                parsed_scores=validated_scores,
                total_score=total_score,
                severity_level=severity_level,
                anxiety_severity=severity_level
            )
            
            # ===== Stage 2.7: 临床解释附加 =====
            result.clinical_interpretation = self.interpreter.interpret_gad7_result(result)
            
            logger.info(f"Completed GAD-7 assessment for {persona.baseline.name}: {total_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error conducting GAD-7 assessment: {e}")
            return None
    
    async def conduct_pss10_assessment(self, persona: Persona, 
                                     responses: List[str]) -> Optional[PSS10Result]:
        """
        【Stage 2】执行完整的 PSS-10 评估流程
        
        处理流程的特殊之处：
        - PSS-10 需要 10 个回答
        - 包含反向计分逻辑（部分题目需要反向计分）
        - 无效回答使用中间值 2 分（而非 0 分）
        """
        try:
            # ===== Stage 2.1: 批量校验与分数收集 =====
            validated_scores = []
            for i, response in enumerate(responses):
                is_valid, score = self.validator.validate_pss10_response(response, i)
                if is_valid and score is not None:
                    validated_scores.append(score)
                else:
                    logger.warning(f"Invalid PSS-10 response {i+1}: {response}")
                    # PSS-10 使用中间值 2 分作为保守回退（因为 PSS-10 是 5 级量表）
                    validated_scores.append(2)
            
            # ===== Stage 2.2: 回答数量验证 =====
            if len(validated_scores) != 10:  # PSS-10 需要 10 个回答
                logger.error(f"PSS-10 requires 10 responses, got {len(validated_scores)}")
                return None
            
            # ===== Stage 2.3: 总分计算（含反向计分）=====
            # PSS-10 需要调用特殊的反向计分方法
            total_score = self.validator.calculate_pss10_score(validated_scores)  # 范围 0-40
            
            # ===== Stage 2.4: 严重度分级 =====
            severity_level = PSS10Result.calculate_severity(total_score)
            
            # ===== Stage 2.6: 结果对象构建 =====
            result = PSS10Result(
                assessment_id=f"{persona.state.persona_id}_pss10_{persona.state.simulation_day}",
                persona_id=persona.state.persona_id,
                assessment_type="pss10",
                simulation_day=persona.state.simulation_day,
                raw_responses=responses,
                parsed_scores=validated_scores,
                total_score=total_score,
                severity_level=severity_level,
                stress_severity=severity_level
            )
            
            # ===== Stage 2.7: 临床解释附加 =====
            result.clinical_interpretation = self.interpreter.interpret_pss10_result(result)
            
            logger.info(f"Completed PSS-10 assessment for {persona.baseline.name}: {total_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error conducting PSS-10 assessment: {e}")
            return None
    
    def is_assessment_due(self, persona: Persona, schedule: str = "weekly") -> bool:
        """检查是否到了评估时间（基于时间表）"""
        interval_days = self.assessment_schedules.get(schedule, 7)
        days_since_last = persona.state.simulation_day - persona.state.last_assessment_day
        return days_since_last >= interval_days
    
    def get_next_assessment_day(self, persona: Persona, schedule: str = "weekly") -> int:
        """获取下次评估的日期（基于时间表）"""
        interval_days = self.assessment_schedules.get(schedule, 7)
        return persona.state.last_assessment_day + interval_days


# ===== 全局实例（便于直接使用）=====
psychiatric_validator = PsychiatricScaleValidator()  # Stage 1
clinical_interpreter = ClinicalInterpreter()          # Stage 3
assessment_orchestrator = AssessmentOrchestrator()    # Stage 2（协调 Stage 1 和 Stage 3） 