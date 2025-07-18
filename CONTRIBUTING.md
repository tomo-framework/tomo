# Contributing to Tomo

Thank you for your interest in contributing to Tomo! We welcome contributions from the community and are excited to work with you to make Tomo better.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with newcomers
- **Focus on what's best** for the community
- **Show empathy** towards others

## 🚀 Getting Started

### Ways to Contribute

- **🐛 Report bugs** - Help us identify and fix issues
- **💡 Suggest features** - Propose new functionality
- **📝 Improve documentation** - Help others understand Tomo
- **🔧 Submit code** - Fix bugs or implement features
- **🧪 Write tests** - Improve test coverage
- **🎨 Improve UX** - Enhance developer experience

### First-Time Contributors

Look for issues labeled:
- `good first issue` - Perfect for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements

## 💻 Development Setup

### Prerequisites

- **Python 3.10+**
- **uv** (recommended) or pip
- **Git**

### Setup Instructions

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/tomo.git
   cd tomo
   ```

2. **Set up development environment**
   ```bash
   # Using uv (recommended)
   uv sync --extra all --extra dev
   uv shell
   
   # Or using pip
   pip install -e .[all,dev]
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Verify setup**
   ```bash
   # Run tests
   pytest
   
   # Check code formatting
   black --check .
   ruff check .
   
   # Check types
   mypy tomo/
   ```

### Project Structure

```
tomo/
├── tomo/                   # Main package
│   ├── core/              # Core functionality (tools, registry, runner)
│   ├── adapters/          # LLM provider adapters
│   ├── orchestrators/     # Orchestration and workflows
│   ├── servers/           # API and MCP servers
│   ├── plugins/           # Plugin system
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
├── examples/              # Example tools and usage
├── docs/                  # Documentation and guides
└── README.md              # Project overview
```

## 📋 Contributing Guidelines

### Code Style

We use automated formatting and linting:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:
```bash
# Format code
black .
ruff check . --fix

# Check types
mypy tomo/
```

### Code Standards

- **Write type hints** for all public functions
- **Add docstrings** using Google style
- **Follow PEP 8** conventions
- **Keep functions small** and focused
- **Use descriptive variable names**
- **Add tests** for new functionality

### Example Code Style

```python
from typing import List, Optional
from pydantic import BaseModel

class ExampleTool(BaseTool):
    """Example tool demonstrating proper style.
    
    Args:
        input_text: The text to process
        options: Optional processing options
        
    Returns:
        Processed text result
        
    Raises:
        ValueError: If input_text is empty
    """
    
    input_text: str
    options: Optional[List[str]] = None
    
    def run(self) -> str:
        """Execute the tool processing."""
        if not self.input_text.strip():
            raise ValueError("Input text cannot be empty")
        
        # Process the text
        result = self.input_text.upper()
        return result
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create an issue** for discussion (for significant changes)
2. **Fork the repository** and create a feature branch
3. **Write tests** for your changes
4. **Update documentation** if needed
5. **Run the full test suite**

### PR Guidelines

1. **Clear title** describing the change
2. **Detailed description** explaining:
   - What changed and why
   - How to test the changes
   - Any breaking changes
3. **Link related issues** using keywords (fixes #123)
4. **Small, focused changes** - easier to review
5. **Update CHANGELOG.md** if applicable

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Added/updated tests
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one maintainer** review required
3. **Address feedback** promptly and respectfully
4. **Squash commits** before merging (if requested)

## 🐛 Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Clear title** summarizing the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (Python version, OS, etc.)
- **Code examples** or error messages
- **Potential solutions** (if known)

### Feature Requests

Use the feature request template and include:

- **Clear description** of the proposed feature
- **Use case and motivation** - why is this needed?
- **Proposed implementation** (if applicable)
- **Alternatives considered**
- **Additional context** or examples

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements needed
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tomo --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests matching pattern
pytest -k "test_calculator"
```

### Writing Tests

- **Use pytest** framework
- **Test both success and failure cases**
- **Use descriptive test names**
- **Follow AAA pattern** (Arrange, Act, Assert)
- **Mock external dependencies**

Example test:
```python
import pytest
from tomo import ToolRegistry, ToolRunner
from tomo.core.exceptions import ToolNotFoundError

def test_tool_runner_executes_registered_tool():
    """Test that ToolRunner can execute a registered tool."""
    # Arrange
    registry = ToolRegistry()
    registry.register(CalculatorTool)
    runner = ToolRunner(registry)
    
    # Act
    result = runner.run_tool("CalculatorTool", {
        "operation": "add",
        "a": 5,
        "b": 3
    })
    
    # Assert
    assert result == 8

def test_tool_runner_raises_error_for_unregistered_tool():
    """Test that ToolRunner raises error for unregistered tools."""
    # Arrange
    registry = ToolRegistry()
    runner = ToolRunner(registry)
    
    # Act & Assert
    with pytest.raises(ToolNotFoundError):
        runner.run_tool("NonexistentTool", {})
```

## 📚 Documentation

### Documentation Types

- **API Documentation** - Docstrings in code
- **User Guides** - Step-by-step tutorials
- **Reference** - Comprehensive API reference
- **Examples** - Working code examples

### Writing Documentation

- **Use clear, simple language**
- **Include code examples**
- **Test all examples** work correctly
- **Update for API changes**
- **Follow existing structure**

### Building Documentation

```bash
# Test documentation examples
python docs/examples/code/test-integration.py

# Check documentation builds
# (Future: sphinx-build or similar)
```

## 🏗️ Development Workflow

### Branching Strategy

- **main** - Stable, production-ready code
- **feature/description** - New features
- **bugfix/description** - Bug fixes
- **docs/description** - Documentation updates

### Commit Messages

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat` - New feature
- `fix` - Bug fix  
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks

Examples:
```
feat(core): add new ToolValidator class

fix(adapters): resolve OpenAI schema conversion bug

docs(readme): add installation instructions

test(core): add tests for ToolRegistry.list() method
```

### Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Create release PR**
4. **Tag release** after merge
5. **Publish to PyPI** automatically (CI/CD)

## 🤝 Community

### Getting Help

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Documentation** - Comprehensive guides and examples

### Stay Connected

- **Star the repository** to show support
- **Watch releases** for updates
- **Share your projects** using Tomo
- **Contribute examples** and use cases

### Recognition

We appreciate all contributions! Contributors will be:

- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Recognized in documentation**

## 📞 Contact

- **Maintainers**: Create an issue for questions
- **Security Issues**: Create a private security advisory
- **General Discussion**: Use GitHub Discussions

---

Thank you for contributing to Tomo! Your efforts help make this project better for everyone. 🎉 