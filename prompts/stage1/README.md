# Stage 1 — 파라미터 조절 · RAG

**학습 목표:** chunk_size, top_k, temperature를 조절하며 RAG 답변 품질을 비교한다.

**담당:** 1단계 flow 개발자가 아래 파일을 작성한다.

## 파일

| 파일 | 상태 |
|------|------|
| `system.template.md` | 틀 — 복사 후 `rag-chat.md` 등으로 저장 |
| `rag-chat.md` | Stage 1 RAG 튜터 프롬프트 |
| `handoff.md` | flow 구현·연동 handoff (AI 총괄·백엔드용) |

## 페르소나

사용하지 않음. 중립적 교육용 AI 튜터 톤.

## API 연동 참고 (Notion)

- `POST /student/assignments/{id}/step1/chat`
- 입력: `message`, `parameters` (chunk_size, top_k, temperature)
- 출력: `ai_response`, `rag_process_visualization`

연동 상세·역할 분담: **[handoff.md](./handoff.md)**

## baseline (프롬프트)

상세 규칙은 [`rag-chat.md`](./rag-chat.md)를 따릅니다.

- 검색된 청크(`context`)를 주요 근거로 답한다.
- 파라미터 이름을 학생에게 설명하지 않는다.
- LLM은 답변 본문(plain text)만 출력한다.
