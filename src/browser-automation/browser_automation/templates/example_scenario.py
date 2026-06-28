from __future__ import annotations


def run(page, variables: dict | None = None):
    variables = variables or {}
    page.goto(variables.get("url", "https://example.com"))
    return {"title": page.title()}
