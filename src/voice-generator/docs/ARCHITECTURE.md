# voice-generator Architecture

## Overview

`voice-generator` is a provider-based text-to-speech toolkit. The public API
stays centered on requests, results, and provider selection. Provider-specific
runtime details stay inside provider modules and their internal helpers.

## Layering

- `cli.py` parses user input and builds a shared request model.
- `config.py` loads defaults and applies environment overrides.
- `models/` contains request, audio result, and voice metadata models.
- `providers/` exposes public provider implementations.
- `runtimes/` contains internal Orpheus runtime implementations.
- `decoders/` contains internal audio-token decoding helpers.
- `services/` coordinates registry, generation, validation, and benchmark
  flows.
- `utils/` holds reusable file, text, and audio helpers.

## Orpheus Flow

The Orpheus provider is runtime-driven:

1. The provider selects a runtime implementation from configuration.
2. The runtime builds the inference prompt.
3. The runtime executes the configured executable.
4. The runtime captures the runtime output.
5. The runtime extracts `<custom_token_xxxxx>` audio tokens.
6. The decoder converts the tokens to WAV.
7. The runtime returns an `AudioResult`.

The CLI does not expose internal staging commands or decoder-specific flags.

## Runtime Selection

Supported runtime identifiers:

- `llama-cpp`
- `official-python`

Future runtimes can be added by implementing a new runtime class and wiring
it into the runtime registry.

## Decoder Selection

Supported decoder identifiers:

- `snac`

Decoder selection is intentionally internal. The public CLI only exposes the
runtime, model, executable, and decoder values needed to configure Orpheus.
The current SNAC implementation expects `snac` and `torch` to be available at
runtime.
