# PROXIMO Chatbot - Modular Architecture

## Overview

The PROXIMO Chatbot is a modular, layered conversational health agent framework designed for psychosocial safety. This document describes the new modular architecture located in `src_new/`.

## Architecture

The system follows a **five-layer architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                   PROXIMO Chatbot                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Adaptive    │  │  Safety      │  │ Conversation │ │
│  │  Layer       │  │  Layer       │  │  Layer       │ │
│  │              │  │              │  │              │ │
│  │ • Feedback   │  │ • Guardrails │  │ • Pipeline   │ │
│  │ • History    │  │ • Validator  │  │ • Agents     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Control     │  │  Perception  │                    │
│  │  Layer       │  │  Layer       │                    │
│  │              │  │              │                    │
│  │ • Router     │  │ • PsyGUARD   │                    │
│  │ • Updater    │  │ • Question-  │                    │
│  │ • Context    │  │   naires     │                    │
│  └──────────────┘  └──────────────┘                    │
│                                                          │
│  ┌──────────────┐                                       │
│  │  Shared      │                                       │
│  │  Components  │                                       │
│  │              │                                       │
│  │ • Models     │                                       │
│  │ • Utils      │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Perception Layer (`src_new/perception/`)

**Purpose**: Real-time risk assessment and signal detection

**Components**:
- **PsyGuardService**: PsyGUARD-RoBERTa model integration for real-time risk scoring
- **QuestionnaireService**: PHQ-9 and GAD-7 assessment management
- **QuestionnaireTrigger**: Intelligent triggering mechanism
- **QuestionnaireMapper**: Maps assessment scores to risk routes

**Key Features**:
- Multi-label risk classification (11 categories)
- Real-time chat content analysis
- Structured questionnaire assessments
- Priority-based signal integration

### 2. Control Layer (`src_new/control/`)

**Purpose**: Risk routing and conversation rigidity management

**Components**:
- **RiskRouter**: Central routing decision engine
- **RouteUpdater**: Dynamic route transitions
- **ControlContext**: Context management

**Key Features**:
- Multi-signal risk routing
- Chat content priority over questionnaires
- Rigid score calculation (0.0-1.0)
- One-way route upgrades (safety-first)

### 3. Conversation Layer (`src_new/conversation/`)

**Purpose**: Multi-agent conversation orchestration

**Components**:
- **ConversationPipeline**: High-level orchestration
- **SessionService**: Session management
- **Agents**:
  - **LowRiskAgent**: Free empathetic chat
  - **MediumRiskAgent**: Semi-structured with state machine
  - **HighRiskAgent**: Fixed safety script

**Key Features**:
- Temperature-based flexibility control
- State machine for semi-structured conversations
- Resistance and acceptance detection
- Fixed scripts for high-risk scenarios

### 4. Safety Layer (`src_new/safety/`)

**Purpose**: Content safety and policy enforcement

**Components**:
- **SafetyGuardrailsService**: NeMo Guardrails integration
- **SafetyValidator**: Content validation

**Key Features**:
- User input safety checks
- Response content filtering
- Fixed script validation
- Prohibited pattern detection

### 5. Adaptive Layer (`src_new/adaptive/`)

**Purpose**: Feedback collection and continuous improvement

**Components**:
- **FeedbackCollector**: User feedback collection
- **HistoryService**: User history management

**Key Features**:
- Low/Medium/High risk feedback collection
- User assessment history
- Feedback statistics
- Complete conversation history

## Key Innovations

### 1. Temperature-Based Flexibility Control

The system uses `rigid_score` (0.0-1.0) to control LLM temperature:

```python
adjusted_temp = max(0.1, base_temp - 0.8 * rigid_score)
```

- **Low Risk** (rigid_score = 0.15-0.3): High temperature → Flexible responses
- **Medium Risk** (rigid_score = 0.5-0.75): Medium temperature → Semi-structured responses
- **High Risk** (rigid_score = 1.0): Fixed script → No LLM generation

### 2. State Machine for Semi-Structured Conversations

