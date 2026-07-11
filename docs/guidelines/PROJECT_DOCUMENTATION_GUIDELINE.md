# Project Documentation Guideline

Use this guideline to keep repository documentation accurate, discoverable, and
easy for agents to follow.

## Purpose

This repository contains several small tools plus shared documentation. The
docs should explain how the project is structured, how to work on it, and how
to keep the docs in sync with the code.

## Who Should Read It

- Tool engineers working on app behavior, structure, or developer experience.
- Technical leads reviewing architecture and repo conventions.
- Testing engineers validating behavior and documenting checks.
- Product owners and other reviewers who need the current project shape.
- Any agent that needs to update README files, plans, reports, or role docs.

## Read Order

When updating documentation, read the shared docs first:

1. `README.md`
2. `docs/guidelines/ARCHITECTURE_GUIDELINE.md`
3. `docs/guidelines/IMPLEMENTATION_GUIDELINE.md`
4. `docs/guidelines/TESTING_GUIDELINE.md`
5. `docs/improvements_plan.md`
6. Relevant module `README.md`
7. Relevant module `docs/DEVELOPMENT_GUIDELINE.md`
8. Relevant module `docs/IMPLEMENTATION_PLAN.md`
9. Relevant module `docs/reports/`
10. Special architecture docs such as `src/dictate/docs/ARCHITECTURE.md`

## Sync Rules

- Update documentation in the same change as the behavior or workflow change.
- Keep shared rules in root guidelines.
- Keep module-specific status in module plans.
- Keep completed work in reports.
- Avoid duplicating the same rule in multiple files unless that makes the docs
  easier for agents to use.

## Required Documentation Updates

When a task changes behavior, check whether these docs need to change:

- `README.md` for user-facing run and usage instructions
- `docs/guidelines/*` for shared rules
- `docs/improvements_plan.md` for active documentation work
- module `docs/IMPLEMENTATION_PLAN.md` for current state and next steps
- module `docs/DEVELOPMENT_GUIDELINE.md` for module-specific workflow rules
- module `docs/reports/` for completed work records

## Report Tracking

Every documentation update should leave a report in the affected module or root
docs area. Reports should include:

- summary
- files changed
- checks or review steps
- remaining risks
- `commit_name` for git tracking

## Agent Guidance

- Read the current docs before editing.
- Keep the language short and direct.
- Prefer one source of truth for each rule.
- When a doc is stale, either update it or mark it for follow-up in the
  improvement plan.
