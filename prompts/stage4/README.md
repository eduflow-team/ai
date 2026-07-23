# Stage 4 — 보안 실습 (프롬프트 인젝션)

**상태:** API 초안 작성 완료 · Langflow/백엔드 구현 대기  
**담당:** AI/LLM · 백엔드 (임정원)

## 목표

학생이 해커 역할로 AI에 프롬프트 인젝션을 시도하고, 비밀 키 탈취(클리어) 후
보안 분석 보고서를 제출한다.

## 파일

| 파일 | 용도 |
|------|------|
| `system.template.md` | Langflow 공통 Prompt Template |
| `defense-easy.md` | `EASY` → `{difficulty_prompt}` |
| `defense-normal.md` | `NORMAL` → `{difficulty_prompt}` |
| `defense-hard.md` | `HARD` → `{difficulty_prompt}` |

## 문서

| 경로 | 설명 |
|------|------|
| `docs/stage4-langflow-contract.md` | tweaks·출력·성공 판정 계약 |

## Notion API (`stage4`)

| Endpoint | Langflow |
|----------|----------|
| `POST /teacher/assignments/step4` | — |
| `GET /student/assignments/{id}/step4` | — |
| `POST /student/assignments/{id}/step4/chat` | **연동** |
| `POST /student/assignments/{id}/step4/submit` | — |

## 핵심 규칙

- 성공: `secret_key in ai_response` (백엔드 Rule)
- HARD는 매우 어려움이지 절대 불가 아님
- 보고서는 **클리어 후** 제출

## TODO

- [ ] Langflow UI에서 flow 구성 → `flows/stage4-security-chat.json` Export
- [ ] 노드 이름 안정화 후 `.env` Flow/노드 ID 연결
- [ ] 백엔드 `LangflowClient.run_stage4_chat` + API 구현
- [ ] EASY/NORMAL/HARD Playground 체감 테스트
