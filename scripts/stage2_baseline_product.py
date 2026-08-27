#!/usr/bin/env python3
"""Stage2 product-path baseline (1 error/card). Encoding-safe + server-like indices."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LANGFLOW_URL = os.getenv("LANGFLOW_URL", "http://localhost:7860").rstrip("/")
API_KEY = os.getenv("LANGFLOW_API_KEY", "")
FLOW_ID = os.getenv("FLOW_ID", "")
RUNS_PER_CASE = int(os.getenv("RUNS_PER_CASE", "3"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", f"baseline-results/product-{datetime.now():%Y%m%d-%H%M%S}"))
PHASE = os.getenv("BASELINE_PHASE", "unknown")

JANG_DOC = (
    "장영실은 세종 대에 자격루와 측우기를 발명한 조선시대 최고의 과학자입니다.\n"
    "자격루는 물의 흐름을 이용해 시간을 알리는 자동 물시계이고, 측우기는 비의 양을 재는 기구입니다."
)
PERSONA = "장영실이 연을 만들었다고 믿고, 자격루를 서양 기술이라고 주장하는 선생님"

def _load_long_doc() -> str:
    path = Path(__file__).resolve().parents[1] / "baseline-results" / "dongasia-body.txt"
    if path.is_file():
        text = path.read_text(encoding="utf-8").strip()
        if len(text) > 400:
            return text
    return JANG_DOC


LONG_DOC = _load_long_doc()
LONG_PERSONA = "주몽이 백제를 세웠다고 굳게 믿는 동아시아사 선생님"

SHORT_CASES = [
    {
        "id": "single-persona-bias",
        "name": "PERSONA_BIAS 단일 (제품 경로)",
        "document_text": JANG_DOC,
        "question": "장영실은 어떤 발명을 했나요?",
        "persona": "장영실이 연을 만들었다고 확신하는 역사 선생님",
        "hallucination_types": "PERSONA_BIAS",
        "expected_error_count": 1,
    },
    {
        "id": "single-fabrication",
        "name": "INFORMATION_FABRICATION 단일 (제품 경로)",
        "document_text": JANG_DOC,
        "question": "장영실의 발명품에 대해 설명해줘.",
        "persona": PERSONA,
        "hallucination_types": "INFORMATION_FABRICATION",
        "expected_error_count": 1,
    },
    {
        "id": "single-retrieval",
        "name": "RETRIEVAL_ERROR 단일 (제품 경로)",
        "document_text": JANG_DOC,
        "question": "자격루와 측우기는 각각 무엇인가요?",
        "persona": PERSONA,
        "hallucination_types": "RETRIEVAL_ERROR",
        "expected_error_count": 1,
    },
]

LONG_CASES = [
    {
        "id": "long-persona-bias",
        "name": "긴문서 PERSONA_BIAS 단일",
        "document_text": LONG_DOC,
        "question": "고구려는 어떻게 건국되었나요?",
        "persona": LONG_PERSONA,
        "hallucination_types": "PERSONA_BIAS",
        "expected_error_count": 1,
    },
    {
        "id": "long-fabrication",
        "name": "긴문서 INFORMATION_FABRICATION 단일",
        "document_text": LONG_DOC,
        "question": "도왜인은 누구이며 어떤 역할을 했나요?",
        "persona": LONG_PERSONA,
        "hallucination_types": "INFORMATION_FABRICATION",
        "expected_error_count": 1,
    },
    {
        "id": "long-retrieval",
        "name": "긴문서 RETRIEVAL_ERROR 단일",
        "document_text": LONG_DOC,
        "question": "백제와 신라의 성립 과정을 설명해줘.",
        "persona": LONG_PERSONA,
        "hallucination_types": "RETRIEVAL_ERROR",
        "expected_error_count": 1,
    },
]

SUITE = os.getenv("BASELINE_SUITE", "short").strip().lower()
CASES = LONG_CASES if SUITE == "long" else SHORT_CASES
if SUITE == "all":
    CASES = SHORT_CASES + LONG_CASES


def load_env_file(path: Path) -> None:
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


def build_payload(case: dict) -> dict:
    count = str(case["expected_error_count"])
    types = case["hallucination_types"]
    shared = {
        "document_text": case["document_text"],
        "hallucination_types": types,
        "expected_error_count": count,
    }
    return {
        "input_value": "",
        "session_id": f"stage2-product-{case['id']}",
        "tweaks": {
            "Prompt-fwk9l": {
                "document_text": case["document_text"],
                "question": case["question"],
                "persona": case["persona"],
                "hallucination_types": types,
                "expected_error_count": count,
            },
            "Prompt-We0Ob": shared,
        },
    }


def extract_texts(response: dict) -> list[str]:
    texts: list[str] = []
    for run_output in response.get("outputs") or []:
        for inner in run_output.get("outputs") or []:
            results = inner.get("results") or {}
            message = results.get("message") or results.get("text")
            if isinstance(message, dict):
                if message.get("text"):
                    texts.append(str(message["text"]))
            elif message:
                texts.append(str(message))
    return texts


def parse_generated_errors(raw: str) -> tuple[list[dict] | None, str | None]:
    if not raw or not raw.strip():
        return None, "empty generated_errors text"
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("\n", 1)
        clean = parts[1] if len(parts) > 1 else clean
        clean = clean.split("```", 1)[0].strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse failed: {exc}"
    if isinstance(parsed, dict) and "generated_errors" in parsed:
        return list(parsed["generated_errors"]), None
    if isinstance(parsed, list):
        return list(parsed), None
    return None, "generated_errors key missing"


def apply_server_indices(flawed: str, errors: list[dict]) -> tuple[list[dict], list[str]]:
    """Mirror backend stage2_index_calculator.apply_server_error_indices."""
    codes: list[str] = []
    updated: list[dict] = []
    for err in errors:
        sentence = str(err.get("error_sentence") or "").strip()
        if not sentence:
            codes.append("ERROR_SENTENCE_NOT_FOUND")
            updated.append({**err, "start_index": 0, "end_index": 0})
            continue
        positions: list[int] = []
        start = 0
        while True:
            idx = flawed.find(sentence, start)
            if idx < 0:
                break
            positions.append(idx)
            start = idx + len(sentence)
        if not positions:
            codes.append("ERROR_SENTENCE_NOT_FOUND")
            updated.append({**err, "start_index": 0, "end_index": 0})
        elif len(positions) > 1:
            codes.append("ERROR_SENTENCE_AMBIGUOUS")
            updated.append({**err, "start_index": 0, "end_index": 0})
        else:
            s = positions[0]
            updated.append({**err, "start_index": s, "end_index": s + len(sentence)})
    return updated, codes


def bucket_reason(reason: str) -> str:
    if "expected" in reason and "errors" in reason:
        return "error_count_mismatch"
    if "evidence_sentence" in reason:
        return "evidence_not_found"
    if "error_type" in reason:
        return "error_type_invalid"
    if "error_sentence not found" in reason or "ERROR_SENTENCE_NOT_FOUND" in reason:
        return "error_sentence_missing"
    if "AMBIGUOUS" in reason or "slice mismatch" in reason or "invalid range" in reason:
        return "index_accuracy"
    if "JSON" in reason or "generated_errors" in reason or "empty" in reason:
        return "parse_or_output"
    if "HTTP" in reason:
        return "http_failed"
    return "other"


def evaluate(case: dict, run_index: int, flawed: str | None, errors: list[dict] | None,
             parse_error: str | None, elapsed_ms: int, http_ok: bool) -> dict:
    checks = {
        "call_success": http_ok,
        "json_parse_success": parse_error is None,
        "error_count_match": False,
        "error_types_valid": True,
        "error_sentence_in_flawed": True,
        "evidence_in_document": True,
        "index_accuracy": True,
    }
    fail_reasons: list[str] = []
    if parse_error:
        fail_reasons.append(parse_error)
    if not http_ok:
        fail_reasons.append("HTTP call failed")

    allowed = [t.strip() for t in case["hallucination_types"].split(",") if t.strip()]
    expected = int(case["expected_error_count"])
    index_codes: list[str] = []

    if errors is not None:
        checks["error_count_match"] = len(errors) == expected
        if not checks["error_count_match"]:
            fail_reasons.append(f"expected {expected} errors, got {len(errors)}")

        if flawed:
            errors, index_codes = apply_server_indices(flawed, errors)
            for code in index_codes:
                checks["index_accuracy"] = False
                fail_reasons.append(code)

        for err in errors:
            etype = str(err.get("error_type") or "")
            if etype not in allowed:
                checks["error_types_valid"] = False
                fail_reasons.append(f"error_type {etype} not in allowed [{', '.join(allowed)}]")
            es = str(err.get("error_sentence") or "")
            if flawed and es and es not in flawed:
                checks["error_sentence_in_flawed"] = False
                fail_reasons.append("error_sentence not found in flawed_ai_response")
            ev = str(err.get("evidence_sentence") or "")
            if ev and ev not in case["document_text"]:
                checks["evidence_in_document"] = False
                fail_reasons.append("evidence_sentence not found in document_text")
            if flawed and checks["index_accuracy"]:
                start = int(err.get("start_index") or 0)
                end = int(err.get("end_index") or 0)
                if start < 0 or end <= start or end > len(flawed) or flawed[start:end] != es:
                    checks["index_accuracy"] = False
                    fail_reasons.append(f"slice mismatch at {start}..{end}")
    elif parse_error is None:
        fail_reasons.append("no errors array")

    auto_pass = all(
        [
            checks["call_success"],
            checks["json_parse_success"],
            checks["error_count_match"],
            checks["error_types_valid"],
            checks["error_sentence_in_flawed"],
            checks["evidence_in_document"],
            checks["index_accuracy"],
        ]
    )
    return {
        "case_id": case["id"],
        "case_name": case["name"],
        "run": run_index,
        "elapsed_ms": elapsed_ms,
        "auto_pass": auto_pass,
        "checks": checks,
        "fail_reasons": fail_reasons,
        "flawed_ai_response": flawed,
        "generated_errors": errors,
        "index_codes": index_codes,
    }


def run_flow(payload: dict) -> tuple[bool, dict | None, str | None]:
    url = f"{LANGFLOW_URL}/api/v1/run/{FLOW_ID}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "x-api-key": API_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
            return True, json.loads(raw.decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return False, None, f"HTTP {exc.code}: {detail[:500]}"
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)


def main() -> int:
    global API_KEY, FLOW_ID
    root = Path(__file__).resolve().parents[1]
    load_env_file(root / ".env")
    load_env_file(root.parent / "backend" / ".env")
    API_KEY = os.getenv("LANGFLOW_API_KEY", API_KEY)
    FLOW_ID = os.getenv("FLOW_ID") or os.getenv("LANGFLOW_STAGE2_FLOW_ID", FLOW_ID)
    if not FLOW_ID or not API_KEY:
        print("FLOW_ID / LANGFLOW_API_KEY required", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Stage2 PRODUCT baseline [{PHASE}/{SUITE}]: {len(CASES)} cases x {RUNS_PER_CASE}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Flow: {FLOW_ID} @ {LANGFLOW_URL}")
    print()

    all_results: list[dict] = []
    for case in CASES:
        print(f"Case: {case['id']}")
        for run_i in range(1, RUNS_PER_CASE + 1):
            t0 = time.perf_counter()
            http_ok, response, http_err = run_flow(build_payload(case))
            elapsed = int((time.perf_counter() - t0) * 1000)
            flawed = None
            errors = None
            parse_error = http_err
            if http_ok and response is not None:
                texts = extract_texts(response)
                if texts:
                    flawed = texts[0]
                if len(texts) >= 2:
                    errors, parse_error = parse_generated_errors(texts[1])
                else:
                    parse_error = f"missing generated_errors output (got {len(texts)} text outputs)"

            result = evaluate(case, run_i, flawed, errors, parse_error, elapsed, http_ok)
            all_results.append(result)
            status = "PASS" if result["auto_pass"] else "FAIL"
            print(f"  run {run_i}: {status} ({elapsed} ms)")
            if not result["auto_pass"] and result["fail_reasons"]:
                print(f"    -> {'; '.join(result['fail_reasons'])}")

            artifact = {
                "meta": {
                    "case_id": case["id"],
                    "run": run_i,
                    "elapsed_ms": elapsed,
                    "auto_pass": result["auto_pass"],
                    "phase": PHASE,
                },
                "input": case,
                "output": {
                    "flawed_ai_response": flawed,
                    "generated_errors": result["generated_errors"],
                },
                "checks": result["checks"],
                "fail_reasons": result["fail_reasons"],
            }
            (OUTPUT_DIR / f"{case['id']}-run{run_i}.json").write_text(
                json.dumps(artifact, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    total = len(all_results)
    passed = sum(1 for r in all_results if r["auto_pass"])
    by_case = []
    for case in CASES:
        runs = [r for r in all_results if r["case_id"] == case["id"]]
        case_pass = sum(1 for r in runs if r["auto_pass"])
        by_case.append(
            {
                "case_id": case["id"],
                "name": case["name"],
                "pass": case_pass,
                "total": len(runs),
                "pass_rate": round(100 * case_pass / len(runs), 1) if runs else 0,
                "avg_ms": round(sum(r["elapsed_ms"] for r in runs) / len(runs)) if runs else 0,
            }
        )

    fail_bucket: Counter[str] = Counter()
    for r in all_results:
        if r["auto_pass"]:
            continue
        for reason in r["fail_reasons"]:
            fail_bucket[bucket_reason(reason)] += 1

    report = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "phase": PHASE,
        "flow_id": FLOW_ID,
        "langflow_url": LANGFLOW_URL,
        "runs_per_case": RUNS_PER_CASE,
        "total_runs": total,
        "auto_pass_count": passed,
        "auto_pass_rate": round(100 * passed / total, 1) if total else 0,
        "avg_elapsed_ms": round(sum(r["elapsed_ms"] for r in all_results) / total) if total else 0,
        "by_case": by_case,
        "fail_reason_counts": dict(fail_bucket),
        "representative_failures": [
            {
                "case_id": r["case_id"],
                "run": r["run"],
                "fail_reasons": r["fail_reasons"],
                "flawed_preview": (r["flawed_ai_response"] or "")[:200] or None,
            }
            for r in all_results
            if not r["auto_pass"]
        ][:5],
    }
    (OUTPUT_DIR / "baseline-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=== PRODUCT Baseline Summary ===")
    print(f"Auto pass: {passed} / {total} ({report['auto_pass_rate']}%)")
    print(f"Avg response: {report['avg_elapsed_ms']} ms")
    print(f"Report: {OUTPUT_DIR / 'baseline-report.json'}")
    for row in by_case:
        print(f"  {row['case_id']}: {row['pass']}/{row['total']} ({row['pass_rate']}%) avg={row['avg_ms']}ms")
    if fail_bucket:
        print("Fail reason buckets:")
        for key, val in fail_bucket.most_common():
            print(f"  {key}: {val}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
