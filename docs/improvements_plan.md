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

## Global Docs Expansion

The shared documentation now needs one more pass to make the reusable rules
obvious to agents:

- add a simple documentation map that says where global vs local information
  belongs
- keep the config precedence rule explicit in the shared architecture docs
- document the standard tool contract in one place
- define a lightweight role responsibility matrix
- give one or two canonical tool examples so new modules have a model to copy
- keep the report template and `commit_name` rule easy to find

Done when:

- a new agent can tell where to document a rule without guessing
- the shared docs describe the common tool shape and the core precedence rules

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

### Step 2b: Expand global docs coverage

- [x] Add the global documentation targets to
  `docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md`
- [ ] Add a concise documentation map to any other root doc that needs one
- [x] Add a lightweight role responsibility matrix if the role docs remain too
  vague
- [ ] Add canonical tool examples to the shared architecture docs if the
  current examples are still too generic
- [ ] Re-check the report template after the new global doc targets are in
  place

Done when:

- the root docs say what belongs globally and what stays local
- the shared examples are concrete enough for new modules to follow

### Step 3: Standardize report tracking

- [x] Define the report fields that every update report should include
- [x] Add `commit_name` to the report convention
- [x] Update any report templates or examples that still omit commit tracking
- [x] Switch report files to one hourly file per folder with appended entries
  inside the same hour

Done when:

- a report can be reviewed and tied back to a git commit name without extra
  guessing
- report files stay grouped by hour instead of one file per change

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
