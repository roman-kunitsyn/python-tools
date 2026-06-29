# Task: Implement Local Voice SDK

## Goal

Implement a production-ready Python toolkit for Text-to-Speech (TTS) that provides a unified interface for multiple speech synthesis engines.

The toolkit must support:

- Local inference
- Cloud providers
- CLI usage
- Python SDK
- Future TUI integration
- Batch generation
- Voice catalogs
- Streaming architecture

The implementation must be modular so that adding a new provider requires implementing only a provider interface.

---

# Technology Stack

- Python 3.13+
- uv
- Typer
- Rich
- Textual (future)
- Pydantic v2
- ffmpeg
- pathlib
- asyncio

No Docker.

No GUI.

CLI-first architecture.

---

# Project Structure

```text
voice-sdk/

README.md
pyproject.toml

src/voice/

    cli.py
    config.py

    providers/
        base.py

        macos_say.py
        kokoro.py
        piper.py
        orpheus.py
        elevenlabs.py

    models/

        voice.py
        request.py
        response.py

    services/

        generator.py
        registry.py
        cache.py

    utils/

        audio.py
        text.py
        files.py

tests/
docs/
```

---

# Provider Interface

Every provider must implement:

```python
class VoiceProvider:

    id: str
    name: str

    def list_voices(self)

    def supports_streaming(self)

    def supports_ssml(self)

    def generate(request)

    def validate()
```

No provider-specific logic outside provider modules.

---

# Supported Providers

## macOS Say

Purpose:

Fast offline synthesis using the native macOS `say` command.

Requirements:

- enumerate voices
- generate AIFF
- optional WAV conversion
- speech rate
- pitch (if supported)

---

## Kokoro

Requirements:

- local inference
- voice selection
- CPU support
- optional GPU
- SSML support (if available)

---

## Piper

Requirements:

- local inference
- model discovery
- voice management

---

## Orpheus

Initial implementation target.

Requirements:

Support:

- GGUF model
- llama.cpp backend
- local inference
- SNAC decoding
- emotional tags
- voice selection

Must NOT depend on:

- LM Studio
- Docker

The implementation should be structured so different runtimes (llama.cpp, future Ollama integration, etc.) can be swapped without changing the public API.

Research Tasks:

- investigate official prompt format
- investigate voice token injection
- investigate custom token generation
- integrate SNAC decoder
- generate WAV

---

## ElevenLabs

Cloud implementation.

Support:

- API key
- streaming
- voice list
- emotion settings

---

# Request Model

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

---

# Response Model

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

# CLI

Commands:

```bash
voice list

voice providers

voice voices

voice generate

voice benchmark

voice validate
```

Examples:

```bash
voice generate \
    --provider orpheus \
    --voice tara \
    --text "Hello Roman"

voice generate \
    --provider kokoro \
    --voice af_heart \
    --input article.md \
    --output article.wav

voice generate \
    --provider macos \
    --voice Samantha \
    --text "Hello"
```

---

# Configuration

Support:

```yaml
default_provider:
default_voice:
cache_directory:
models_directory:
ffmpeg_path:
```

---

# Output Formats

Support:

- wav
- aiff
- mp3 (ffmpeg)
- flac

---

# Voice Registry

Implement:

```python
voice list
```

Returns:

Provider

Voice ID

Language

Gender

Tags

Installed

---

# Benchmark Command

Measure:

- loading time
- inference speed
- generation duration
- realtime factor
- output size

---

# Validation Command

Verify:

- ffmpeg
- provider binaries
- models
- API keys
- writable output directories

---

# Error Handling

Never crash.

Return structured exceptions.

Examples:

MissingModelError

ProviderUnavailableError

VoiceNotFoundError

AudioGenerationError

---

# Future Extensions

The architecture must support adding:

- Suno
- Udio
- Fish Speech
- Dia
- XTTS
- OpenVoice
- Voice cloning
- Speech-to-Speech
- Singing synthesis
- Multi-speaker dialogue

without changing the public API.

---

# Deliverables

- Fully typed Python package
- CLI
- Provider abstraction
- Unit tests
- Integration tests
- Documentation
- Example configurations
- Example scripts
- Benchmark report
- Developer documentation
- Architecture document

```

```
