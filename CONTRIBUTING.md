# Contributing to Leader Election Playground

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install -r requirements-dev.txt`

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Run `make lint` before committing

## Testing

- Write unit tests for new code
- Run `make test` to execute tests
- Aim for >90% coverage

## Commit Messages

Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring

## Pull Requests

- Create feature branches from `main`
- Ensure CI passes
- Update documentation as needed
- Squash commits before merging