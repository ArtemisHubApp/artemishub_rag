# Plan: CI/CD Pipeline for Quality Assurance

## Context
The project lacks automated quality gates, leading to regressions and linting errors being pushed to main.

## Goals
1. **Automated Linting**: Use Ruff for extremely fast linting and formatting.
2. **Deterministic Testing**: Run pytest across multiple Python versions (3.11, 3.14).
3. **Consistency**: Ensure the same environment in CI as in development.
4. **Fast Feedback**: The pipeline should run in under 3 minutes.

## Proposed Stack
- **GitHub Actions**: Workflow triggered on push to main and pull requests.
- **Ruff**: For linting (E, F, I, UP rules) and formatting.
- **Pytest**: For unit and integration tests.
- **Docker**: Use a standard Python image to avoid environment drift.

## Success Criteria
- Every push to main triggers a CI run.
- Ruff check must pass (zero errors).
- Pytest must pass all tests.
- CI fails if any check fails, preventing unstable code from being merged.
