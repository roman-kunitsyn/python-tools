# Task: Implement `voice-generator` Toolset

## Objective

Implement a production-ready Python toolkit for text-to-speech generation.

The toolset should provide:

- a CLI for day-to-day use
- a Python SDK for other tools in this workspace
- a provider abstraction for local and cloud engines
- batch generation
- voice discovery and validation
- benchmark and diagnostics commands
- a clean path for future TUI integration
- default timestamped output files under `./logs/voice-generator/`

This repository entry is the project specification. The first implementation
slice now includes the package scaffold, shared models, provider catalog, and a
thin CLI boundary.

---

## Scope

The toolset is responsible for:

- turning text into audio files
- selecting a provider and voice
- validating local dependencies and API credentials
- reporting generation metadata
- keeping provider-specific logic isolated

The toolset is not responsible for:

- transcription
- note taking
- audio recording
- speech-to-speech conversion
- GUI applications
- Docker packaging

---

## Technology Stack

- Python 3.13+
- uv
- Typer or argparse for CLI entry points
- Rich for terminal output
- Pydantic v2 for request and response models
- pathlib for file handling
- subprocess for external command wrappers
- asyncio for streaming and long-running tasks
- ffmpeg for output conversion when needed

---

## Design Principles

- One tool should have one primary responsibility.
- CLI code should stay thin.
- Shared behavior should live in service modules.
- Provider-specific logic should stay inside provider modules.
- All public operations should return explicit models or structured errors.
- Adding a new provider should require only a new provider implementation and registry entry.

---

## Proposed Package Layout

```text
voice-generator/
README.md
pyproject.toml

src/voice_generator/
    __init__.py
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

tests/
docs/
```

---

## Provider Interface

Each provider should implement a common interface.

```python
class VoiceProvider:
    id: str
    name: str

    def list_voices(self)
    def supports_streaming(self)
    def supports_ssml(self)
    def generate(self, request)
    def validate(self)
```

Rules:

- provider selection happens through the registry
- generation behavior stays inside the provider and service layers
- no provider-specific branching should leak into the CLI

---

## Supported Providers

### macOS Say

Purpose:

- fast offline synthesis using the native `say` command

Implemented support:

- voice enumeration
- WAV output by default
- AIFF output when requested
- optional WAV conversion from the AIFF synthesis output
- speech rate control
- pitch control is not supported by `say`

### Kokoro

Expected support:

- local inference
- voice selection
- CPU support
- optional GPU support
- SSML support if available

### Piper

Expected support:

- local inference
- model discovery
- voice management

### Orpheus

Initial implementation target for the local voice pipeline.

Implemented as a configurable runtime adapter:

- local inference through a user-supplied runtime command
- GGUF model validation
- voice selection
- voice catalog loading
- runtime command templating

Constraints:

- do not depend on LM Studio
- do not depend on Docker
- keep runtime adapters swappable without changing the public API

Configuration:

- `orpheus_command`
- `orpheus_model_path`
- `orpheus_voice_catalog`
- `orpheus_command_template`

Runtime-specific details such as the exact prompt format, SNAC decoding, and
emotion token handling stay inside the configured backend command.

### ElevenLabs

Cloud provider support.

Expected support:

- API key handling
- streaming
- voice list retrieval
- emotion settings

---

## Request Model

```python
VoiceRequest

text
voice
language
provider
emotion
speed
pitch
temperature
seed
stream
output_path
```

Suggested extensions:

- `format`
- `sample_rate`
- `normalize_audio`
- `metadata`

---

## Response Model

```python
VoiceResponse

provider
voice
duration
sample_rate
output_file
generation_time
metadata
```

---

## CLI

Planned commands:

```bash
voice providers
voice voices
voice generate
voice benchmark
voice validate
```

Suggested examples:

```bash
voice generate \
  --provider orpheus \
  --voice tara \
  --text "Hello Roman"
```

```bash
voice generate \
  --provider kokoro \
  --voice af_heart \
  --input article.md \
  --output article.wav
```

```bash
voice generate \
  --provider macos \
  --voice Samantha \
  --text "Hello"

voice generate \
  --provider orpheus \
  --orpheus-command orpheus-runner \
  --orpheus-model-path ./models/orpheus.gguf \
  --text "Hello Roman"
```

---

## Configuration

Support a simple config file for defaults.

```yaml
default_provider:
default_voice:
cache_directory:
models_directory:
ffmpeg_path:
orpheus_command:
orpheus_model_path:
orpheus_voice_catalog:
orpheus_command_template:
```

Recommended config behavior:

- CLI flags override config defaults
- environment variables can override secrets and API keys
- config loading should be explicit and predictable

---

## Output Formats

Planned output formats:

- wav
- aiff
- mp3
- flac

Notes:

- WAV is the standard output format.
- If `--output` is omitted, the tool writes to
  `./logs/voice-generator/{YYYY_MM_DD-HH_MM_SS}.wav`.
- `mp3` and `flac` may require ffmpeg conversion
- provider-native formats can be converted in a shared utility layer

---

## Voice Registry

The `voice list` command should return:

- provider
- voice ID
- language
- gender
- tags
- installed status

This output should be usable both for human inspection and future machine parsing.

---

## Benchmark Command

The benchmark command should measure:

- loading time
- inference speed
- generation duration
- realtime factor
- output size

---

## Validation Command

The validation command should verify:

- ffmpeg availability
- provider binaries
- model availability
- API keys
- writable output directories

---

## Error Handling

The toolset should never crash on user-facing failures.

Use structured exceptions such as:

- `MissingModelError`
- `ProviderUnavailableError`
- `VoiceNotFoundError`
- `AudioGenerationError`

Errors should be surfaced with actionable messages and non-zero exit codes.

---

## Future Extensions

The architecture should allow future support for:

- Suno
- Udio
- Fish Speech
- Dia
- XTTS
- OpenVoice
- voice cloning
- speech-to-speech
- singing synthesis
- multi-speaker dialogue

These should be add-on capabilities, not changes to the public API.

---

## Documentation Deliverables

Planned documentation for this toolset:

- project README
- architecture document
- development guideline
- example configs
- example scripts
- benchmark report
- developer guide
- test strategy

---

## Implementation Deliverables

- fully typed Python package
- CLI
- provider abstraction
- unit tests
- integration tests
- documentation
- example configurations
- example scripts
- benchmark report
- developer documentation
- architecture document

---

## Status

Implemented in the first slice:

- package scaffold under `voice_generator`
- thin `voice-generator` script entry point
- macOS Say provider backend
- Orpheus configurable runtime adapter
- provider catalog command
- voice catalog command
- environment validation command
- generation command through provider dispatch
- shared request, response, voice, and provider metadata models
- config loader for flat key-value files
- generation and benchmark service boundaries

---

## Documentation

- [Development Guideline](docs/DEVELOPMENT_GUIDELINE.md): local rules for building `voice-generator`.
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md): current module state and next parts.
- [Architecture Guideline](../../docs/guidelines/ARCHITECTURE_GUIDELINE.md): shared Python tool architecture.
- [Implementation Guideline](../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md): shared implementation process.
