# Stage 1 — 파라미터 조절 · RAG

**학습 목표:** chunk_size, top_k, temperature를 조절하며 **검색된 자료 범위**에 따라 답변 품질이 달라지는지 비교한다. 좋은 파라미터 = 관련 청크가 잘 잡히고 답이 원문에 가깝다.

**담당:** 1단계 flow 개발자가 아래 파일을 작성한다.

## 파일

| 파일 | 상태 |
|------|------|
| `system.template.md` | 틀 — 복사 후 `rag-chat.md` 등으로 저장 |
| `rag-chat.md` | Stage 1 RAG 튜터 프롬프트 (자료만 근거) |
| `handoff.md` | flow 구현·연동 handoff (AI 총괄·백엔드용) |

## 페르소나

사용하지 않음. 중립적 교육용 AI 튜터 톤.

## API 연동 참고 (Notion)

- `POST /student/assignments/{id}/step1/chat`
- 입력: `message`, `parameters` (chunk_size, top_k, temperature)
- 출력: `ai_response`, `rag_process_visualization` (`retrieved_chunk_previews` 포함)

연동 상세·역할 분담: **[handoff.md](./handoff.md)**

## baseline (프롬프트)

상세 규칙은 [`rag-chat.md`](./rag-chat.md)를 따릅니다.

- 검색된 청크(`context`)에 **있는 내용만** 답한다. 없으면 확인할 수 없다고 한다.
- 자료 밖 사실 창작 금지. 문장 수 강제 없음.
- 파라미터 이름을 학생에게 설명하지 않는다.
- LLM은 답변 본문(plain text)만 출력한다.
