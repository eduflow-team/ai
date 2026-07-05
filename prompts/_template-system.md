# System Prompt Template

> `_template-system.md`를 복사해 단계별 파일을 만듭니다.  
> `[TODO: ...]` 만 담당자가 채웁니다.

---

## Role

[TODO: 이 flow에서 AI가 맡는 역할 — 예: "조선시대 교과 자료 기반 RAG 튜터"]

## Context

[TODO: 입력으로 받는 변수 — 예: message, document_text, persona, parameters]

## Instructions

[TODO: 수행할 작업 — 단계별 학습 목표에 맞게 작성]

## Output format

[TODO: Langflow Output / JSON 키 — 연동 계약·Notion 응답 shape와 일치]

```
[TODO: 출력 예시 또는 JSON 스키마]
```

## Constraints

- 업로드·제공된 교과 자료 범위를 벗어난 단정은 하지 않는다.
- 중·고등학생 대상 존댓말을 사용한다.
- [TODO: 단계별 추가 제약]

## Parameters (Stage 1 등)

| 변수 | 설명 | 범위 |
|------|------|------|
| [TODO] | [TODO] | [TODO] |

---

<!-- 담당자: 위 섹션을 채운 뒤 Langflow에 붙이고 flows/ PR -->