MediumRiskAgent uses a state machine with 6 states:
- `INITIAL_SUGGESTION`
- `DETECTING_RESISTANCE`
- `HANDLING_RESISTANCE`
- `ACCEPTED`
- `REJECTED`
- `PROVIDING_RESOURCES`

### 3. Multi-Signal Risk Assessment

Combines multiple risk signals:
- Questionnaire scores (PHQ-9, GAD-7)
- PsyGUARD real-time scores
- Priority rules (chat content > questionnaire)

## Testing

### Layer Tests
- `test_perception_layer/`: Perception layer tests
- `test_control_layer/`: Control layer tests
- `test_conversation_layer/`: Conversation layer tests
- `test_safety_layer/`: Safety layer tests
- `test_adaptive_layer/`: Adaptive layer tests

### Integration Tests
- `test_integration/`: End-to-end scenario tests
  - Low/Medium/High risk scenarios
  - Route transitions
  - Boundary cases
  - Error recovery
  - Safety monitoring

## Documentation

- **Control Layer Rigidity Analysis**: `docs/developer/control_layer_rigidity_analysis.md`
- **Risk Score Mapping**: `docs/developer/risk_score_rigid_score_mapping.md`
- **Temperature Control**: `docs/developer/temperature_math_explanation.md`
- **Integration Tests**: `docs/developer/integration_tests_documentation.md`

## Quick Start

### Prerequisites

- Python 3.12+
- PROXIMO conda environment
- Ollama service (for LLM)
- PsyGUARD-RoBERTa model

### Download PsyGUARD-RoBERTa Model

The PsyGUARD-RoBERTa model is required for risk detection. Download it from Hugging Face:

**Option 1: Using Git LFS (Recommended)**
```bash
git lfs install
git clone https://huggingface.co/qiuhuachuan/PsyGUARD-RoBERTa
```

**Option 2: Using Hugging Face Mirror**
```bash
git clone https://hf-mirror.com/qiuhuachuan/PsyGUARD-RoBERTa
```

**Option 3: Manual Download**
1. Visit: https://huggingface.co/qiuhuachuan/PsyGUARD-RoBERTa
2. Download all files to `PsyGUARD-RoBERTa/` directory

**Note**: The model files are large (~500MB) and are not included in this repository. Please download them separately and place in the `PsyGUARD-RoBERTa/` directory.

**Model Citation**:
```bibtex
@inproceedings{qiu-etal-2024-psyguard,
    title = "{P}sy{GUARD}: An Automated System for Suicide Detection and Risk Assessment in Psychological Counseling",
    author = "Qiu, Huachuan and Ma, Lizhi and Lan, Zhenzhong",
    booktitle = "Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing",
    year = "2024",
    url = "https://aclanthology.org/2024.emnlp-main.264"
}
```

### Setup

```bash
# Activate conda environment
conda activate PROXIMO

# Install dependencies
uv sync

# Run tests
pytest test_integration/
```

### Usage

```python
from src_new.conversation.pipeline import ConversationPipeline
from src_new.control.control_context import ControlContext

# Initialize pipeline
pipeline = ConversationPipeline()

# Create control context
context = ControlContext(
    user_id="user_123",
    route="low",
    rigid_score=0.15
)

# Process message
result = await pipeline.process_message(
    user_id="user_123",
    user_message="I've been feeling anxious",
    control_context=context
)
```

## Migration from `src/` to `src_new/`

The `src_new/` directory contains the new modular architecture. The old `src/` directory is maintained for backward compatibility.

**Key Differences**:
- **Modular Architecture**: Five distinct layers with clear separation
- **Type Safety**: Better type hints and validation
- **Test Coverage**: Comprehensive test suite
- **Documentation**: Detailed technical documentation

## License

MIT License - see LICENSE file for details.

## Contributing

See CONTRIBUTING.md for guidelines.

## Acknowledgments

- EmoAgent framework for inspiration
- PsyGUARD-RoBERTa for risk detection
- NeMo Guardrails for safety enforcement

