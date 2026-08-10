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
- `rag_process_visualization` — `total_chunks`, `retrieved_chunks`, `vector_search_score`, `retrieved_chunk_previews`

### 교사 과제 생성 (`step1`) — 벡터화 flow 참고

multipart: `subject`, `file`, `default_chunk_size`, `default_top_k`, `default_temperature`  
(`question`/`guideline`은 서버 고정·AI 생성)

### 학생 과제 상세 (`GET step1`) — UI·기본값 참고

- `parameter_explanations`, `default_parameters`
- `attempts` — 최대 3회
- `highest_score`, `best_parameters` (이력 없으면 `null`)

### 최종 제출 (`submit`) — 채점은 백엔드

입력: `final_parameters`, `selected_ai_response`  
출력: `evaluation_report` (`faithfulness_score`, `relevance_score`, `feedback`), `attempts`

상세: [`rag-chat.md`](./rag-chat.md), [`handoff.md`](./handoff.md)
