# Changelog

All notable changes to the PROXIMO Chatbot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - PROXIMO Chatbot Modular Architecture (November 2025)

#### New Architecture (`src_new/`)

- **Perception Layer** (`src_new/perception/`)
  - `PsyGuardService`: PsyGUARD-RoBERTa model integration for real-time risk scoring
  - `QuestionnaireService`: PHQ-9 and GAD-7 assessment management
  - `QuestionnaireTrigger`: Intelligent triggering mechanism
  - `QuestionnaireMapper`: Maps assessment scores to risk routes

- **Control Layer** (`src_new/control/`)
  - `RiskRouter`: Central routing decision engine with multi-signal integration
  - `RouteUpdater`: Dynamic route transitions with one-way upgrades
  - `ControlContext`: Context management for routing decisions

- **Conversation Layer** (`src_new/conversation/`)
  - `ConversationPipeline`: High-level conversation orchestration
  - `SessionService`: Session management and history tracking
  - `LowRiskAgent`: Free empathetic chat with coping skills
  - `MediumRiskAgent`: Semi-structured conversation with state machine
  - `HighRiskAgent`: Fixed safety script with crisis intervention

- **Safety Layer** (`src_new/safety/`)
  - `SafetyGuardrailsService`: NeMo Guardrails integration
  - `SafetyValidator`: Content validation and safety checks

- **Adaptive Layer** (`src_new/adaptive/`)
  - `FeedbackCollector`: User feedback collection and analysis
  - `HistoryService`: User history management and statistics

- **Shared Components** (`src_new/shared/`)
  - `Models`: Data models (PerceptionSummary, PipelineResult, ConversationTurn)
  - `Utils`: Utility functions and helpers

#### Key Features

- **Temperature-Based Flexibility Control**: Rigid score system (0.0-1.0) controls LLM temperature for adaptive conversation styles
- **State Machine for Semi-Structured Conversations**: 6-state machine for medium-risk peer group suggestions
- **Multi-Signal Risk Assessment**: Combines questionnaire scores and PsyGUARD real-time scores
- **Priority-Based Routing**: Chat content risk has priority over questionnaire scores
- **Resistance Detection**: Keyword-based detection for privacy, time, stigma, and doubt concerns
- **Acceptance Detection**: Keyword-based acceptance recognition

#### Testing

- **Layer Tests**: Comprehensive test suite for each layer
  - `test_perception_layer/`: Perception layer tests
  - `test_control_layer/`: Control layer tests
  - `test_conversation_layer/`: Conversation layer tests
  - `test_safety_layer/`: Safety layer tests
  - `test_adaptive_layer/`: Adaptive layer tests

- **Integration Tests**: End-to-end scenario testing
  - `test_integration/`: Complete integration test suite
    - Low/Medium/High risk scenarios
    - Route transitions
    - Boundary cases
    - Error recovery
    - Safety monitoring

#### Documentation

- **Technical Documentation**:
  - `docs/developer/control_layer_rigidity_analysis.md`: Control layer rigidity analysis
  - `docs/developer/risk_score_rigid_score_mapping.md`: Risk score to rigid score mapping
  - `docs/developer/temperature_math_explanation.md`: Temperature control mathematical explanation
  - `docs/developer/integration_tests_documentation.md`: Integration tests documentation

- **Architecture Documentation**:
  - `README_PROXIMO_CHATBOT.md`: New architecture overview
  - `docs/weekly_report_2025_11_01.md`: Weekly progress report

#### Technical Improvements

- **Modular Architecture**: Five distinct layers with clear separation of concerns
- **Type Safety**: Better type hints and validation using Pydantic
- **Async/Await**: Full async/await support for better performance
- **Error Handling**: Comprehensive error handling and graceful degradation
- **Backward Compatibility**: Legacy `src/` directory maintained for compatibility

## [0.1.0] - Initial Release

### Added

- Initial project structure
- Basic simulation engine
- LLM integration with Ollama
- Clinical assessment tools (PHQ-9, GAD-7)
- Mechanistic interpretability
- Web dashboard
- Docker support

### Changed

- N/A (initial release)

### Deprecated

- N/A (initial release)

### Removed

- N/A (initial release)

### Fixed

- N/A (initial release)

### Security

- N/A (initial release)

---

## Version History

- **0.1.0** (Initial Release): Basic simulation engine and assessment tools
- **Unreleased** (November 2025): PROXIMO Chatbot modular architecture

---

## Notes

- The `src_new/` directory contains the new modular architecture
- The `src/` directory is maintained for backward compatibility
- All new development should use `src_new/` architecture
- Migration from `src/` to `src_new/` is planned for future releases

