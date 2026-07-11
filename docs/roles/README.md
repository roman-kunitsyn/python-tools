# Roles

This folder defines the project roles used to plan, review, build, test, and
shape Python tools in this repository.

Use the role docs when you need to know who owns a task or which viewpoint
should review a change.

## Role Summary

- [Tool Engineer](./TOOL_ENGINEER.md): builds focused CLI/TUI tools with thin
  entry points, shared config models, service layers, and external wrappers.
- [Technical Lead](./TECHNICAL_LEAD.md): reviews architecture, splits work into
  small slices, and manages delivery risk.
- [Testing Engineer](./TESTING_ENGINEER.md): defines and validates test
  coverage, focusing on observable behavior and regression safety.
- [Product Owner](./PRODUCT_OWNER.md): prioritizes work, clarifies user value,
  and defines acceptance criteria.
- [UI/UX Designer](./UI_UX_DESIGNER.md): designs keyboard-first CLI/TUI
  interactions, layouts, states, and navigation.
- [Telegram Engineer](./TELEGRAM_ENGINEER.md): builds Telegram bot workflows
  with thin handlers, service layers, and asynchronous media handling.

## Machine-Readable Profiles

- [Tool Engineer profile](./profiles/python_tool_engineer.json)
- [Technical Lead profile](./profiles/python_tool_technical_lead.json)
- [Testing Engineer profile](./profiles/python_tool_testing_engineer.json)
- [Product Owner profile](./profiles/python_tool_product_owner.json)
- [UI/UX Designer profile](./profiles/python_tool_ui_ux_designer.json)
- [Telegram Engineer profile](./profiles/python_telegram_engineer.json)

## How To Use These Roles

- Start with `Tool Engineer` for implementation work on Python tool modules.
- Use `Technical Lead` when a task needs scope control, architecture review, or
  a smaller implementation slice.
- Use `Testing Engineer` when you need a verification plan or test coverage
  review.
- Use `Product Owner` when you need prioritization, acceptance criteria, or
  user-facing scope decisions.
- Use `UI/UX Designer` when the task changes CLI or TUI navigation, layout, or
  keyboard flow.
- Use `Telegram Engineer` for Telegram-specific workflows and bot behavior.

## Shared Guidance

- Shared architecture rules live in `../guidelines/`.
- Shared implementation rules live in `../guidelines/IMPLEMENTATION_GUIDELINE.md`.
- Module-specific behavior stays in module docs.
- Completed work goes in reports.
