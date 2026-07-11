# Documentation Improvements Plan

This file tracks documentation work step by step so agents can keep the repo
docs aligned with the codebase.

## Goal

Make the documentation easy to use for agents and maintainers, with one clear
source of truth for shared rules and module-specific status.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done

## Current Focus

Primary target:

- review and refresh the shared documentation workflow

Secondary targets:

- align module docs with the current project structure
- make reports easier to track with a commit name
- keep Unix-style stdin/stdout/stderr conventions explicit in tool docs

## Work Plan

### Step 1: Review shared docs

- [ ] Read `README.md`
- [ ] Read `docs/guidelines/ARCHITECTURE_GUIDELINE.md`
- [ ] Read `docs/guidelines/IMPLEMENTATION_GUIDELINE.md`
- [ ] Read `docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md`
- [ ] Read `docs/guidelines/TESTING_GUIDELINE.md`
- [ ] Read `docs/roles/TOOL_ENGINEER.md`
- [ ] Read the other role docs and note which ones are still too vague
- [ ] Read `src/dictate/docs/ARCHITECTURE.md`

Done when:

- the main documentation gaps are listed in one place
- the shared doc workflow is clear enough for an agent to follow without
  guessing

### Step 2: Tighten shared documentation rules

- [x] Update `docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md`
- [x] Add Unix-style stdin/stdout/stderr expectations to
  `docs/guidelines/ARCHITECTURE_GUIDELINE.md`
- [x] Decide whether additional shared docs need the same I/O convention
  language

Done when:

- the shared docs describe how to read, update, and keep docs in sync
- the CLI and adapter I/O conventions are explicit

### Step 3: Standardize report tracking

- [x] Define the report fields that every update report should include
- [x] Add `commit_name` to the report convention
- [x] Update any report templates or examples that still omit commit tracking

Done when:

- a report can be reviewed and tied back to a git commit name without extra
  guessing

### Step 4: Refresh module documentation

- [ ] Review each active module README against the real current behavior
- [ ] Update module `docs/IMPLEMENTATION_PLAN.md` files to match current state
- [ ] Update module `docs/DEVELOPMENT_GUIDELINE.md` files where the workflow has
  drifted
- [ ] Update `src/dictate/docs/ARCHITECTURE.md` if the repo-level conventions
  need to be mirrored there

Done when:

- the active module docs describe the current project structure
- stale guidance has been removed or moved into this plan

### Step 5: Close the loop

- [x] Write a documentation report in the appropriate `docs/reports/`
  directory
- [x] Include the changed files, checks performed, risks, and `commit_name`
- [x] Update this plan to reflect completed work

Done when:

- the documentation change is recorded and the plan reflects the new state

## Notes

- Keep this file short enough that it can be read quickly.
- Use it as the working checklist for documentation cleanup.
- If a new doc problem appears, add it here before starting the fix.
