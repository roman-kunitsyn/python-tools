from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from browser_automation.extractors.images import ExtractedImage


@dataclass(slots=True)
class CrawlPage:
    url: str
    depth: int
    title: str | None = None
    html: str = ""
    images: list[ExtractedImage] = field(default_factory=list)


@dataclass(slots=True)
class CrawlResult:
    root_url: str
    pages: list[CrawlPage] = field(default_factory=list)

    @property
    def urls(self) -> list[str]:
        return [page.url for page in self.pages]


@dataclass(slots=True)
class ExportArtifact:
    source_url: str
    output_path: Path


@dataclass(slots=True)
class RecorderResult:
    scenario_path: Path
    output_path: Path
    exit_code: int
