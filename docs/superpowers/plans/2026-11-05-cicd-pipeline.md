# Plan: Establish CI/CD Pipeline for Projeto Artemis

## Goal
Implement an automated CI/CD pipeline to ensure code quality and reliability through linting and testing on every push and pull request.

## Proposed Strategy (Adapted from checa-ai)
- **Linting**: Use `ruff` for fast and consistent code style checks.
- **Testing**: Use `pytest` to run unit and integration tests.
- **Containerization**: Use `Docker` to ensure the environment is reproducible across local and CI environments.
- **CI Orchestration**: GitHub Actions for automating the pipeline.

## Implementation Phases
1. **Containerization**: Create a `Dockerfile` that installs system dependencies and Python requirements.
2. **GitHub Actions Setup**:
    - Create `.github/workflows/ci.yml`.
    - Define a `checks` job for Ruff and Unit tests.
    - (Optional) Define an `integration` job if specific external services are added.
3. **Verification**: Push changes and verify that the GH Actions pipeline triggers and passes.

## Success Criteria
- Every push to `main` or PR triggers the CI pipeline.
- Ruff linting must pass.
- All tests in `tests/` must pass.
- The project can be built and run via the Dockerfile.
