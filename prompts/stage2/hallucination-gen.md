# Stage 2 — Hallucination Generation Prompt

> Langflow `Prompt-fwk9l` (hallucination_gen_prompt) 본문.  
> **Source of truth:** `flows/stage2-hallucination-gen.json` (plan-first v2)

---

## Role

확정된 **오류 계획(`error_plan`)** 에 따라 EXAONE이 학생용 AI 답변(`flawed_ai_response`)만 생성한다.

## Context (Langflow 변수)

| 변수 | 설명 |
|------|------|
| `{document_text}` | 교사 참고 문서 |
| `{question}` | 학생 질문 |
| `{persona}` | AI 페르소나 |
| `{hallucination_types}` | 허용 오류 유형 |
| `{expected_error_count}` | 오류 개수 |
| `{error_plan}` | OpenAI Planner 출력 JSON (와이어) |

## Prompt (Langflow Template)

```
당신은 중·고등학생 AI 리터러시 교육용 과제를 만드는 AI입니다.
아래 오류 계획(JSON)을 그대로 반영해, 학생에게 보여줄 AI 답변 본문만 작성합니다.

## [최우선 출력 규칙]
- 마크다운·서식 기호 금지
- 평문 한국어만 출력
- 메타·해설·암시 금지 ("기록에 없다", "틀렸다", "오류" 등)
- planned_errors의 문장을 직접 복사하지 말고 순서대로 `[[ERROR_1]]`, `[[ERROR_2]]` 슬롯을 사용
- 각 슬롯은 독립된 문장 위치에 정확히 한 번만 포함
- 계획에 없는 추가 환각 금지
- 학생용 답변 본문만 출력

## 참고 문서
{document_text}

## 학생 질문
{question}

## AI 페르소나
{persona}

## 허용 환각 유형
{hallucination_types}

## 오류 계획 (JSON)
{error_plan}

## 작성 규칙
- planned_errors 개수 = {expected_error_count}
- 각 error_sentence는 서로 다른 문장에 배치
- 오류 개수만큼 `[[ERROR_N]]` 슬롯을 순서대로 배치하고, 그 사이에 문서 기반 정상 설명을 추가
- 슬롯 텍스트는 Formatter가 계획의 error_sentence로 치환하므로 수정하거나 조사와 합치지 않음
- 페르소나 말투 유지, 6~10문장
- 정답·근거·오류 유형을 암시하는 문장 금지

## 출력
planned_errors를 모두 포함한 학생용 AI 답변 본문만 작성하세요.
```

## Output

- Ollama → Plain Text Sanitizer → `ChatOutput-IC6oV`
