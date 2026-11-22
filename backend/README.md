# BugPilot AI Backend

Stage 1 backend foundation for the local fixture-only investigation flow. It requires Python 3.10 or later; Python 3.11 is used in the current validation environment. The API uses FastAPI and Pydantic, SQLite through the Python standard library, a bounded in-process coordinator, a deterministic fake provider, and a simulated execution adapter. It does not contact external services at runtime or execute fixture/target code.

The investigation intelligence engine receives only the investigation ID, original report, curated fixture metadata, validated source reference, and bounded source content. It deterministically produces source, hypothesis, test-proposal, and patch-proposal evidence. All generated evidence remains `generated` and `fake_provider`; source evidence is `observed` and fixture-authored. The execution adapter is separately marked `simulated`, while verification remains `not_run`.

## Setup

Create a virtual environment:

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
```

Install only through an organization-approved package index or reviewed wheelhouse. The repository currently has no approved source URL or reviewed lockfile; these installation commands are therefore prerequisites, not verified setup steps.

```powershell
python -m pip install --index-url $env:APPROVED_PYPI_INDEX -r requirements-dev.txt
```

```sh
python -m pip install --index-url "$APPROVED_PYPI_INDEX" -r requirements-dev.txt
```

`requirements.txt` pins runtime direct dependencies. `requirements-dev.txt` adds HTTPX and pytest. `pyproject.toml` mirrors these exact versions and pins the setuptools build backend. No lockfile with transitive hashes is present; these pins alone do not claim a fully reproducible environment.

## Configuration and Run

The SQLite database is initialized automatically during FastAPI startup and stored in the platform-specific application-data directory described in `../docs/SECURITY.md`. Startup fails if owner-only permissions cannot be established. Data is rejected if its configured default resolves under the repository or a detected synced folder.

Set `BUGPILOT_UI_ORIGIN` to the exact loopback frontend origin (default `http://127.0.0.1:3000`). `BUGPILOT_API_PORT` defaults to `8000`; `BUGPILOT_COORDINATOR_CAPACITY` defaults to `4`. Start from `backend/`:

```powershell
python -m app.server
```

```sh
python -m app.server
```

The server binds IPv4 `127.0.0.1` and IPv6 `::1` only. Browser mutations require exact Origin, `Sec-Fetch-Site: same-origin`, and a per-process CSRF token obtained from the same-origin proxy.

## Tests

From `backend/`, run:

```powershell
python -m unittest discover -s tests -v
pytest -v
```

```sh
python -m unittest discover -s tests -v
pytest -v
```

Pytest is in `requirements-dev.txt`; it is not installed in the current environment. The unittest command has been run successfully. Tests use synthetic data and do not execute the fixture project.

## Structure

```text
app/api/              HTTP routes, middleware, dependencies, request parsing
app/core/             Configuration, local security, logging, shared errors
app/models/           Investigation and evidence domain models
app/schemas/          Pydantic API contracts
app/repositories/     SQLite schema, transactions, and queries
app/services/         Fixture and investigation business rules
app/integrations/     Fake AI and simulated execution adapters/protocols
app/workers/          Bounded coordinator and workflow processing
tests/                API, service, repository, fixture, and server tests
migrations/           Alembic not adopted for the Stage 1 SQLite prototype
../fixtures/          Repository-root synthetic fixture projects
```

## API Endpoints

- `GET /api/v1/csrf`
- `GET /api/v1/fixtures`
- `POST /api/v1/investigations`
- `GET /api/v1/investigations/{id}`
- `GET /api/v1/investigations/{id}/events?after={sequence}`
- `POST /api/v1/investigations/{id}/cancel`
- `GET /api/v1/health`

## Persistence Decision and Limitations

The local adapter uses stdlib `sqlite3` rather than SQLAlchemy. The approved Stage 1 design specifies SQLite and explicit transaction boundaries but does not require an ORM; the current schema is small, local, and directly exercised by integration tests. Avoiding SQLAlchemy removes an unnecessary dependency without changing the persistence contract. Reconsider an ORM only if a later approved data model or migration requirement justifies it.

Stage 1 has no authentication, real provider, GitHub integration, target dependency installation, target-code execution, target pytest, or hosted services. The in-process queue is lost on process exit; unfinished persisted investigations become `interrupted` on restart. The fixture catalog is server-owned metadata; source references are not opened or executed by the backend. Fixture/source changes require updating and verifying the manifest digest. Alembic has not been adopted.