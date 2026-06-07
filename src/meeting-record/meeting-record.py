import subprocess
import re
from datetime import datetime
from pathlib import Path
import argparse
import json

# 1. Initialize the parser
parser = argparse.ArgumentParser(description="Record Meeting Session")

# 2. Add a positional argument (required by default)
parser.add_argument("filename", type=str, help="The path to the source file")

# 3. Add an optional argument/flag with a type and default value
parser.add_argument("-s", "--stamp", type=str, default="", help="Stamp of the meeting")

# 4. Add a boolean flag (True if passed, False otherwise)
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

# 5. Parse the inputs
args = parser.parse_args()

# 6. Access your values cleanly
print(f"Processing: {args.filename}...")
print(f"Meeting stamp is {args.stamp}.")
if args.verbose:
    print("Verbose mode activated!")

# Generate the string
TIMESTAMP = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

result = subprocess.run(
    ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
    capture_output=True,
    text=True,
)

device_code = None

for line in result.stderr.splitlines():
    if "Aggregate Device" in line:
        match = re.search(r"\[(\d+)\]", line)
        if match:
            device_code = int(match.group(1))
            break

if device_code is None:
    raise RuntimeError("Aggregate Device not found")

MEETING_DIR = Path.home() / "workspace" / "meetings" / f"meeting-{TIMESTAMP}"

MEETING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = MEETING_DIR / f"meeting-core-{TIMESTAMP}.wav"

subprocess.run(
    [
        "ffmpeg",
        "-f",
        "avfoundation",
        "-i",
        f":{device_code}",
        str(OUTPUT_FILE),
    ],
    check=True,
)

metadata_path = MEETING_DIR / "metadata.json"

metadata_path.write_text(json.dumps({"stamp": args.stamp}))

print(result.stderr)
