#!/usr/bin/env python3
"""Patch stage2-hallucination-gen.json to plan-first v2 architecture."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW_PATH = ROOT / "flows" / "stage2-hallucination-gen.json"
PROMPTS_DIR = ROOT / "prompts" / "stage2"


def _extract_prompt_body(markdown_path: Path) -> str:
    text = markdown_path.read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if not match:
        raise ValueError(f"Prompt block not found in {markdown_path}")
    return match.group(1).strip()


def _find_node(nodes: list[dict], node_id: str) -> dict:
    for node in nodes:
        if node.get("id") == node_id:
            return node
    raise KeyError(node_id)


def _set_prompt_template(node: dict, *, fields: list[str], template: str) -> None:
    node_data = node["data"]["node"]
    node_data["custom_fields"]["template"] = fields
    node_data["display_name"] = node["data"]["display_name"]
    node_data["template"]["template"]["value"] = template
    for field in fields:
        if field not in node_data["template"]:
            node_data["template"][field] = {
                "_input_type": "MessageTextInput",
                "display_name": field,
                "dynamic": False,
                "info": "",
                "input_types": ["Message"],
                "list": False,
                "load_from_db": False,
                "name": field,
                "placeholder": "",
                "required": False,
                "show": True,
                "title_case": False,
                "tool_mode": True,
                "trace_as_input": True,
                "type": "str",
                "value": "",
            }


def _plan_formatter_code() -> str:
    return '''import json
import re

from lfx.custom.custom_component.component import Component
from lfx.io import MessageInput, Output
from lfx.schema.message import Message


class Stage2PlanFormatter(Component):
    display_name = "Stage2 Plan Formatter"
    description = "오류 계획 JSON과 flawed_ai_response를 generated_errors JSON으로 변환합니다."
    icon = "braces"
    name = "Stage2PlanFormatter"

    inputs = [
        MessageInput(
            name="error_plan",
            display_name="Error Plan JSON",
            info="OpenAI planner output",
        ),
        MessageInput(
            name="flawed_ai_response",
            display_name="Flawed AI Response",
            info="Sanitized student answer",
        ),
    ]

    outputs = [
        Output(
            display_name="Generated Errors JSON",
            name="generated_errors",
            method="format_errors",
        ),
    ]

    def format_errors(self) -> Message:
        plan_raw = self._text(self.error_plan)
        plan = json.loads(self._extract_json(plan_raw))
        errors = plan.get("planned_errors") or plan.get("generated_errors") or []
        cleaned = []
        for item in errors:
            if not isinstance(item, dict):
                continue
            cleaned.append(
                {
                    "error_sentence": item.get("error_sentence", ""),
                    "error_type": item.get("error_type", ""),
                    "correct_sentence": item.get("correct_sentence", ""),
                    "hallucination_reason": item.get("hallucination_reason", ""),
                    "evidence_sentence": item.get("evidence_sentence", ""),
                    "retrieved_context": item.get("retrieved_context"),
                    "retrieval_source": item.get("retrieval_source"),
                }
            )
        payload = {"generated_errors": cleaned}
        return Message(text=json.dumps(payload, ensure_ascii=False))

    def _text(self, message) -> str:
        if message is None:
            return ""
        return getattr(message, "text", None) or str(message)

    def _extract_json(self, raw: str) -> str:
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.split("\\n", 1)[-1].rsplit("```", 1)[0].strip()
        return text
'''


def main() -> None:
    flow = json.loads(FLOW_PATH.read_text(encoding="utf-8"))
    data = flow["data"]
    nodes = data["nodes"]
    edges = data["edges"]

    plan_prompt = _extract_prompt_body(PROMPTS_DIR / "error-plan.md")
    gen_prompt = _extract_prompt_body(PROMPTS_DIR / "hallucination-gen.md")

    plan_node = _find_node(nodes, "Prompt-We0Ob")
    gen_node = _find_node(nodes, "Prompt-fwk9l")
    sanitizer_node = _find_node(nodes, "CustomComponent-33aRa")

    plan_node["data"]["display_name"] = "error_plan_prompt"
    _set_prompt_template(
        plan_node,
        fields=[
            "document_text",
            "question",
            "persona",
            "hallucination_types",
            "expected_error_count",
            "candidate_chunks",
            "validation_feedback",
        ],
        template=plan_prompt,
    )

    gen_node["data"]["display_name"] = "hallucination_gen_prompt"
    _set_prompt_template(
        gen_node,
        fields=[
            "document_text",
            "question",
            "persona",
            "hallucination_types",
            "expected_error_count",
            "error_plan",
        ],
        template=gen_prompt,
    )

    formatter_node = copy.deepcopy(sanitizer_node)
    formatter_node["id"] = "CustomComponent-PlanFmt"
    formatter_node["data"]["id"] = "CustomComponent-PlanFmt"
    formatter_node["data"]["display_name"] = "stage2_plan_formatter"
    formatter_node["data"]["node"]["display_name"] = "stage2_plan_formatter"
    formatter_node["data"]["node"]["metadata"]["module"] = (
        "lfx.components.custom_component.custom_component.CustomComponent"
    )
    formatter_node["data"]["type"] = "Stage2PlanFormatter"
    formatter_node["position"] = {
        "x": sanitizer_node["position"]["x"] + 420,
        "y": sanitizer_node["position"]["y"] + 180,
    }
    formatter_node["data"]["node"]["template"]["code"]["value"] = _plan_formatter_code()
    nodes.append(formatter_node)

    data["edges"] = [
        edge
        for edge in edges
        if not (
            edge.get("source") == "CustomComponent-33aRa"
            and edge.get("target") == "Prompt-We0Ob"
        )
        and not (
            edge.get("source") == "LanguageModelComponent-Ek4nl"
            and edge.get("target") == "ChatOutput-YlcM3"
        )
    ]

    def _edge(source: str, source_handle: str, target: str, target_field: str) -> dict:
        return {
            "animated": False,
            "className": "",
            "data": {
                "sourceHandle": {
                    "dataType": source.split("-")[0],
                    "id": source,
                    "name": source_handle,
                    "output_types": ["Message"],
                },
                "targetHandle": {
                    "fieldName": target_field,
                    "id": target,
                    "inputTypes": ["Message"],
                    "type": "str",
                },
            },
            "id": f"edge-{source}-{target}-{target_field}",
            "selected": False,
            "source": source,
            "sourceHandle": source_handle,
            "target": target,
            "targetHandle": target_field,
        }

    data["edges"].extend(
        [
            _edge(
                "LanguageModelComponent-Ek4nl",
                "text_output",
                "Prompt-fwk9l",
                "error_plan",
            ),
            _edge(
                "LanguageModelComponent-Ek4nl",
                "text_output",
                "CustomComponent-PlanFmt",
                "error_plan",
            ),
            _edge(
                "CustomComponent-33aRa",
                "sanitized_text",
                "CustomComponent-PlanFmt",
                "flawed_ai_response",
            ),
            _edge(
                "CustomComponent-PlanFmt",
                "generated_errors",
                "ChatOutput-YlcM3",
                "input_value",
            ),
        ]
    )

    FLOW_PATH.write_text(
        json.dumps(flow, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Patched {FLOW_PATH}")


if __name__ == "__main__":
    main()
