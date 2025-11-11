"""PsyGUARD-RoBERTa integration for real-time risk scoring."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

import torch
from transformers import BertConfig, BertTokenizer

# 导入 PsyGUARD 模型类
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "PsyGUARD-RoBERTa"))
try:
    from eval_proximo import RobertaForSequenceClassification, get_device, safe_torch_load
except ImportError:
    # 如果导入失败，提供占位实现
    RobertaForSequenceClassification = None
    get_device = lambda: 'cpu'
    safe_torch_load = torch.load

from src.core.logging import get_logger

logger = get_logger(__name__)

# 阈值配置（根据设计文档）
SUICIDE_INTENT_THRESHOLD = 0.80  # 触发问卷
HIGH_RISK_DIRECT_THRESHOLD = 0.95  # 直接 High Risk
MEDIUM_RISK_THRESHOLD = 0.70  # Medium Risk
LOW_RISK_CLEAR_THRESHOLD = 0.40  # 低风险稳定阈值

# 标签映射（来自 eval_proximo.py）
ID2LABEL = {
    "0": "自杀未遂",
    "1": "自杀准备行为",
    "2": "自杀计划",
    "3": "主动自杀意图",
    "4": "被动自杀意图",
    "5": "用户攻击行为",
    "6": "他人攻击行为",
    "7": "自伤行为",
    "8": "自伤意图",
    "9": "关于自杀的探索",
    "10": "与自杀/自伤/攻击行为无关"
}

# 高风险标签索引（用于计算风险分数）
HIGH_RISK_LABEL_INDICES = [0, 1, 2, 3, 4, 7, 8, 9]  # 自杀和自伤相关
MEDIUM_RISK_LABEL_INDICES = [5, 6]  # 攻击行为


class PsyGuardService:
    """Service for PsyGUARD-RoBERTa model integration.
    
    Provides real-time risk scoring for user messages using the
    PsyGUARD-RoBERTa multi-label classification model.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize PsyGUARD service.
        
        Args:
            model_path: Path to PsyGUARD-RoBERTa model directory
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
            enabled: Whether PsyGUARD is enabled (default: True)
        """
        self.enabled = enabled
        
        # 默认模型路径
        if model_path is None:
            base_path = Path(__file__).parent.parent.parent
            model_path = str(base_path / "PsyGUARD-RoBERTa")
        
        self.model_path = Path(model_path)
        self.model_file = "pytorch_model.bin"
        self.device = device or get_device()
        
        # 模型组件
        self._model: Optional[RobertaForSequenceClassification] = None
        self._tokenizer: Optional[BertTokenizer] = None
        self._config: Optional[BertConfig] = None
        self._loaded = False
        
    async def load(self) -> bool:
        """
        Load PsyGUARD model and tokenizer.
        
        Returns:
            True if loading successful, False otherwise
        """
        if not self.enabled:
            logger.info("PsyGUARD service is disabled")
            return True
            
        if self._loaded:
            return True
            
        if RobertaForSequenceClassification is None:
            logger.error("PsyGUARD model class not available. Please check PsyGUARD-RoBERTa installation.")
            return False
        
        try:
            logger.info(f"Loading PsyGUARD model from {self.model_path}")
            
            # 检查模型文件
            model_bin_path = self.model_path / self.model_file
            if not model_bin_path.exists():
                logger.error(f"Model file not found: {model_bin_path}")
                return False
            
            # 加载配置
            logger.info("Loading model config...")
            self._config = BertConfig.from_pretrained(
                str(self.model_path),
                num_labels=11,
                problem_type="multi_label_classification",
                finetuning_task='text classification'
            )
            
            # 加载 tokenizer
            logger.info("Loading tokenizer...")
            self._tokenizer = BertTokenizer.from_pretrained(
                str(self.model_path),
                use_fast=False
            )
            
            # 加载模型架构
            logger.info("Loading model architecture...")
            self._model = RobertaForSequenceClassification(self._config, str(self.model_path))
            
            # 加载模型权重
            logger.info(f"Loading model weights from {model_bin_path}...")
            state_dict = safe_torch_load(str(model_bin_path), map_location=self.device)
            
            # 过滤 state_dict
            filtered_state_dict = {}
            model_state_dict = self._model.state_dict()
            for key, value in state_dict.items():
                if key in model_state_dict:
                    if model_state_dict[key].shape == value.shape:
                        filtered_state_dict[key] = value
            
            # 加载权重
            self._model.load_state_dict(filtered_state_dict, strict=False)
            self._model.to(self.device)
            self._model.eval()
            
            self._loaded = True
            logger.info("PsyGUARD model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PsyGUARD model: {e}", exc_info=True)
            self._loaded = False
            return False
    
    def _calculate_risk_score(self, predictions: torch.Tensor) -> float:
        """
        Calculate risk score from model predictions.
        
        Args:
            predictions: Binary predictions tensor (11 labels)
            
        Returns:
            Risk score in [0, 1]
        """
        # 将预测转换为列表
        pred_list = predictions[0].detach().cpu().tolist()
        
        # 检查高风险标签
        high_risk_detected = any(pred_list[i] == 1 for i in HIGH_RISK_LABEL_INDICES)
        medium_risk_detected = any(pred_list[i] == 1 for i in MEDIUM_RISK_LABEL_INDICES)
        
        # 计算风险分数
        if high_risk_detected:
            # 如果有高风险标签，计算加权分数
            high_risk_count = sum(pred_list[i] for i in HIGH_RISK_LABEL_INDICES)
            # 归一化到 [0.7, 1.0]
            risk_score = 0.7 + (high_risk_count / len(HIGH_RISK_LABEL_INDICES)) * 0.3
        elif medium_risk_detected:
            # 中等风险：0.5 - 0.7
            medium_risk_count = sum(pred_list[i] for i in MEDIUM_RISK_LABEL_INDICES)
            risk_score = 0.5 + (medium_risk_count / len(MEDIUM_RISK_LABEL_INDICES)) * 0.2
        else:
            # 低风险：0.0 - 0.5
            risk_score = 0.0
        
        # 确保在 [0, 1] 范围内
        return min(max(risk_score, 0.0), 1.0)
    
    async def score(self, text: str) -> Dict[str, Any]:
        """
        Score a user message for risk.
        
        Args:
            text: User message text
            
        Returns:
            Dictionary with:
                - risk_score: float in [0, 1]
                - labels: List of detected risk labels
                - label_indices: List of label indices
                - should_trigger_questionnaire: bool (if >= SUICIDE_INTENT_THRESHOLD)
                - should_direct_high_risk: bool (if >= HIGH_RISK_DIRECT_THRESHOLD)
        """
        if not self.enabled:
            return {
                "risk_score": 0.0,
                "labels": [],
                "label_indices": [],
                "should_trigger_questionnaire": False,
                "should_direct_high_risk": False,
                "enabled": False
            }
        
        if not self._loaded:
            await self.load()
        
        if not self._loaded or self._model is None or self._tokenizer is None:
            logger.warning("PsyGUARD model not loaded, returning default score")
            return {
                "risk_score": 0.0,
                "labels": [],
                "label_indices": [],
                "should_trigger_questionnaire": False,
                "should_direct_high_risk": False,
                "error": "Model not loaded"
            }
        
        try:
            # Tokenize input
            input_tokens = self._tokenizer(
                text=text,
                padding='max_length',
                max_length=512,
                truncation=False,
                add_special_tokens=True,
                return_token_type_ids=True,
                return_tensors='pt'
            )
            input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}
            
            # Model inference
            with torch.no_grad():
                outputs = self._model(**input_tokens)
            
            # Get predictions (sigmoid + threshold 0.5)
            predictions = torch.sigmoid(outputs.logits).ge(0.5).int()
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(predictions)
            
            # Get detected labels
            pred_list = predictions[0].detach().cpu().tolist()
            label_indices = [i for i, val in enumerate(pred_list) if val == 1]
            labels = [ID2LABEL[str(i)] for i in label_indices]
            
            # Check thresholds
            should_trigger_questionnaire = risk_score >= SUICIDE_INTENT_THRESHOLD
            should_direct_high_risk = risk_score >= HIGH_RISK_DIRECT_THRESHOLD
            
            return {
                "risk_score": float(risk_score),
                "labels": labels,
                "label_indices": label_indices,
                "should_trigger_questionnaire": should_trigger_questionnaire,
                "should_direct_high_risk": should_direct_high_risk,
                "enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error scoring text with PsyGUARD: {e}", exc_info=True)
            return {
                "risk_score": 0.0,
                "labels": [],
                "label_indices": [],
                "should_trigger_questionnaire": False,
                "should_direct_high_risk": False,
                "error": str(e)
            }
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded and self.enabled
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._model is not None:
            del self._model
            self._model = None
        self._tokenizer = None
        self._config = None
        self._loaded = False


# Global service instance
_psyguard_service: Optional[PsyGuardService] = None


def get_psyguard_service() -> PsyGuardService:
    """Get global PsyGUARD service instance."""
    global _psyguard_service
    if _psyguard_service is None:
        _psyguard_service = PsyGuardService()
    return _psyguard_service
