# Implementation Guideline

This guideline explains how to keep implementation work split into small,
consistent parts across Python tool projects. It is a shared process document,
not a module status report.

Use it with:

- [Architecture Guideline](ARCHITECTURE_GUIDELINE.md)
- [Project Documentation Guideline](PROJECT_DOCUMENTATION_GUIDELINE.md)
- [Testing Guideline](TESTING_GUIDELINE.md)
- [Tool Engineer](../roles/TOOL_ENGINEER.md)
- [python_tool_engineer.json](../roles/profiles/python_tool_engineer.json)

Project-specific state belongs in each module's local implementation plan, for
example:

```text
src/<module>/docs/IMPLEMENTATION_PLAN.md
```

## Purpose

Implementation documentation has two layers:

- Root guideline: defines the reusable method for keeping work small,
  consistent, reviewable, and documented.
- Module plan: records the current state of one module, including what exists,
  what is missing, and which small parts should be done next.

Do not put module-specific completion status in this root guideline. Link to the
module plan instead.

## Small Part Rules

Each implementation part should be a complete, narrow functional slice.

A good part:

- has one user-visible or maintainer-visible goal
- touches the fewest layers needed to make that goal work
- leaves the module runnable after the change
- includes validation, error handling, or tests appropriate to the risk
- updates the module plan and creates a task report

Avoid parts that only create empty layers, move files without preserving
behavior, or mix unrelated goals such as packaging, UI redesign, and service
refactoring in one change.

## Consistency Checklist

Before starting a part:

1. Read the module's `README.md`, local `docs/IMPLEMENTATION_PLAN.md`, and
   recent `docs/reports/` entries.
2. Identify the affected boundary:
   - entry point
   - CLI parser
   - config model
   - service layer
   - external tool wrapper
   - TUI screens/widgets
   - tests
   - documentation
3. Confirm the part has a clear done state.
4. Check that the proposed filenames, function names, and data model names
   match the module's existing style.

During implementation:

1. Keep business logic out of root scripts and UI widgets.
2. Pass structured config models between layers.
3. Keep external process calls in wrapper classes or functions.
4. Keep validation close to the service or config boundary that owns the rule.
5. Add test doubles instead of requiring real external tools in core tests.
6. Prefer extending existing local patterns over adding new abstractions.

Before finishing:

1. Run checks that match the changed layer.
2. Update the module implementation plan.
3. Add a report in the module's `docs/reports/` directory.
4. Make sure the README still describes the real user workflow.

## Documentation Consistency

Keep these documents in sync:

- `README.md`: user-facing run, install, and usage information.
- `docs/IMPLEMENTATION_PLAN.md`: current module state and next parts.
- `docs/tasks/`: proposed or approved task designs.
- `docs/reports/`: completed work reports with checks and residual risks.
- shared `docs/guidelines/`: reusable rules only.

When a task changes module behavior, update the module plan in the same change.
When a task only changes shared process, update this root guideline and avoid
editing module-specific status unless the module actually changed.

## Report Format

Every completed implementation part should create a report:

```text
docs/reports/report_{timestamp}.md
```

Use a sortable timestamp:

```text
report_2026-06-08_14-30-00.md
```

Each report should include:

- task summary
- files changed
- behavior added or changed
- checks run
- remaining risks or follow-up work

## Recommended Part Sequence

Use this sequence as a default for a new script-to-tool module. The module plan
should mark which parts are complete, partial, or not started.

1. Create a thin CLI wrapper around one focused capability.
2. Split parser, config model, service logic, external wrapper, and entry point.
3. Add a TUI only after CLI and service boundaries are stable.
4. Add tests and test doubles for core behavior.
5. Improve runtime feedback and failure handling.
6. Add configuration and environment checks.
7. Prepare packaging and repeated local use.
8. Harden production behavior, logging, interruption, and overwrite safety.

This sequence is not mandatory. Choose the next smallest part that reduces real
risk for the module.

## Acceptance Standard

A part is complete when:

- the module still runs through its documented entry point
- changed behavior is documented
- appropriate checks were run or the reason they were skipped is recorded
- the module plan reflects the new state
- the task report captures remaining risks
