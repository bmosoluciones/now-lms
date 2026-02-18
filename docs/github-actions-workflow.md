# GitHub Actions Workflow Chain Documentation

## Overview

This document describes the GitHub Actions workflow configuration for the NOW LMS project. The workflows are designed to create a sequential execution chain that ensures quality gates are passed before deployment.

## Workflow Files

1. **python.yml** - CI (Continuous Integration)
2. **release.yml** - Release Validation
3. **pypi.yml** - Publish to PyPI

## Workflow Chain

### On `development` Branch

```
Push/PR to development
         ↓
    ┌────────┐
    │   CI   │ ← python.yml
    └────────┘
```

**Purpose**: Run basic tests to ensure code quality during development.

### On `main` Branch - Push Event (e.g., Merge)

```
Push to main
         ↓
    ┌────────┐
    │   CI   │ ← python.yml
    └────────┘
         ↓ (if successful)
    ┌──────────────────────┐
    │ Release Validation   │ ← release.yml
    └──────────────────────┘
         ↓ (if successful)
    ┌──────────────────────┐
    │ Publish to PyPI      │ ← pypi.yml
    └──────────────────────┘
```

**Purpose**: Sequential quality gates before publishing to PyPI.

### On `main` Branch - Pull Request

```
PR to main
         ↓
    ┌────────────────┐
    │                │
    ↓                ↓
┌────────┐    ┌──────────────────────┐
│   CI   │    │ Release Validation   │
└────────┘    └──────────────────────┘
```

**Purpose**: Validate both basic tests and comprehensive tests before merging.

## Workflow Details

### 1. CI (python.yml)

**Triggers:**
- Push to `main` or `development`
- Pull requests to `main` or `development`

**What it does:**
- Tests with Python 3.11, 3.12, 3.13, 3.14
- Runs pytest
- Builds and validates Python package
- Checks package with twine

**Matrix strategy**: Tests run in parallel for each Python version.

### 2. Release Validation (release.yml)

**Triggers:**
- Pull requests to `main` (for validation)
- After CI workflow completes successfully on `main` (for push events)

**What it does:**
- Tests with SQLite (in-memory)
- Tests with PostgreSQL + pg8000
- Tests with MySQL
- Runs linting (flake8, mypy, ruff, pylint)
- Uploads coverage to Codecov

**Important:** 
- Only runs if CI workflow was successful (for workflow_run trigger)
- Checks out the correct commit using `workflow_run.head_sha`

### 3. Publish to PyPI (pypi.yml)

**Triggers:**
- After Release Validation workflow completes successfully on `main`

**What it does:**
- Builds source distribution and wheel
- Publishes to PyPI using trusted publishing

**Important:**
- Uses `continue-on-error: true` to allow graceful failure when version hasn't changed
- Only runs if Release Validation was successful
- Checks out the correct commit using `workflow_run.head_sha`
- Requires PyPI environment protection

## Key Configuration Details

### Workflow Run Triggers

The `workflow_run` trigger is used to create dependencies between workflows:

```yaml
on:
  workflow_run:
    workflows: ["CI"]  # Name of the workflow to wait for
    types:
      - completed
    branches:
      - main
```

### Success Conditions

Workflows check if the previous workflow was successful:

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

### Correct Commit Checkout

To ensure the correct code is tested and deployed:

```yaml
- uses: actions/checkout@v4
  with:
    ref: ${{ github.event.workflow_run.head_sha || github.sha }}
```

## Workflow Behavior Summary

| Workflow           | File         | `development` (push/PR) | `main` (push) | `main` (PR) |
|--------------------|--------------|-------------------------|---------------|-------------|
| CI                 | python.yml   | ✓ Runs                  | ✓ Runs        | ✓ Runs      |
| Release Validation | release.yml  | ✗ Does not run          | ✓ After CI    | ✓ Runs      |
| Publish to PyPI    | pypi.yml     | ✗ Does not run          | ✓ After Release | ✗ Does not run |

## Expected Scenarios

### Scenario 1: Development Work
- Push to `development` → Only CI runs
- PR to `development` → Only CI runs

### Scenario 2: Pull Request to Main
- Open PR to `main` → Both CI and Release Validation run in parallel
- Both must pass for the PR to be mergeable

### Scenario 3: Merge to Main (with version bump)
1. CI runs on the merge commit
2. If CI passes → Release Validation runs
3. If Release Validation passes → PyPI Publish runs
4. Package is published successfully to PyPI

### Scenario 4: Merge to Main (without version bump)
1. CI runs on the merge commit
2. If CI passes → Release Validation runs
3. If Release Validation passes → PyPI Publish runs
4. PyPI Publish fails (package already exists) but workflow succeeds due to `continue-on-error: true`

### Scenario 5: Hot Fix to Main
Same as Scenario 3 or 4, depending on whether version was bumped.

## Version Management

The version is defined in `now_lms/version/__init__.py`:

```python
MAYOR = "1"
MENOR = "2"
PATCH = "3"
VERSION = MAYOR + "." + MENOR + "." + PATCH
```

To trigger a PyPI release, increment one of these values before merging to `main`.

## Environment Protection

The PyPI workflow uses GitHub environment protection:
- **Environment name**: `pypi`
- **URL**: https://pypi.org/p/now-lms
- **Permissions**: `id-token: write` (for OIDC trusted publishing)

This requires proper configuration in the GitHub repository settings.

## Monitoring Workflows

### Using GitHub Web UI
1. Go to: https://github.com/williamjmorenor/now-lms/actions
2. View workflow runs and their status
3. Click on a run to see the execution graph and logs

### Using GitHub CLI

```bash
# List recent workflow runs
gh run list --limit 20

# Watch a specific run
gh run watch <run-id>

# View logs for a run
gh run view <run-id> --log

# List workflows
gh workflow list
```

## Troubleshooting

### Workflow Not Running
- Check that the previous workflow completed successfully
- Verify the workflow name matches exactly (case-sensitive)
- Ensure the branch name matches the trigger configuration

### Wrong Code Checked Out
- Verify `workflow_run.head_sha` is used in checkout action
- Check that the workflow_run trigger is properly configured

### PyPI Publish Always Failing
- If version wasn't bumped, this is expected (continue-on-error: true)
- If version was bumped, check PyPI credentials and environment configuration
- Verify the package build completed successfully

### Release Validation Doesn't Run After CI
- Check if CI workflow actually succeeded
- Verify the workflow name in workflow_run trigger matches "CI"
- Check GitHub Actions logs for any workflow_run events

## References

- [GitHub Actions: workflow_run event](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
- [GitHub Actions: contexts](https://docs.github.com/en/actions/learn-github-actions/contexts)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
