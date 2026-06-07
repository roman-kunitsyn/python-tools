import subprocess
from pathlib import Path
import argparse

# 1. Initialize the parser
parser = argparse.ArgumentParser(description="A script to process custom data.")

# 2. Add a positional argument (required by default)
parser.add_argument("filename", type=str, help="The path to the source file")

# 3. Add an optional argument/flag with a type and default value
parser.add_argument(
    "-t", "--timestamp", type=str, default="", help="Timestamp of meeting"
)

# 4. Add a boolean flag (True if passed, False otherwise)
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

# 5. Parse the inputs
args = parser.parse_args()

# 6. Access your values cleanly
print(f"Processing: {args.filename}...")
print(f"Meeting at {args.timestamp}.")
if args.verbose:
    print("Verbose mode activated!")


TIMESTAMP = args.timestamp
CHANAL_OTHER = "1"
CHANAL_ME = "2"

MEETING_DIR = Path.home() / "workspace" / "meetings" / f"meeting-{TIMESTAMP}"
MEETING_CORE_FILE = MEETING_DIR / f"meeting-core-{TIMESTAMP}.wav"
MEETING_ME_FILE = MEETING_DIR / f"meeting-me-{TIMESTAMP}.wav"
MEETING_OTHER_FILE = MEETING_DIR / f"meeting-other-{TIMESTAMP}.wav"

if not MEETING_DIR.exists():
    raise RuntimeError("Meeting does not exist")

result = subprocess.run(
    [
        "ffmpeg",
        "-i",
        f"{MEETING_CORE_FILE}",
        "-af",
        f"pan=mono|c0=c{CHANAL_OTHER}",
        f"{MEETING_OTHER_FILE}",
    ],
    capture_output=True,
    text=True,
)

result = subprocess.run(
    [
        "ffmpeg",
        "-i",
        f"{MEETING_CORE_FILE}",
        "-af",
        f"pan=mono|c0=c{CHANAL_ME}",
        f"{MEETING_ME_FILE}",
    ],
    capture_output=True,
    text=True,
)
