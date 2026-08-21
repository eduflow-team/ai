#!/usr/bin/env python3
"""Patch Langflow stage2 flow Prompt templates from local flow JSON. Backs up first."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW_PATH = ROOT / "flows" / "stage2-hallucination-gen.json"
BACKUP_PATH = ROOT / "baseline-results" / "flow-backup-before-quality-20260821.json"
PROMPT_IDS = ("Prompt-We0Ob", "Prompt-fwk9l")


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def http_json(method: str, url: str, api_key: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "x-api-key": api_key,
            **({"Content-Type": "application/json; charset=utf-8"} if data is not None else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    load_env(ROOT / ".env")
    load_env(ROOT.parent / "backend" / ".env")
    api_key = os.environ.get("LANGFLOW_API_KEY", "")
    flow_id = (
        os.environ.get("FLOW_ID")
        or os.environ.get("LANGFLOW_STAGE2_FLOW_ID")
        or "5dcabbe0-9639-4a0c-8f71-f682ba875712"
    )
    if not api_key:
        print("LANGFLOW_API_KEY missing", file=sys.stderr)
        return 1

    local = json.loads(FLOW_PATH.read_text(encoding="utf-8"))
    local_nodes = {n["id"]: n for n in local["data"]["nodes"]}
    remote = http_json("GET", f"http://localhost:7860/api/v1/flows/{flow_id}", api_key)
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.write_text(json.dumps(remote, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"backup: {BACKUP_PATH}")

    remote_data = remote.get("data") or {}
    changed = 0
    for node in remote_data.get("nodes") or []:
        node_id = node.get("id")
        if node_id not in PROMPT_IDS or node_id not in local_nodes:
            continue
        new_val = local_nodes[node_id]["data"]["node"]["template"]["template"]["value"]
        old_val = node["data"]["node"]["template"]["template"].get("value", "")
        if old_val != new_val:
            node["data"]["node"]["template"]["template"]["value"] = new_val
            changed += 1
            print(f"patched {node_id}: {len(old_val)} -> {len(new_val)}")

    if changed == 0:
        print("no prompt changes to patch")
        return 0

    updated = http_json(
        "PATCH",
        f"http://localhost:7860/api/v1/flows/{flow_id}",
        api_key,
        {
            "name": remote.get("name"),
            "description": remote.get("description"),
            "data": remote_data,
            "endpoint_name": remote.get("endpoint_name"),
        },
    )
    print(f"PATCH ok updated_at={updated.get('updated_at')} id={updated.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
