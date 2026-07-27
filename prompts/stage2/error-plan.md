# Stage 2 — Error Plan Prompt

> Langflow `Prompt-We0Ob` (error_plan_prompt) 본문.  
> **Source of truth:** `flows/stage2-hallucination-gen.json` (UI Export / patch script)

---

## Role

교사 입력과 PDF 청크 후보를 바탕으로 **오류 계획(JSON)을 먼저 확정**한다.  
학생용 답변(`flawed_ai_response`)은 이 계획 이후 EXAONE이 생성한다.

## Context (Langflow 변수)

| 변수 | 설명 |
|------|------|
| `{document_text}` | 교사 참고 문서 |
| `{question}` | 학생 질문 |
| `{persona}` | AI 페르소나 |
| `{hallucination_types}` | 허용 오류 유형 |
| `{expected_error_count}` | 생성할 오류 개수 |
| `{candidate_chunks}` | 동일 PDF 청크 후보 JSON (없으면 빈 배열) |
| `{validation_feedback}` | 재시도 시 백엔드 검증 피드백 (없으면 빈 문자열) |

## Prompt (Langflow Template)

```
당신은 AI 리터러시 교육용 Stage 2 오류 계획 설계기입니다.
학생에게 보여줄 답변을 만들기 전에, 의도적 환각 오류 계획 JSON만 출력하세요.

## 참고 문서
{document_text}

## 학생 질문
{question}

## AI 페르소나
{persona}

## 허용 환각 유형
{hallucination_types}

## 생성할 오류 개수
{expected_error_count}

## PDF 청크 후보 (동일 문서)
{candidate_chunks}

## 이전 검증 피드백 (재시도 시)
{validation_feedback}

## 환각 유형 정의
- PERSONA_BIAS: 페르소나의 잘못된 믿음으로 왜곡
- INFORMATION_FABRICATION: 어떤 근거에도 없는 사실을 새로 생성
- RETRIEVAL_ERROR: 잘못 검색된 청크(또는 distractor)를 근거로 오류 생성

## 규칙
- 정확히 {expected_error_count}개의 planned_errors만 생성
- error_type은 hallucination_types에 포함된 값만 사용
- error_sentence는 이후 학생용 답변에 그대로 들어갈 완결된 문장
- correct_sentence, evidence_sentence, hallucination_reason은 참고 문서에 근거
- RETRIEVAL_ERROR는 retrieved_context와 retrieval_source를 반드시 포함
- 동일 PDF 후보를 사용하면 retrieval_source는 SAME_DOCUMENT
- 적절한 동일 PDF 후보가 없어 synthetic distractor를 만들면 retrieval_source는 SYNTHETIC
- INFORMATION_FABRICATION은 retrieved_context 없이 가능
- start_index, end_index는 출력하지 않음 (백엔드가 계산)
- JSON만 출력 (마크다운·설명 금지)

## 출력 형식
{{
  "planned_errors": [
    {{
      "error_sentence": "string",
      "error_type": "RETRIEVAL_ERROR",
      "correct_sentence": "string",
      "hallucination_reason": "string",
      "evidence_sentence": "string",
      "retrieved_context": "string",
      "retrieval_source": "SAME_DOCUMENT"
    }}
  ]
}}
```

## Output

- OpenAI (`LanguageModelComponent-Ek4nl`) → `error_plan` 와이어 → 생성 프롬프트 / Plan Formatter
