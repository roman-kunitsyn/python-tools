from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from browser_automation.browser import BrowserManager


@dataclass(slots=True)
class ScenarioRunResult:
    scenario_path: Path
    success: bool
    value: Any = None


def load_scenario_module(scenario_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(scenario_path.stem, scenario_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scenario module: {scenario_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _callable_with_context(callable_obj: object, *, page: object, context: object, browser: object, variables: Mapping[str, Any]) -> Any:
    signature = inspect.signature(callable_obj)  # type: ignore[arg-type]
    candidates = {
        "page": page,
        "context": context,
        "browser": browser,
        "variables": dict(variables),
        "data": dict(variables),
    }

    kwargs = {name: value for name, value in candidates.items() if name in signature.parameters}
    if kwargs:
        return callable_obj(**kwargs)  # type: ignore[misc]

    positional = []
    for parameter in signature.parameters.values():
        if parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue
        if parameter.name == "page":
            positional.append(page)
        elif parameter.name == "context":
            positional.append(context)
        elif parameter.name == "browser":
            positional.append(browser)
        elif parameter.name in {"variables", "data"}:
            positional.append(dict(variables))
        else:
            break

    if positional:
        return callable_obj(*positional)  # type: ignore[misc]

    return callable_obj(page)  # type: ignore[misc]


class ScenarioRunner:
    def __init__(self, browser: BrowserManager) -> None:
        self.browser = browser

    def run_scenario(self, scenario_path: Path, *, url: str | None = None, variables: Mapping[str, Any] | None = None) -> ScenarioRunResult:
        module = load_scenario_module(scenario_path)
        callable_obj = getattr(module, "run", None) or getattr(module, "main", None) or getattr(module, "scenario", None)
        if callable_obj is None:
            raise RuntimeError(f"Scenario module {scenario_path} does not define run(), main(), or scenario().")

        with self.browser.session() as session:
            page = session.open_page(url) if url is not None else session.open_page()
            value = _callable_with_context(
                callable_obj,
                page=page,
                context=session.context,
                browser=session.browser,
                variables=variables or {},
            )
        return ScenarioRunResult(scenario_path=scenario_path, success=True, value=value)
