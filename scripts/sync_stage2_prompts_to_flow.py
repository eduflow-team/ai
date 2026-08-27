#!/usr/bin/env python3
"""Sync prompts/stage2/*.md into flows/stage2-hallucination-gen.json Prompt nodes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW_PATH = ROOT / "flows" / "stage2-hallucination-gen.json"
PROMPTS = {
    "Prompt-We0Ob": ROOT / "prompts" / "stage2" / "error-plan.md",
    "Prompt-fwk9l": ROOT / "prompts" / "stage2" / "hallucination-gen.md",
}


def extract_prompt_body(markdown_path: Path) -> str:
    text = markdown_path.read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if not match:
        raise ValueError(f"Prompt block not found in {markdown_path}")
    return match.group(1).strip()


def main() -> int:
    flow = json.loads(FLOW_PATH.read_text(encoding="utf-8"))
    nodes = flow.get("data", {}).get("nodes") or flow.get("nodes") or []
    by_id = {n.get("id"): n for n in nodes}
    updated = []
    for node_id, md_path in PROMPTS.items():
        node = by_id.get(node_id)
        if not node:
            print(f"MISSING node {node_id}", file=sys.stderr)
            return 1
        body = extract_prompt_body(md_path)
        template = node["data"]["node"]["template"]["template"]
        old = template.get("value", "")
        template["value"] = body
        updated.append((node_id, len(old), len(body)))
    FLOW_PATH.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for node_id, old_len, new_len in updated:
        print(f"updated {node_id}: {old_len} -> {new_len} chars")
    print(f"wrote {FLOW_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
