# Stage 2 — 의도적 환각 · 비판적 검증

**학습 목표:** AI 답변 속 의도적 오류를 찾고 수정한다.

## 파일

| 파일 | 상태 | 용도 |
|------|------|------|
| `hallucination-gen.md` | ✅ | 1차 Ollama 프롬프트 (`Prompt-s2gen`) |
| `error-extraction.md` | ✅ | 2차 OpenAI 프롬프트 (`Prompt-s2ext`) |

## Flow

- `flows/stage2-hallucination-gen.json` — **7노드** UI 튜닝본 (Ollama + Sanitizer + OpenAI)
- 수정: Langflow UI Export → 위 JSON 덮어쓰기

## 환각 타입 (Notion API 기준)

| 값 | 의미 |
|----|------|
| `PERSONA_BIAS` | 페르소나 편향 |
| `INFORMATION_FABRICATION` | 정보 날조 |
| `RETRIEVAL_ERROR` | 잘못된 문서 검색 |

## 문서

| 경로 | 설명 |
|------|------|
| `docs/stage2-langflow-contract.md` | tweaks·출력·노드 ID |
| `docs/stage2-backend-implementation.md` | 백엔드 연동 |
| `scripts/stage2-test.ps1` | curl 테스트 |

## API 연동 참고 (Notion)

명세 원본: [API 명세서(변경)](https://app.notion.com/p/API-38f4eb81e0ec8022aabef9b9e2ce86e1) → 기능리스트 `stage2`

| Endpoint | Langflow | 요약 |
|----------|----------|------|
| `POST /teacher/assignments/step2` | **연동 (환각 생성)** | 교사 2단계 과제 생성 |
| `GET /student/assignments/{id}/step2` | — | 참고 문서·틀린 답변·시도 현황 |
| `POST /student/assignments/{id}/step2/highlight` | 연동 (검증) | 오답 하이라이트 제출·검증 (최대 5회) |
| `POST /student/assignments/{id}/step2/correction` | 연동 (피드백) | 빈칸 정답 최종 제출 (1회) |

### Langflow flow I/O — 환각 생성 (`teacher/step2`)

**Request (tweaks / 입력)**

- `question`
- `persona`
- `hallucination_types[]` — `PERSONA_BIAS`, `INFORMATION_FABRICATION`, `RETRIEVAL_ERROR`
- `expected_error_count`
- 문서 텍스트는 백엔드가 업로드 파일에서 추출해 전달 (API Body: multipart `file`)

multipart 필드: `subject`, `file`, `question`, `persona`, `hallucination_types`, `expected_error_count`

**Response (Output JSON)**

- `flawed_ai_response`
- `generated_errors[]` (Langflow 2차 출력, 백엔드 저장용)

API 성공 응답에 함께 반환: `assignment_id`, `question`, `expected_error_count` (백엔드 조합)

### 학생 과제 상세 (`GET step2`) — UI·검증 flow 참고

- `reference_document_text`, `flawed_ai_response`, `total_errors_to_find`
- `attempts` — 최대 5회
- `cleared_highlights` — 이전 시도에서 맞춘 구간 (없으면 `[]`)

### 하이라이트 검증 (`highlight`)

**Request:** `submissions[]` — `highlighted_text`, `student_reason`  
**Response:** `results[]` — `is_correct`, `evaluation_report` (`location_match_score`, `reasoning_score`, `ai_feedback`), `correct_answer` (정답 시만)

### 빈칸 정답 제출 (`correction`)

**Request:** `corrections[]` — `original_highlight`, `student_answer`  
**Response:** `is_passed`, `final_correct_sentence`, `feedback_details[]` (`hallucination_reason`, `reference_evidence`)

## baseline (모든 Stage 2 프롬프트에 포함 권장)

- `persona`·`hallucination_types`·`expected_error_count`를 반드시 준수한다.
- 의도적 오류는 참고 문서(`reference_document_text` / 업로드 파일)와 대비해 검증 가능해야 한다.
