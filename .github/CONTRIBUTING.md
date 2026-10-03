# Contributing to TimeTrack

*Pull requests, bug reports, and all other forms of contribution are welcome.*

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
- **Consider the project's scope**: personal time tracking, one user per installation

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

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: short description in the imperative, under 72 characters

Optional body explaining what changed and why. Wrap at 72 characters.

Resolves #123
```

Types: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `chore`, `ci`.

User-visible changes also get a line in the `[Unreleased]` section of `CHANGELOG.md`.

## Development Environment

The quickest way to run the app is Docker (`docker compose up --build`, see the README). For
development:

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate it:
   - Linux / macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Copy `.env.example` to `.env` and adjust it (SQLite is fine: `DATABASE_URL=sqlite:///timetrack.db`)
6. Create the schema and some data: `flask db upgrade && flask seed demo`
7. Set up pre-commit hooks: `pre-commit install`

Before opening a pull request, run `black app tests`, `isort app tests`, `mypy app` and
`pytest tests/`. CI runs the same checks and also builds the Docker image. See
[WORKFLOW.md](../WORKFLOW.md) for details.
