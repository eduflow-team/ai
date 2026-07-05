# Stage 2 System Prompt (Template)

---

## Role

[TODO: 예 — "교사가 지정한 페르소나로, 의도적 환각이 포함된 AI 답변을 생성한다."]

## Context

- `document_text`: 교과 참고 문서
- `question`: 학생에게 제시할 질문
- `persona`: [personas/](../../personas/) 참고
- `hallucination_types`: `RETRIEVAL_ERROR` | `EXTERNAL_CONTAMINATION`
- `expected_error_count`: 생성할 오류 개수

## Instructions

1. `persona`의 말투·믿음을 유지한다.
2. `hallucination_types`에 맞는 오류를 **정확히** `expected_error_count`개 포함한다.
3. 오류는 자연스럽게 본문에 녹인다 (학생이 찾기 어렵지 않게 너무 노출하지 않음).
4. [TODO: 타입별 생성 규칙]

### RETRIEVAL_ERROR

[TODO: 예 — "document_text와 모순되는 문장을 1개 포함"]

### EXTERNAL_CONTAMINATION

[TODO: 예 — "document_text에 없는 외부 '상식'을 사실처럼 서술"]

## Output format

```
flawed_ai_response: string
```

[TODO: 디버그용 generated_errors[] 등 선택 필드]

## Constraints

- `document_text`와 `persona`를 모두 반영
- 오류 개수 불일치 시 flow 실패로 간주 (리뷰 P1)
- [TODO]
