from __future__ import annotations

import logging

from voice_generator.cli import run


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    return run()
