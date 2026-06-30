from __future__ import annotations

from functools import lru_cache
import json
import re
import wave
from array import array
from pathlib import Path
from typing import Any

from voice_generator.errors import ProviderUnavailableError, ValidationError
from voice_generator.utils.audio import convert_audio_with_ffmpeg, ensure_output_path


class SnacDecoder:
    id = "snac"
    name = "SNAC"

    def decode(self, payload: str, output_path: Path, *, format: str) -> Path:
        tokens = _extract_tokens(payload)
        return self.decode_tokens(tokens, output_path, format=format)

    def decode_tokens(self, tokens: list[int], output_path: Path, *, format: str) -> Path:
        if not tokens:
            raise ValidationError("orpheus runtime did not return any audio tokens")

        model = _load_snac_model()
        codes = _reconstruct_codebooks(tokens)
        with _maybe_torch_inference():
            audio = model.decode(codes)

        output_path = ensure_output_path(output_path)
        temp_wav = output_path if output_path.suffix.lower() == ".wav" else output_path.with_suffix(".wav")
        _write_audio_waveform(audio, temp_wav)

        if temp_wav == output_path:
            return output_path

        convert_audio_with_ffmpeg(temp_wav, output_path, format=format)
        return output_path


def _extract_tokens(payload: str) -> list[int]:
    text = payload.strip()
    if not text:
        return []
    json_tokens = _extract_json_tokens(text)
    if json_tokens is not None:
        return json_tokens
    custom_tokens = [int(match.group(1)) for match in re.finditer(r"<custom_token_(\d+)>", text)]
    if custom_tokens:
        return custom_tokens
    match = re.search(r"\[[^\]]+\]", text)
    if match is not None:
        text = match.group(0).strip("[]")
    tokens: list[int] = []
    for chunk in re.split(r"[\s,]+", text):
        if not chunk:
            continue
        try:
            tokens.append(int(chunk))
        except ValueError:
            continue
    return tokens


def _extract_json_tokens(text: str) -> list[int] | None:
    if not text.startswith("{") and not text.startswith("["):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        return [_coerce_int(item) for item in data if _coerce_int(item) is not None]
    if isinstance(data, dict):
        for key in ("audio_tokens", "tokens", "token_ids", "snac_tokens"):
            value = data.get(key)
            if isinstance(value, list):
                tokens = [_coerce_int(item) for item in value]
                return [token for token in tokens if token is not None]
    return None


def _coerce_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _reconstruct_codebooks(tokens: list[int]) -> list[Any]:
    codebook_count = 4
    codebooks: list[list[int]] = [[] for _ in range(codebook_count)]
    strides = [8, 4, 2, 1]
    index = 0
    step = 0
    while index < len(tokens):
        for codebook_index, stride in enumerate(strides):
            if step % stride != 0:
                continue
            if index >= len(tokens):
                break
            codebooks[codebook_index].append(tokens[index])
            index += 1
        step += 1
    return [_tensor_from_codes(codebook) for codebook in codebooks]


def _tensor_from_codes(codes: list[int]) -> Any:
    try:
        import torch

        return torch.tensor([codes], dtype=torch.long)
    except Exception as error:  # pragma: no cover - dependency error path
        raise ProviderUnavailableError(
            "snac decoding requires the optional 'torch' dependency"
        ) from error


@lru_cache(maxsize=1)
def _load_snac_model() -> Any:
    try:
        import torch
        from snac import SNAC
    except Exception as error:  # pragma: no cover - dependency error path
        raise ProviderUnavailableError(
            "snac decoding requires the optional 'snac' and 'torch' dependencies"
        ) from error

    model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
    model = model.to(torch.device("cpu"))
    model.eval()
    return model


class _maybe_torch_inference:
    def __enter__(self) -> None:
        try:
            import torch

            self._ctx = torch.inference_mode()
            self._ctx.__enter__()
        except Exception:
            self._ctx = None

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._ctx is not None:
            self._ctx.__exit__(exc_type, exc, tb)


def _write_audio_waveform(audio: Any, output_path: Path) -> None:
    samples = _flatten_audio(audio)
    pcm = array("h")
    for sample in samples:
        clamped = max(-1.0, min(1.0, float(sample)))
        pcm.append(int(clamped * 32767))

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(pcm.tobytes())


def _flatten_audio(audio: Any) -> list[float]:
    candidate = audio
    for method in ("detach", "cpu", "squeeze"):
        if hasattr(candidate, method):
            candidate = getattr(candidate, method)()
    if hasattr(candidate, "tolist"):
        values = candidate.tolist()
    else:
        values = candidate
    while isinstance(values, list) and values and isinstance(values[0], list):
        values = values[0]
    if not isinstance(values, list):
        values = [values]
    return [float(value) for value in values]
