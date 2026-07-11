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

명세 원본: [API 명세서(변경)](https://app.notion.com/p/API-38f4eb81e0ec8022aabef9b9e2ce86e1) → 기능리스트 `stage1`

| Endpoint | Langflow | 요약 |
|----------|----------|------|
| `POST /teacher/assignments/step1` | 연동 (벡터화) | 교사 과제 생성 · 문서 업로드 |
| `GET /student/assignments/{id}/step1` | — | 과제 상세·기본 파라미터·시도 횟수 |
| `POST /student/assignments/{id}/step1/chat` | **연동 (RAG 채팅)** | 파라미터 반영 AI 응답 |
| `POST /student/assignments/{id}/step1/submit` | — (백엔드 G-Eval) | 최종 답변 제출·채점 |

### Langflow flow I/O (`step1/chat`)

**Request (tweaks / 입력)**

- `message`
- `parameters.chunk_size`, `parameters.top_k`, `parameters.temperature`

**Response (Output JSON)**

- `ai_response`
- `rag_process_visualization` — `total_chunks`, `retrieved_chunks`, `vector_search_score`

### 교사 과제 생성 (`step1`) — 벡터화 flow 참고

multipart: `subject`, `file`, `question`, `guideline`, `default_chunk_size`, `default_top_k`, `default_temperature`

### 학생 과제 상세 (`GET step1`) — UI·기본값 참고

- `parameter_explanations`, `default_parameters`
- `attempts` — 최대 3회
- `highest_score`, `best_parameters` (이력 없으면 `null`)

### 최종 제출 (`submit`) — 채점은 백엔드

입력: `final_parameters`, `selected_ai_response`  
출력: `evaluation_report` (`faithfulness_score`, `relevance_score`, `feedback`), `attempts`

연동 상세·역할 분담: **[handoff.md](./handoff.md)**

## baseline (프롬프트)

상세 규칙은 [`rag-chat.md`](./rag-chat.md)를 따릅니다.

- 검색된 청크(`context`)를 주요 근거로 답한다.
- 파라미터 이름을 학생에게 설명하지 않는다.
- LLM은 답변 본문(plain text)만 출력한다.
