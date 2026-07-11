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

## Global vs Local Scope

Use the shared docs for reusable rules that apply to every tool:

- architecture shape
- CLI, TUI, service, and wrapper boundaries
- stdin, stdout, stderr, and flag precedence rules
- config precedence rules
- report format and tracking rules
- testing and validation conventions
- role responsibilities

Keep module-local docs for details that only apply to one tool:

- file and folder layout
- command examples and exact flags
- storage formats and session structures
- TUI behavior and keyboard shortcuts
- feature order and implementation slices
- runtime dependencies and platform-specific notes
- module-specific reports and status

If a rule is shared across tools, document the general rule globally and keep
the module doc focused on the local example or exception.

## Global Documentation Targets

The next shared documentation improvements should focus on:

- config conventions
  - config keys should match CLI option names
  - CLI option values override config file values
  - config file values override built-in defaults
- standard tool contract
  - thin entry point
  - CLI parser
  - shared config model
  - service layer
  - external wrapper
  - optional TUI or adapter layer
- report template
  - summary
  - files changed
  - checks run
  - risks
  - `commit_name`
- role responsibility matrix
  - `TOOL_ENGINEER`
  - `TECHNICAL_LEAD`
  - `TESTING_ENGINEER`
  - `PRODUCT_OWNER`
  - `TELEGRAM_ENGINEER`
- global adapter rules
  - adapters stay thin
  - business logic stays in services
  - adapters only translate input and output
- documentation map
  - shared rules in root guidelines
  - module behavior in module implementation plans
  - user-facing usage in module READMEs
  - completed work in reports
- common tool examples
  - pipeline CLI tool
  - TUI-backed tool
  - config-file-backed tool
  - tool with both CLI and TUI modes

Keep these targets in shared docs only when the rule applies to multiple
modules. Keep module-specific examples in the module docs.

## Required Documentation Updates

When a task changes behavior, check whether these docs need to change:

- `README.md` for user-facing run and usage instructions
- `docs/guidelines/*` for shared rules
- `docs/improvements_plan.md` for active documentation work
- module `docs/IMPLEMENTATION_PLAN.md` for current state and next steps
- module `docs/DEVELOPMENT_GUIDELINE.md` for module-specific workflow rules
- module `docs/reports/` for completed work records

## Report Tracking

Every documentation update should leave a report entry in the affected module
or root docs area. Use one hourly report file per folder:

```text
docs/reports/report-YYYY_MM_DD-HH.md
```

If another documentation update happens in the same hour, append the new entry
to the existing file instead of creating a new one.

Reports should include:

- summary
- files changed
- checks or review steps
- remaining risks
- `commit_name` for git tracking
- a full timestamp marker for the report entry

## Agent Guidance

- Read the current docs before editing.
- Keep the language short and direct.
- Prefer one source of truth for each rule.
- When a doc is stale, either update it or mark it for follow-up in the
  improvement plan.
