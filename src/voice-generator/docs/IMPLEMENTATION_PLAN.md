# voice-generator Implementation Plan

## Current State

Implemented:

- README task specification for the `voice-generator` toolset.
- Local development guideline describing module boundaries and return codes.
- Implementation plan for the module.
- Documentation links from the README to the shared workspace guidelines.
- Package scaffold under `voice_generator`.
- Thin script entry point at `src/voice-generator/voice-generator.py`.
- Shared request, response, provider, and voice metadata models.
- Provider catalog command that lists the planned provider set.
- Environment validation command with `ffmpeg` and directory checks.
- Placeholder generation and benchmark service boundaries.

Not implemented yet:

- Provider backends.
- Voice discovery from real engines.
- Actual audio generation pipeline.
- Benchmark execution against real providers.
- Tests.
- Packaging metadata.

## Module Purpose

`voice-generator` will provide a provider-based text-to-speech toolkit for
local and cloud synthesis engines.

The module should remain focused on generation and orchestration, not on
recording, transcription, or note-taking.

## Planned Structure

```text
src/voice_generator/
    cli.py
    config.py

    models/
        request.py
        response.py
        voice.py

    providers/
        base.py
        macos_say.py
        kokoro.py
        piper.py
        orpheus.py
        elevenlabs.py

    services/
        generator.py
        registry.py
        validator.py
        benchmark.py
        cache.py

    utils/
        audio.py
        files.py
        text.py
```

## Runtime Dependencies

- `ffmpeg` for format conversion when provider-native output needs post-
  processing.
- Provider-specific binaries, model files, or API keys depending on the
  selected engine.

## Remaining Enhancements

- Add the thin CLI entry point and shared request/response models.
- Implement provider interfaces and registry-driven provider selection.
- Add generation, validation, and benchmark service flows.
- Add unit tests around request mapping, registry behavior, and error handling.
- Add integration coverage for local providers and ffmpeg conversion.
- Add packaging metadata once the module shape stabilizes.

## Next Small Parts

1. Create the package scaffold with empty modules and imports.
2. Add the shared config and request/response models.
3. Add the provider base class and registry.
4. Add the generation service and output conversion helpers.
5. Add validation and benchmark commands.
6. Add tests and documentation reports for each implementation slice.

## Documentation Rules

When implementation changes:

1. Update this plan to match the current state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep the provider boundary isolated from CLI presentation code.
