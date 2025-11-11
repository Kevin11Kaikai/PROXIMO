# PROXIMO Chatbot Architecture

## Overview

The PROXIMO Chatbot is a modular, layered conversational health agent framework designed for psychosocial safety. This document provides a detailed overview of the system architecture.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface                              │
│                  (Frontend / API Client)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Conversation Pipeline                          │
│              (src_new/conversation/pipeline.py)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Perception  │    │   Control    │    │ Conversation │
│    Layer     │───►│    Layer     │───►│    Layer     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Safety     │    │   Adaptive   │    │    Shared    │
│    Layer     │    │    Layer     │    │  Components  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Layer Details

### 1. Perception Layer

**Location**: `src_new/perception/`

**Purpose**: Real-time risk assessment and signal detection

**Components**:

#### PsyGuardService
- **File**: `psyguard_service.py`
- **Purpose**: PsyGUARD-RoBERTa model integration
- **Features**:
  - Multi-label classification (11 risk categories)
  - Real-time risk scoring (0.0-1.0)
  - Threshold-based risk detection
  - Model loading and inference

#### QuestionnaireService
- **File**: `questionnaire_service.py`
- **Purpose**: PHQ-9 and GAD-7 assessment management
- **Features**:
  - PHQ-9 depression screening (0-27 scale)
  - GAD-7 anxiety screening (0-21 scale)
  - Special handling for PHQ-9 Q9 (suicidal ideation)
  - Assessment result parsing and validation

#### QuestionnaireTrigger
- **File**: `questionnaire_trigger.py`
- **Purpose**: Intelligent triggering mechanism
- **Features**:
  - Turn-count based triggers
  - Early trigger for suicide intent
  - Priority-based trigger ordering
  - Trigger condition evaluation

#### QuestionnaireMapper
- **File**: `questionnaire_mapper.py`
- **Purpose**: Maps assessment scores to risk routes
- **Features**:
  - PHQ-9 to route mapping (Low/Medium/High)
  - GAD-7 to route mapping (Low/Medium/High)
  - Route combination logic
  - Chat content priority rules

**Data Flow**:
```
User Message → PsyGuardService → Risk Score
User Message → QuestionnaireTrigger → Trigger Assessment
Assessment → QuestionnaireService → Scores
Scores → QuestionnaireMapper → Route Decision
```

### 2. Control Layer

**Location**: `src_new/control/`

**Purpose**: Risk routing and conversation rigidity management

**Components**:

#### RiskRouter
- **File**: `risk_router.py`
- **Purpose**: Central routing decision engine
- **Features**:
  - Multi-signal risk routing
  - Chat content priority over questionnaires
  - Route-to-rigid-score mapping
  - Routing decision metadata

#### RouteUpdater
- **File**: `route_updater.py`
- **Purpose**: Dynamic route transitions
- **Features**:
  - One-way route upgrades (Low → Medium → High)
  - No downgrade rules (safety-first)
  - Direct high-risk escalation
  - Route transition validation

#### ControlContext
- **File**: `control_context.py`
- **Purpose**: Context management
- **Features**:
  - Perception data storage
  - Routing decision tracking
  - Rigid score storage
  - Route history management

**Data Flow**:
```
Perception Data → RiskRouter → Route Decision
Route Decision → RouteUpdater → Route Update
Route Decision → ControlContext → Context Storage
Route + Scores → RiskRouter → Rigid Score Calculation
```

### 3. Conversation Layer

**Location**: `src_new/conversation/`

**Purpose**: Multi-agent conversation orchestration

**Components**:

#### ConversationPipeline
- **File**: `pipeline.py`
- **Purpose**: High-level conversation orchestration
- **Features**:
  - Message routing to appropriate agent
  - Conversation history management
  - Session state management
  - Response generation coordination

#### SessionService
- **File**: `session_service.py`
- **Purpose**: Session management
- **Features**:
  - User session tracking
  - Conversation history storage
  - State persistence
  - Session cleanup

#### Agents

##### LowRiskAgent
- **File**: `agents/low_risk_agent.py`
- **Purpose**: Free empathetic chat
- **Features**:
  - High flexibility (temperature = 0.9)
  - Coping skills suggestions
  - Goodbye detection
  - Natural conversation flow

##### MediumRiskAgent
- **File**: `agents/medium_risk_agent.py`
- **Purpose**: Semi-structured conversation
- **Features**:
  - State machine (6 states)
  - Resistance detection
  - Acceptance detection
  - Peer group suggestion
  - Persuasion limits (max 5 turns)

##### HighRiskAgent
- **File**: `agents/high_risk_agent.py`
- **Purpose**: Fixed safety script
- **Features**:
  - Fixed script (no LLM generation)
  - Crisis hotline information
  - Safety banner display
  - Urgent meeting suggestion

**Data Flow**:
```
User Message → ConversationPipeline → Route Selection
Route Selection → Agent Selection → Response Generation
Response Generation → Safety Layer → Safety Validation
Safety Validation → ConversationPipeline → Response Return
```

### 4. Safety Layer

**Location**: `src_new/safety/`

**Purpose**: Content safety and policy enforcement

**Components**:

#### SafetyGuardrailsService
- **File**: `guardrails_service.py`
- **Purpose**: NeMo Guardrails integration
- **Features**:
  - User input safety checks
  - Response content filtering
  - Fixed script validation
  - Safe response generation

#### SafetyValidator
- **File**: `safety_validator.py`
- **Purpose**: Content validation
- **Features**:
  - Response content validation
  - Prohibited pattern detection
  - User message safety assessment
  - Safety score calculation

