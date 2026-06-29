# voice-generator Development Guideline

## Responsibility

`voice-generator` turns text into audio and exposes a provider-based TTS
toolkit.

It should stay focused on generation and provider orchestration:

- text input to audio output
- provider selection and voice discovery
- validation of local binaries, models, and API access
- benchmark and diagnostics flows
- future TUI integration on top of the same service layer

It must not expand into transcription, note taking, or recording. Those are
separate tools in this workspace.

## Architecture

- `voice-generator.py` should be a thin script entry point.
- `voice_generator.cli` owns argument parsing and command dispatch.
- `voice_generator.config` owns the shared config model and config loading.
- `voice_generator.models` contains request, response, and voice metadata
  models.
- `voice_generator.providers` owns provider-specific implementations.
- `voice_generator.services` owns generation, registry, validation, caching,
  and benchmarking logic.
- `voice_generator.utils` owns reusable file, audio, and text helpers.

## Boundary Rules

- Keep provider-specific branching out of the CLI.
- Keep runtime adapters and external command wrappers inside provider or
  service modules.
- Do not let UI state leak into services.
- Do not pass raw argparse or widget objects into the provider layer.
- Keep audio conversion rules in shared utilities unless a provider needs a
  special case.

## Provider Rules

- Every provider should implement the same public interface shape.
- Provider modules may encapsulate runtime-specific quirks, but they should not
  change the public request or response model.
- Registry and validation logic should depend on provider capabilities, not
  hard-coded command-line branching.
- If a provider needs subprocess execution, build commands as `list[str]` and
  keep shell invocation out of the public API.
- macOS Say should stay a thin wrapper over the native `say` tool.
- Orpheus should stay a configurable runtime adapter so the backend command
  and model path can be swapped without changing the CLI or request model.

## CLI Rules

- The CLI should map user input to the shared request model.
- Keep CLI validation limited to argument-level checks.
- Generate output paths and format decisions in services, not in command
  handlers.
- Use structured errors and stable exit codes instead of uncaught exceptions.

## Long-Running Work

- Generation, validation, and benchmarking may be slow.
- Run long tasks behind service boundaries so a future TUI can call them from a
  worker or background task.
- Do not block the CLI with unrelated preloading or expensive discovery unless
  it is necessary for the requested command.

## Output Rules

- Prefer explicit output files for generated audio.
- Keep conversion logic deterministic.
- Preserve provider metadata in responses where useful for downstream tools.
- Treat temporary files as internal implementation details unless the user
  explicitly asks for them.

## Error Handling

- Raise typed exceptions for expected failures.
- Keep user-facing messages actionable.
- Do not leak raw subprocess traces or provider internals unless debug mode is
  enabled.
- Preserve a consistent mapping from exception type to exit code.

## Return Codes

- `0`: success
- `1`: validation or user input error
- `2`: provider or generation failure
- `3`: missing dependency, unavailable model, or environment error
- `130`: interrupted by user

## Documentation Rules

- Keep the README aligned with the actual CLI and package layout.
- Update the local development guideline when architecture boundaries change.
- Add or refresh module reports after implementation slices, not in the
  guideline itself.
