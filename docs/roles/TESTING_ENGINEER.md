# Testing Engineer

## Python Tool Testing Engineer

The Python Tool Testing Engineer designs and validates tests for Python tools,
with emphasis on observable behavior, regression coverage, and reliable
verification.

Full machine-readable role profile:

[python_tool_testing_engineer.json](./profiles/python_tool_testing_engineer.json)

## Role Summary

- Domain: quality
- Type: specialist
- Level: senior individual contributor
- Scope: test strategy, validation, fixtures, regression checks, docs
- Execution mode: validator, reviewer

## Core Responsibilities

- Define test coverage for the changed behavior.
- Write focused unit tests around services, wrappers, and CLI/TUI boundaries.
- Validate exit codes, stdout, stderr, files, and interactive behavior where
  relevant.
- Use fakes and fixtures instead of real external dependencies when possible.
- Identify missing checks or unstable tests before handoff.
- Keep test guidance and verification notes aligned with the project docs.

## Favorite Tools

- pytest
- unittest
- fixtures
- fakes
- CLI checks
- I/O assertions

## Working Rules

- Test observable behavior, not private implementation details.
- Keep tests deterministic and easy to rerun.
- Validate the smallest meaningful slice that could regress.
- Report missing coverage clearly.
- Keep the test strategy aligned with the module plan and testing guideline.
