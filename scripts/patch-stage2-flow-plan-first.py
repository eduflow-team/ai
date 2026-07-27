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
    for key in list(node_data["template"]):
        value = node_data["template"][key]
        if (
            key not in {"_type", "code", "template"}
            and isinstance(value, dict)
            and value.get("_input_type") == "MessageTextInput"
            and key not in fields
        ):
            del node_data["template"][key]
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
            display_name="Compliant AI Response",
            name="compliant_response",
            method="format_response",
        ),
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

    def format_response(self) -> Message:
        plan_raw = self._text(self.error_plan)
        plan = json.loads(self._extract_json(plan_raw))
        errors = plan.get("planned_errors") or plan.get("generated_errors") or []
        response = self._text(self.flawed_ai_response).strip()
        for index, item in enumerate(errors, start=1):
            if not isinstance(item, dict):
                continue
            sentence = str(item.get("error_sentence") or "").strip()
            marker = f"[[ERROR_{index}]]"
            if marker in response:
                response = response.replace(marker, sentence, 1)
            elif sentence and sentence not in response:
                response = f"{response} {sentence}".strip()
        return Message(text=response)

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


def _formatter_input_template(name: str, display_name: str, info: str) -> dict:
    return {
        "_input_type": "MessageInput",
        "advanced": False,
        "display_name": display_name,
        "dynamic": False,
        "info": info,
        "input_types": ["Message"],
        "list": False,
        "list_add_label": "Add More",
        "load_from_db": False,
        "name": name,
        "override_skip": False,
        "placeholder": "",
        "required": True,
        "show": True,
        "title_case": False,
        "tool_mode": False,
        "trace_as_input": True,
        "trace_as_metadata": True,
        "track_in_telemetry": False,
        "type": "str",
        "value": "",
    }


def _configure_formatter_node(formatter_node: dict) -> None:
    node_data = formatter_node["data"]["node"]
    formatter_node["data"]["description"] = (
        "오류 계획과 학생용 답변을 generated_errors JSON으로 변환합니다."
    )
    node_data["description"] = formatter_node["data"]["description"]
    node_data["field_order"] = ["error_plan", "flawed_ai_response"]
    node_data["icon"] = "braces"
    node_data["name"] = "Stage2PlanFormatter"
    node_data["outputs"] = [
        {
            "allows_loop": False,
            "cache": True,
            "display_name": "Compliant AI Response",
            "group_outputs": False,
            "hidden": None,
            "loop_types": None,
            "method": "format_response",
            "name": "compliant_response",
            "options": None,
            "required_inputs": None,
            "selected": "Message",
            "tool_mode": True,
            "types": ["Message"],
            "value": "__UNDEFINED__",
        },
        {
            "allows_loop": False,
            "cache": True,
            "display_name": "Generated Errors JSON",
            "group_outputs": False,
            "hidden": None,
            "loop_types": None,
            "method": "format_errors",
            "name": "generated_errors",
            "options": None,
            "required_inputs": None,
            "selected": "Message",
            "tool_mode": True,
            "types": ["Message"],
            "value": "__UNDEFINED__",
        }
    ]
    code_field = node_data["template"]["code"]
    node_data["template"] = {
        "_type": "Component",
        "code": code_field,
        "error_plan": _formatter_input_template(
            "error_plan",
            "Error Plan JSON",
            "OpenAI planner output",
        ),
        "flawed_ai_response": _formatter_input_template(
            "flawed_ai_response",
            "Flawed AI Response",
            "Sanitized student answer",
        ),
    }
    node_data["template"]["code"]["value"] = _plan_formatter_code()


def _handle_string(data: dict) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return serialized.replace('"', "œ")


