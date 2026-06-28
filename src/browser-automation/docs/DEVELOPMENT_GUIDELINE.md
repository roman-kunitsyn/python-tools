# Browser Automation Development Guideline

This module follows the shared Python tool process:

- keep the CLI thin
- keep browser orchestration in library modules
- use the browser manager as the boundary for Playwright interactions
- keep extraction and export helpers testable without a live browser when
  possible
- update the README, implementation plan, and report after each implementation
  slice

Shared workspace guidance:

- [Architecture Guideline](../../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../../docs/roles/TOOL_ENGINEER.md)

