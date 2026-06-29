from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from voice_generator.errors import FeatureNotImplementedError


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    loading_time: float | None = None
    inference_speed: float | None = None
    generation_duration: float | None = None
    realtime_factor: float | None = None
    output_size: int | None = None


def run_benchmark(provider: str | None = None) -> BenchmarkResult:
    raise FeatureNotImplementedError("benchmarking is not implemented yet")
