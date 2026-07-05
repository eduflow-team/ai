# Stage 2 — 의도적 환각 · 비판적 검증

**학습 목표:** AI 답변 속 의도적 오류를 찾고 수정한다.

**담당:** 2단계 flow 개발자

## 파일

| 파일 | 상태 |
|------|------|
| `system.template.md` | 틀 |
| `hallucination-gen.md` | [TODO] 담당자 작성 |

## 페르소나

**필수.** API Request의 `persona`와 같은 계열로 동작해야 한다.  
템플릿: [personas/_template.md](../../personas/_template.md)  
예시: [personas/examples/jangyeongsil-teacher.md](../../personas/examples/jangyeongsil-teacher.md)

## 환각 타입 (API enum)

| 값 | 의미 |
|----|------|
| `RETRIEVAL_ERROR` | 잘못된 문서·리트리벌 오류 |
| `EXTERNAL_CONTAMINATION` | 교과 외 지식 혼입 |

`expected_error_count`개만큼 위 타입에 맞는 오류를 답변에 **의도적으로** 포함한다.

## API 연동 참고 (Notion)

- `POST /teacher/assignments/step2`
- 입력: `document_text`, `question`, `persona`, `hallucination_types[]`, `expected_error_count`
- 출력: `flawed_ai_response`
