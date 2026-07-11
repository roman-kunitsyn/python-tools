you are
./docs/roles/TOOL_ENGINEER.md

Task

Review the repository documentation, identify drift, and update the core docs so
they match the current codebase and the way agents should work in this repo.

Primary goals

- Make the documentation easy to follow for agents.
- Keep shared docs aligned with the real project structure.
- Establish Unix-style tool conventions: stdin for input, stdout for results,
  stderr for diagnostics and errors.
- Standardize task reports so they also include a `commit_name` field for git
  tracking.
- Treat `TOOL_ENGINEER` as the primary role for this repository until the other
  roles are fully defined.

Docs to review first

- `docs/guidelines/ARCHITECTURE_GUIDELINE.md`
- `docs/guidelines/IMPLEMENTATION_GUIDELINE.md`
- `docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md`
- `docs/guidelines/TESTING_GUIDELINE.md`
- `docs/guidelines/UX_UI_DESIGN_GUIDELINE.md`
- `docs/guidelines/INVESTIGATION_REVIEW_PLANNING_PROTOTYPING.md`
- `docs/guidelines/TELEGRAM_BOT_GUIDELINE.md`
- `docs/roles/TOOL_ENGINEER.md`
- `docs/roles/PRODUCT_OWNER.md`
- `docs/roles/TECHNICAL_LEAD.md`
- `docs/roles/TESTING_ENGINEER.md`
- `docs/roles/TELEGRAM_ENGINEER.md`
- `docs/roles/UI_UX_DESIGNER.md`
- `docs/roles/profiles/*.json`
- `docs/improvements_plan.md`
- `src/dictate/docs/ARCHITECTURE.md`

Also review the active module docs when they are affected by the documentation
change:

- `README.md`
- `src/*/README.md`
- `src/*/docs/DEVELOPMENT_GUIDELINE.md`
- `src/*/docs/IMPLEMENTATION_PLAN.md`
- `src/*/docs/reports/`

What to update

1. Update the shared documentation rules first.
2. Make the root docs describe how agents should read, update, and keep docs in
   sync.
3. Add or clarify Unix-style stdin/stdout/stderr behavior where it matters for
   tools and adapters.
4. Update module docs that are stale or that conflict with the shared rules.
5. Refresh `docs/improvements_plan.md` so it tracks documentation work step by
   step.
6. Add a report for the documentation update with the commit tracking name.

Report requirements

- Include a short summary of what changed.
- List the files changed.
- List the checks or review steps performed.
- Call out remaining documentation risks or follow-up work.
- Include `commit_name: <name>` so the git commit can be tracked later.
- Write the report as an hourly entry file under `docs/reports/` using the
  current-hour file name.
- If another report already exists for the same hour, append a new entry to
  that file instead of creating a new file.
- Include a full timestamp marker in the report entry body.

Working rule

- Prefer concise, direct instructions.
- Keep the docs specific to this repo.
- Avoid duplicating guidance across files unless the duplication is deliberate
  and keeps the docs easier for agents to use.
