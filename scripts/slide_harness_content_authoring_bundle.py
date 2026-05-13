#!/usr/bin/env python3
"""Build a Hermes/JARVIS prompt bundle for slide-harness content-plan authoring.

This script does not call Hermes, an LLM, or the network. It only combines a
brief, content-plan template, and optional context notes into a prompt file that
Hermes can use to author a valid content-plan JSON.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_PROMPT_TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "slide-harness" / "content-plan-author-prompt.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json_pretty(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_prompt(brief: Path, template: Path, contexts: list[Path], prompt_template: Path) -> str:
    prompt = read_text(prompt_template)
    context_notes = []
    for context in contexts:
        context_notes.append(f"# Context: {context}\n\n{read_text(context)}")
    replacements = {
        "{{BRIEF_JSON}}": read_json_pretty(brief),
        "{{CONTENT_PLAN_TEMPLATE_JSON}}": read_json_pretty(template),
        "{{CONTEXT_NOTES}}": "\n\n---\n\n".join(context_notes) if context_notes else "No additional context provided.",
    }
    for old, new in replacements.items():
        prompt = prompt.replace(old, new)
    return prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a slide-harness content-plan authoring prompt bundle.")
    parser.add_argument("--brief", required=True, type=Path, help="Path to brief JSON produced by slide_harness.cli draft-brief or equivalent.")
    parser.add_argument("--template", required=True, type=Path, help="Path to content-plan template JSON produced by slide_harness.cli content-template.")
    parser.add_argument("--context", action="append", default=[], type=Path, help="Optional context markdown/text file. Repeatable.")
    parser.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE, type=Path, help="Prompt template markdown with placeholders.")
    parser.add_argument("--out", required=True, type=Path, help="Output prompt markdown path.")
    args = parser.parse_args()

    for path in [args.brief, args.template, args.prompt_template, *args.context]:
        if not path.exists():
            parser.error(f"missing path: {path}")

    prompt = build_prompt(args.brief, args.template, args.context, args.prompt_template)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(prompt, encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
