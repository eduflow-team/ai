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
- `hallucination_types[]` — `RETRIEVAL_ERROR`, `EXTERNAL_CONTAMINATION`
- `expected_error_count`
- 문서 텍스트는 백엔드가 업로드 파일에서 추출해 전달 (API Body: multipart `file`)

multipart 필드: `subject`, `file`, `question`, `persona`, `hallucination_types`, `expected_error_count`

**Response (Output JSON)**

- `flawed_ai_response`

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
