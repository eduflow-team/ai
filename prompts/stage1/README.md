# Stage 1 — RAG 퀴즈 탐색

**학습 목표:** 교사 퀴즈 1문제 → 학생이 파라미터를 조절하며 자료에서 근거를 탐색 → **본인 답** 제출.  
검색이 약하면(WEAK) 시대착오 환각이 보이도록 백엔드가 context를 래핑하고, 충분하면(STRONG) 교재 근거·힌트만 제공합니다.

## 파일

| 파일 | 상태 |
|------|------|
| `rag-chat.md` | Stage 1 프롬프트 (WEAK/STRONG 모드) |
| `handoff.md` | flow·연동 handoff |
| `system.template.md` | 틀 |

## API

| Endpoint | Langflow | 요약 |
|----------|----------|------|
| `POST /teacher/assignments/step1` | — (백엔드 벡터화) | 교사: PDF + `question` + `answer` + defaults |
| `GET /student/assignments/{id}/step1` | — | 문제·자료·기본 파라미터 (정답은 마감 후) |
| `POST /student/assignments/{id}/step1/chat` | **연동 (RAG 채팅)** | 자유 `message` + 파라미터 |
| `POST /student/assignments/{id}/step1/submit` | — | `student_answer` + `final_parameters` 채점 |

### Langflow

백엔드가 `{context}`에 `[내부모드: WEAK|STRONG]` (+ WEAK 노이즈)를 붙입니다.  
`rag-chat.md` 하단 블록을 Prompt 노드에 **수동 동기화**하세요.

상세: [`rag-chat.md`](./rag-chat.md), [`handoff.md`](./handoff.md)
