# Stage 1 — 파라미터 조절 · RAG

**학습 목표:** 첫 답(나쁜 파라미터) → 파라미터 조절 → 교재에 가까운 최적 답을 찾는다.  
답변은 **항상** 존재한다(거부 금지). 검색이 약하거나 temperature가 높으면 일반 지식으로 틀린 답이 날 수 있다.

## 파일

| 파일 | 상태 |
|------|------|
| `rag-chat.md` | Stage 1 프롬프트 (항상 답변 / 자료 우선·부족 시 보완 허용) |
| `handoff.md` | flow·연동 handoff |
| `system.template.md` | 틀 |

## API

- `POST /student/assignments/{id}/step1/chat`
- 출력: `ai_response`, `rag_process_visualization`(+`retrieved_chunk_previews`)

상세: [`rag-chat.md`](./rag-chat.md), [`handoff.md`](./handoff.md)
