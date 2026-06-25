from __future__ import annotations


def split_text(text: str, chunk_size: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if not text:
        return [""]

    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
