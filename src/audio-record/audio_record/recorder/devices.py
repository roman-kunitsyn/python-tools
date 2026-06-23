import platform
import re
import subprocess

from audio_record.models.device import AudioDevice


class AudioDeviceNotFoundError(ValueError):
    pass


def current_platform() -> str:
    return platform.system().lower()


def get_audio_devices() -> list[AudioDevice]:
    system = current_platform()

    if system == "darwin":
        return _get_avfoundation_devices()

    if system == "windows":
        return _get_dshow_devices()

    if system == "linux":
        return _get_linux_devices()

    return []


def resolve_input_device(device: str | None) -> str:
    system = current_platform()

    if system == "darwin":
        return _resolve_avfoundation_input(device)

    if system == "windows":
        name = device or "default"
        return f"audio={name}" if not name.startswith("audio=") else name

    if system == "linux":
        return device or "default"

    raise AudioDeviceNotFoundError(f"Unsupported platform: {platform.system()}")


def _get_avfoundation_devices() -> list[AudioDevice]:
    output = _run_device_probe(["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""])
    devices: list[AudioDevice] = []
    in_audio_section = False

    for line in output.splitlines():
        if "AVFoundation video devices" in line:
            in_audio_section = False
            continue

        if "AVFoundation audio devices" in line:
            in_audio_section = True
            continue

        if not in_audio_section:
            continue

        match = re.search(r"\[(\d+)\]\s+(.+)$", line)
        if match:
            devices.append(
                AudioDevice(
                    id=match.group(1),
                    name=match.group(2).strip(),
                    platform="darwin",
                )
            )

    return devices


def _resolve_avfoundation_input(device: str | None) -> str:
    if device is None:
        return ":0"

    if device.isdigit():
        return f":{device}"

    for audio_device in _get_avfoundation_devices():
        if device == audio_device.name:
            return f":{audio_device.id}"

    raise AudioDeviceNotFoundError(f"Audio input device not found: {device}")


def _get_dshow_devices() -> list[AudioDevice]:
    output = _run_device_probe(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"])
    devices: list[AudioDevice] = []
    in_audio_section = False

    for line in output.splitlines():
        if "DirectShow audio devices" in line:
            in_audio_section = True
            continue

        if "DirectShow video devices" in line:
            in_audio_section = False
            continue

        if not in_audio_section or "Alternative name" in line:
            continue

        match = re.search(r'"(.+?)"', line)
        if match:
            name = match.group(1)
            devices.append(AudioDevice(id=name, name=name, platform="windows"))

    return devices


def _get_linux_devices() -> list[AudioDevice]:
    output = _run_device_probe(["ffmpeg", "-sources", "pulse"])
    devices: list[AudioDevice] = []

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Auto-detected"):
            continue

        parts = stripped.split(maxsplit=1)
        if parts and "/" in parts[0]:
            device_id = parts[0]
            name = parts[1] if len(parts) > 1 else device_id
            devices.append(AudioDevice(id=device_id, name=name, platform="linux"))

    return devices


def _run_device_probe(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError as error:
        raise AudioDeviceNotFoundError("ffmpeg executable not found") from error

    return "\n".join(part for part in (result.stdout, result.stderr) if part)
