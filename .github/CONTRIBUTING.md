# Contributing to TimeTrack

*Pull requests, bug reports, and all other forms of contribution are welcomed and highly encouraged!* :octocat:

## Our Standards

Please review our [Code of Conduct](CODE_OF_CONDUCT.md). We expect it to be honored by everyone who contributes to this project.

## Bug Reports

Before creating an issue, check if you are using the latest version of TimeTrack. Then:

- **Check existing issues** first to avoid duplicates
- **Use the issue template** provided
- **Include clear steps** to reproduce the bug
- **Include screenshots** of the issue if possible
- **Include browser and OS details**
- **Include details about your environment** (Python version, database, etc.)

## Feature Proposals

Feature proposals are welcome! We'll consider all requests but may not accept all of them to maintain TimeTrack's simplicity and focus.

- **Search first** for similar proposals
- **Describe the use case** clearly
- **Keep it simple** and focused
- **Consider the project's scope** - time tracking for employees

## Pull Requests

Before submitting a pull request:

1. **Discuss major changes** first in an issue
2. **Keep changes focused** - one feature/fix per PR
3. **Add tests** for new functionality
4. **Follow style guidelines**:
   - Use [Black](https://github.com/psf/black) for code formatting
   - Use [isort](https://pycqa.github.io/isort/) for import sorting
   - Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
   - Use type hints where appropriate

## Commit Guidelines

```
[type] Short description under 50 chars

More detailed explanation if needed. Wrap at 72 characters.
Explain the motivation for the change.

Resolves: #123
```

Types:
- **feature**: New feature or enhancement
- **fix**: Bug fix
- **refactor**: Code refactoring
- **style**: Code style update
- **docs**: Documentation
- **test**: Testing
- **config**: Configuration changes
- **ui**: User interface improvements

## Development Environment

1. Clone the repository
2. Set up a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install development dependencies: `pip install -r requirements-dev.txt`
6. Set up pre-commit hooks: `pre-commit install`

## The Contributor's Token :key:

Include the ⚡ lightning emoji at the start of your pull requests and issues to show you've read these guidelines.
