# Contributing to PROXIMO Chatbot

Thank you for your interest in contributing to PROXIMO Chatbot! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different opinions and approaches

## Development Setup

### Prerequisites

- Python 3.12+
- Conda (for environment management)
- Git
- Ollama (for LLM services)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/glitch_core.git
   cd glitch_core
   ```

2. **Create and activate Conda environment**
   ```bash
   conda env create -f environment.yml
   conda activate PROXIMO
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Run tests**
   ```bash
   pytest test_integration/
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

```bash
git add .
git commit -m "feat: Add your feature description"
```

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use meaningful variable names

### Formatting

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black src_new/

# Lint code
ruff check src_new/
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy src_new/
```

## Testing

### Writing Tests

- Write tests for all new features
- Follow the existing test structure
- Use descriptive test names
- Test both success and failure cases

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_integration/test_low_risk_scenario.py

# Run with coverage
pytest --cov=src_new --cov-report=html
```

### Test Structure

- **Layer Tests**: `test_*_layer/` - Test individual layers
- **Integration Tests**: `test_integration/` - Test end-to-end scenarios
- **Unit Tests**: `tests/` - Test individual components

## Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Include parameter descriptions
- Include return value descriptions
- Include usage examples for complex functions

### Architecture Documentation

- Update `ARCHITECTURE.md` for architectural changes
- Update `README_PROXIMO_CHATBOT.md` for new features
- Update `CHANGELOG.md` for all changes

## Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Check Code Style**: Run `black` and `ruff`
3. **Update Documentation**: Update relevant documentation
4. **Update Changelog**: Add entry to `CHANGELOG.md`

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Tests added/updated
```

## Project Structure

### Source Code

- `src_new/`: New modular architecture
  - `perception/`: Perception layer
  - `control/`: Control layer
  - `conversation/`: Conversation layer
  - `safety/`: Safety layer
  - `adaptive/`: Adaptive layer
  - `shared/`: Shared components

### Tests

- `test_perception_layer/`: Perception layer tests
- `test_control_layer/`: Control layer tests
- `test_conversation_layer/`: Conversation layer tests
- `test_safety_layer/`: Safety layer tests
- `test_adaptive_layer/`: Adaptive layer tests
- `test_integration/`: Integration tests

### Documentation

- `docs/developer/`: Developer documentation
- `docs/researcher/`: Researcher documentation
- `ARCHITECTURE.md`: Architecture overview
- `README_PROXIMO_CHATBOT.md`: PROXIMO Chatbot overview
- `CHANGELOG.md`: Version history

## Areas for Contribution

### High Priority

1. **Performance Optimization**
   - Optimize PsyGUARD model loading
   - Improve state machine performance
   - Optimize database queries

2. **Enhanced Safety Features**
   - Additional safety rules
   - Improved content validation
   - Better error handling

3. **Documentation**
   - API documentation
   - Tutorials and guides
   - Code examples

### Medium Priority

1. **New Features**
   - Additional agent types
   - New assessment tools
   - Enhanced feedback mechanisms

2. **Testing**
   - Additional test coverage
   - Performance tests
   - Integration tests

3. **Tooling**
   - Development scripts
   - Deployment tools
   - Monitoring tools

## Questions?

If you have questions or need help:

1. Check the documentation
2. Search existing issues
3. Create a new issue
4. Ask in discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Thank you for contributing to PROXIMO Chatbot! Your contributions help make this project better for everyone.