def _validate_flow(data: dict) -> None:
    nodes = data["nodes"]
    edges = data["edges"]
    node_ids = [node["id"] for node in nodes]
    edge_ids = [edge["id"] for edge in edges]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Duplicate node IDs")
    if len(edge_ids) != len(set(edge_ids)):
        raise ValueError("Duplicate edge IDs")

    formatter = _find_node(nodes, "CustomComponent-PlanFmt")["data"]["node"]
    if formatter["field_order"] != ["error_plan", "flawed_ai_response"]:
        raise ValueError("Formatter input metadata is stale")
    formatter_outputs = [
        (output["name"], output["method"])
        for output in formatter["outputs"]
    ]
    if formatter_outputs != [
        ("compliant_response", "format_response"),
        ("generated_errors", "format_errors"),
    ]:
        raise ValueError("Formatter output metadata is stale")
    compile(formatter["template"]["code"]["value"], "<stage2_plan_formatter>", "exec")

    expected_edges = {
        ("LanguageModelComponent-Ek4nl", "Prompt-fwk9l", "error_plan"),
        ("LanguageModelComponent-Ek4nl", "CustomComponent-PlanFmt", "error_plan"),
        (
            "CustomComponent-33aRa",
            "CustomComponent-PlanFmt",
            "flawed_ai_response",
        ),
        ("CustomComponent-PlanFmt", "ChatOutput-IC6oV", "input_value"),
        ("CustomComponent-PlanFmt", "ChatOutput-YlcM3", "input_value"),
    }
    actual_edges = {
        (
            edge["source"],
            edge["target"],
            edge["data"]["targetHandle"]["fieldName"],
        )
        for edge in edges
    }
    if not expected_edges.issubset(actual_edges):
        raise ValueError("Plan-first edges are incomplete")


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

    nodes[:] = [
        node for node in nodes if node.get("id") != "CustomComponent-PlanFmt"
    ]
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
    _configure_formatter_node(formatter_node)
    nodes.append(formatter_node)

    data["edges"] = [
        edge
        for edge in edges
        if not str(edge.get("id", "")).startswith("edge-")
        and edge.get("source") != "CustomComponent-PlanFmt"
        and edge.get("target") != "CustomComponent-PlanFmt"
        if not (
            edge.get("source") == "CustomComponent-33aRa"
            and edge.get("target") in {"Prompt-We0Ob", "ChatOutput-IC6oV"}
        )
        and not (
            edge.get("source") == "LanguageModelComponent-Ek4nl"
            and edge.get("target") == "ChatOutput-YlcM3"
        )
    ]

    def _edge(
        source: str,
        source_type: str,
        source_handle: str,
        target: str,
        target_field: str,
    ) -> dict:
        source_data = {
            "dataType": source_type,
            "id": source,
            "name": source_handle,
            "output_types": ["Message"],
        }
        target_data = {
            "fieldName": target_field,
            "id": target,
            "inputTypes": ["Message"],
            "type": "str",
        }
        return {
            "animated": False,
            "className": "",
            "data": {
                "sourceHandle": source_data,
                "targetHandle": target_data,
            },
            "id": f"edge-{source}-{target}-{target_field}",
            "selected": False,
            "source": source,
            "sourceHandle": _handle_string(source_data),
            "target": target,
            "targetHandle": _handle_string(target_data),
        }

    data["edges"].extend(
        [
            _edge(
                "LanguageModelComponent-Ek4nl",
                "LanguageModelComponent",
                "text_output",
                "Prompt-fwk9l",
                "error_plan",
            ),
            _edge(
                "LanguageModelComponent-Ek4nl",
                "LanguageModelComponent",
                "text_output",
                "CustomComponent-PlanFmt",
                "error_plan",
            ),
            _edge(
                "CustomComponent-33aRa",
                "PlainTextSanitizer",
                "sanitized_text",
                "CustomComponent-PlanFmt",
                "flawed_ai_response",
            ),
            _edge(
                "CustomComponent-PlanFmt",
                "Stage2PlanFormatter",
                "compliant_response",
                "ChatOutput-IC6oV",
                "input_value",
            ),
            _edge(
                "CustomComponent-PlanFmt",
                "Stage2PlanFormatter",
                "generated_errors",
                "ChatOutput-YlcM3",
                "input_value",
            ),
        ]
    )

    _validate_flow(data)
    FLOW_PATH.write_text(
        json.dumps(flow, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Patched {FLOW_PATH}")


if __name__ == "__main__":
    main()
