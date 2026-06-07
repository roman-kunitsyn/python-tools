import re
import subprocess
from pathlib import Path


class FfmpegWrapper:
    def list_avfoundation_devices(self) -> str:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
        )
        return result.stderr

    def find_audio_device_code(self, device_name: str) -> int:
        device_output = self.list_avfoundation_devices()

        for line in device_output.splitlines():
            if device_name in line:
                match = re.search(r"\[(\d+)\]", line)
                if match:
                    return int(match.group(1))

        raise ValueError(f"Audio input device not found: {device_name}")

    def record_audio(
        self,
        device_code: int,
        output_file: Path,
        verbose: bool = False,
    ) -> None:
        command = [
            "ffmpeg",
            "-f",
            "avfoundation",
            "-i",
            f":{device_code}",
            str(output_file),
        ]

        if verbose:
            print(f"Running: {' '.join(command)}")

        subprocess.run(command, check=True)