**Data Flow**:
```
User Message → SafetyValidator → Safety Check
Agent Response → SafetyGuardrailsService → Content Filtering
Filtered Response → SafetyValidator → Final Validation
```

### 5. Adaptive Layer

**Location**: `src_new/adaptive/`

**Purpose**: Feedback collection and continuous improvement

**Components**:

#### FeedbackCollector
- **File**: `feedback.py`
- **Purpose**: User feedback collection
- **Features**:
  - Low/Medium/High risk feedback collection
  - Feedback validation and scoring
  - User and route-based feedback retrieval
  - Feedback statistics

#### HistoryService
- **File**: `history_service.py`
- **Purpose**: User history management
- **Features**:
  - User assessment history
  - User feedback history
  - Complete conversation history
  - Feedback statistics

**Data Flow**:
```
Conversation End → FeedbackCollector → Feedback Collection
Feedback → HistoryService → History Storage
History → Analysis → Improvement Suggestions
```

## Key Design Patterns

### 1. Layered Architecture

- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Direction**: Layers depend only on lower layers
- **Interface-Based**: Layers communicate through well-defined interfaces

### 2. Strategy Pattern

- **Agent Selection**: Different agents for different risk levels
- **Routing Strategy**: Different routing strategies for different scenarios
- **Safety Strategy**: Different safety strategies for different risk levels

### 3. State Machine Pattern

- **MediumRiskAgent**: 6-state machine for peer group suggestion
- **State Transitions**: Based on user input and internal logic
- **State Persistence**: Per-user state management

### 4. Observer Pattern

- **Feedback Collection**: Observes conversation events
- **History Tracking**: Observes user interactions
- **Safety Monitoring**: Observes content generation

## Data Flow

### Complete Conversation Flow

```
1. User sends message
   ↓
2. Perception Layer:
   - PsyGuardService: Real-time risk scoring
   - QuestionnaireTrigger: Check if assessment needed
   - QuestionnaireService: Run assessment if triggered
   - QuestionnaireMapper: Map scores to route
   ↓
3. Control Layer:
   - RiskRouter: Make routing decision
   - RouteUpdater: Update route if needed
   - ControlContext: Store context
   ↓
4. Conversation Layer:
   - ConversationPipeline: Route to appropriate agent
   - Agent: Generate response based on risk level
   ↓
5. Safety Layer:
   - SafetyGuardrailsService: Filter content
   - SafetyValidator: Validate response
   ↓
6. Response returned to user
   ↓
7. Adaptive Layer:
   - FeedbackCollector: Collect feedback
   - HistoryService: Store history
```

## Key Algorithms

### 1. Rigid Score Calculation

```python
def calculate_rigid_score(route, phq9_score, gad7_score):
    if route == "high":
        return 1.0
    elif route == "medium":
        max_score = max(phq9_score, gad7_score)
        if max_score >= 15:
            return 0.75
        elif max_score >= 10:
            return 0.6
        else:
            return 0.5
    else:  # low
        max_score = max(phq9_score, gad7_score)
        if max_score >= 5:
            return 0.3
        else:
            return 0.15
```

### 2. Temperature Adjustment

```python
def adjust_temperature(base_temp, rigid_score):
    return max(0.1, base_temp - 0.8 * rigid_score)
```

### 3. Route Decision

```python
def decide_route(phq9_score, gad7_score, chat_risk_score):
    # Chat content priority
    if chat_risk_score >= HIGH_RISK_THRESHOLD:
        return "high"
    elif chat_risk_score >= MEDIUM_RISK_THRESHOLD:
        return "medium"
    
    # Questionnaire-based routing
    phq9_route = map_phq9(phq9_score)
    gad7_route = map_gad7(gad7_score)
    return combine_routes(phq9_route, gad7_route)
```

## Performance Considerations

### 1. Async/Await

- All I/O operations are async
- Non-blocking model inference
- Concurrent request handling

### 2. Caching

- Model loading cached
- Assessment results cached
- Session state cached

### 3. Resource Management

- Model lazy loading
- Connection pooling
- Memory management

## Security Considerations

### 1. Input Validation

- User input sanitization
- Content safety checks
- Pattern detection

### 2. Output Filtering

- Response content filtering
- Prohibited pattern removal
- Safety score validation

### 3. Access Control

- Session-based authentication
- Role-based access control
- Rate limiting

## Testing Strategy

### 1. Unit Tests

- Layer-specific tests
- Component isolation
- Mock dependencies

### 2. Integration Tests

- End-to-end scenarios
- Layer interaction tests
- System integration tests

### 3. Performance Tests

- Load testing
- Stress testing
- Resource usage testing

## Deployment

### 1. Local Development

```bash
conda activate PROXIMO
uv sync
pytest
```

### 2. Docker Deployment

```bash
docker-compose up
```

### 3. Production Deployment

- Environment variables
- Secret management
- Monitoring and logging
- Error tracking

## Future Improvements

### 1. Enhanced State Machine

- More states for complex scenarios
- State transition learning
- Adaptive state machine

### 2. Advanced Risk Assessment

- Multi-model ensemble
- Temporal risk analysis
- Context-aware scoring

### 3. Improved Safety

- Real-time safety monitoring
- Adaptive safety rules
- Safety score learning

### 4. Better Feedback Loop

- Automated feedback analysis
- Model fine-tuning
- Continuous improvement

## References

- EmoAgent Framework: Multi-Agent AI Framework for Mental Health
- PsyGUARD-RoBERTa: Real-time risk detection model
- NeMo Guardrails: Safety and policy enforcement
- PHQ-9: Depression screening tool
- GAD-7: Anxiety screening tool

