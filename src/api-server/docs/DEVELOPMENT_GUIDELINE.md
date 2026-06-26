# API Server Development Guideline

This module follows the shared Python tool architecture:

- keep the FastAPI layer thin
- translate HTTP input into service calls
- keep external command execution in service or wrapper modules
- reuse the workspace tool behavior instead of duplicating it in routers
- update the README, implementation plan, and report after each implementation task

Use the root project guidelines for shared process rules:

- [Architecture Guideline](../../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../../docs/roles/TOOL_ENGINEER.md)
