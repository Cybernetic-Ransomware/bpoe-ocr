# bpoe-ocr — task runner
# Install: scoop install just  |  winget install Casey.Just

set shell := ["powershell", "-Command"]

# Run pre-commit on staged files, then open Commitizen
# Stage your changes first: git add <files>
commit:
    uv run pre-commit run
    .venv\Scripts\cz commit

# Bump version on release (auto-tags vX.Y.Z, updates pyproject.toml)
bump:
    .venv\Scripts\cz bump

# Auto-format source files
format:
    uv run ruff format src/

# Run the full linting suite
lint:
    uv run ruff check --fix src/
    uv run ty check src/
    uv run python -m codespell_lib src/
    uv run bandit -r src/ -c pyproject.toml -q

# Run unit tests (excludes integration by default)
test:
    uv run pytest

# Run integration tests (requires Docker — starts real MongoDB via testcontainers)
test-integration:
    uv run pytest -m integration

# Start full Docker stack (app + mongo + minio) with rebuild
up:
    docker-compose -f docker/docker-compose.yml up --build -d

# Stop and remove Docker stack containers
down:
    docker-compose -f docker/docker-compose.yml down

# Stream Docker app logs
logs:
    docker-compose -f docker/docker-compose.yml logs -f app