import re
import subprocess
import threading
from pathlib import Path


class FfmpegWrapper:
    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._stop_requested = False
        self._lock = threading.Lock()

    def clear_stop_request(self) -> None:
        with self._lock:
            self._stop_requested = False

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

        process = subprocess.Popen(command, stdin=subprocess.PIPE)

        with self._lock:
            self._process = process
            stop_requested = self._stop_requested

        if stop_requested:
            self.stop_recording()

        try:
            return_code = process.wait()
        except KeyboardInterrupt:
            self.stop_recording()
            raise
        finally:
            with self._lock:
                if self._process is process:
                    self._process = None

        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    def stop_recording(self) -> None:
        with self._lock:
            self._stop_requested = True
            process = self._process

        if process is None or process.poll() is not None:
            return

        if process.stdin is not None:
            try:
                process.stdin.write(b"q")
                process.stdin.flush()
                return
            except BrokenPipeError:
                pass

        process.terminate()
