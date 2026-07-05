# Stage 1 — 파라미터 조절 · RAG

**학습 목표:** chunk_size, top_k, temperature를 조절하며 RAG 답변 품질을 비교한다.

**담당:** 1단계 flow 개발자가 아래 파일을 작성한다.

## 파일

| 파일 | 상태 |
|------|------|
| `system.template.md` | 틀 — 복사 후 `rag-chat.md` 등으로 저장 |
| `rag-chat.md` | [TODO] 담당자 작성 |

## 페르소나

사용하지 않음. 중립적 교육용 AI 튜터 톤.

## API 연동 참고 (Notion)

- `POST /student/assignments/{id}/step1/chat`
- 입력: `message`, `parameters` (chunk_size, top_k, temperature)
- 출력: `ai_response`, `rag_process_visualization`

## baseline (모든 Stage 1 프롬프트에 포함 권장)

- 검색된 청크(context)에 근거해 답한다.
- context에 없는 내용은 "자료에 없습니다"라고 말한다.
