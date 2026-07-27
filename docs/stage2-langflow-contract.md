# Stage 2 Langflow ↔ Backend 연동 계약 (plan-first v2)

Notion **시나리오2** · **개발 단계** 기준.  
2단계 파이프라인: **OpenAI 오류 계획 → Ollama 답변 생성 → Plan Formatter JSON**.

## Langflow가 담당하는 범위

| Notion 단계 | 내용 |
|-------------|------|
| 5 | 문서 + 페르소나 + 청크 후보 기반 **오류 계획** 생성 |
| 6 | 계획의 `error_sentence`를 그대로 포함한 AI 답변 생성 |
| 7 (일부) | `generated_errors[]` 메타데이터 (Plan Formatter 출력) |

학생 하이라이트·채점(8~21)은 **백엔드** 담당.

---

## Flow 구조 (8 functional nodes)

```
error_plan_prompt → OpenAI gpt-4o-mini → error_plan
                                              ↓ (wire)
                    hallucination_gen_prompt → Ollama EXAONE → Sanitizer → flawed_ai_response
                                              ↓ (wire)              ↓ (wire)
                              stage2_plan_formatter ← error_plan + flawed_ai_response
                                              ↓
                                    generated_errors
```

| 노드 ID | Display Name | 역할 |
|---------|--------------|------|
| `Prompt-We0Ob` | error_plan_prompt | OpenAI 오류 계획 JSON |
| `LanguageModelComponent-Ek4nl` | OpenAI (Planner) | `planned_errors[]` 생성 |
| `Prompt-fwk9l` | hallucination_gen_prompt | EXAONE 생성 프롬프트 |
| `LanguageModelComponent-grQBn` | Ollama EXAONE (생성) | 학생용 답변 |
| `CustomComponent-33aRa` | Plain Text Sanitizer | 마크다운 제거 |
| `ChatOutput-IC6oV` | flawed_ai_response | 학생용 AI 답변 |
| `CustomComponent-PlanFmt` | stage2_plan_formatter | plan → `generated_errors` JSON |
| `ChatOutput-YlcM3` | generated_errors | 오류 메타 JSON |

> **tweaks 키 = 노드 ID.** Import 후 Langflow **API 탭**에서 재확인.

---

## 입력 (tweaks)

| 노드 | 키 | 타입 | 출처 |
|------|-----|------|------|
| `Prompt-We0Ob` | `document_text` | string | `documents.raw_text` |
| `Prompt-We0Ob` | `question` | string | 교사 입력 |
| `Prompt-We0Ob` | `persona` | string | 교사 입력 |
| `Prompt-We0Ob` | `hallucination_types` | string | 쉼표 구분 enum |
| `Prompt-We0Ob` | `expected_error_count` | string | `"2"` 등 |
| `Prompt-We0Ob` | `candidate_chunks` | string | JSON (`Stage2RetrievalInput`) |
| `Prompt-We0Ob` | `validation_feedback` | string | 재시도 시 검증 코드 (8번 이후) |
| `Prompt-fwk9l` | `document_text` ~ `expected_error_count` | string | 동일 |
| `Prompt-fwk9l` | `error_plan` | string | **와이어** (Planner 출력) |

### 예시 payload

```json
{
  "input_value": "",
  "tweaks": {
    "Prompt-We0Ob": {
      "document_text": "장영실은 세종 대에 자격루와 측우기를 발명한...",
      "question": "장영실의 발명품에 대해 설명해줘.",
      "persona": "장영실이 연을 만들었다고 믿고...",
      "hallucination_types": "RETRIEVAL_ERROR, PERSONA_BIAS",
      "expected_error_count": "2",
      "candidate_chunks": "{\"strategy\":\"SAME_DOCUMENT_THEN_SYNTHETIC\",\"candidate_chunks\":[],\"synthetic_fallback_allowed\":true}",
      "validation_feedback": ""
    },
    "Prompt-fwk9l": {
      "document_text": "...",
      "question": "...",
      "persona": "...",
      "hallucination_types": "RETRIEVAL_ERROR, PERSONA_BIAS",
      "expected_error_count": "2"
    }
  }
}
```

---

## 출력

### Must

| 키 | 출처 노드 | 설명 |
|----|-----------|------|
| `flawed_ai_response` | `ChatOutput-IC6oV` | 학생에게 보여줄 AI 답변 |
| `generated_errors` | `ChatOutput-YlcM3` | JSON (`planned_errors` → formatter) |

### Planner JSON (중간)

```json
{
  "planned_errors": [
    {
      "error_sentence": "string",
      "error_type": "RETRIEVAL_ERROR",
      "correct_sentence": "string",
      "hallucination_reason": "string",
      "evidence_sentence": "string",
      "retrieved_context": "string",
      "retrieval_source": "SAME_DOCUMENT"
    }
  ]
}
```

- `start_index` / `end_index`는 **출력하지 않음** (백엔드 계산)
- `RETRIEVAL_ERROR`는 `retrieved_context` 필수 (백엔드 validator)
- `retrieval_source`는 `SAME_DOCUMENT` 또는 `SYNTHETIC`

---

## 백엔드 `.env` (8번 연동 시)

```env
LANGFLOW_STAGE2_FLOW_ID=
LANGFLOW_STAGE2_GEN_PROMPT_NODE_ID=Prompt-fwk9l
LANGFLOW_STAGE2_EXT_PROMPT_NODE_ID=Prompt-We0Ob
```

`EXT` 노드 ID는 planner(`Prompt-We0Ob`)를 가리킨다.

---

## 프롬프트 소스

| 파일 | 노드 |
|------|------|
| `prompts/stage2/error-plan.md` | `Prompt-We0Ob` |
| `prompts/stage2/hallucination-gen.md` | `Prompt-fwk9l` |

동기화: `python scripts/patch-stage2-flow-plan-first.py` 또는 Langflow UI Export.

---

## v1 → v2 변경 요약

| v1 | v2 |
|----|-----|
| EXAONE 먼저 생성 | OpenAI **오류 계획** 먼저 |
| OpenAI 사후 추출 | Plan Formatter (LLM 없음) |
| `start_index` LLM 생성 | 백엔드 계산 |
| 청크 후보 없음 | `candidate_chunks` 입력 |
