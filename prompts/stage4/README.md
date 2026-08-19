# Stage 4 — 보안 실습 (프롬프트 인젝션)

**상태:** Langflow 연동·힌트·채점·난이도 캘리브레이션 반영  
**담당:** AI/LLM · 백엔드 (임정원)  
**LLM:** Ollama `exaone3.5:7.8b` (`host.docker.internal:11434`)  
**Flow:** `flows/stage4-security-chat.json`

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
| `docs/stage4-scoring.md` | 힌트 단계 · 채점 루브릭 (100점) |
| `docs/stage4-screenshots/playground-easy-clear.png` | EASY Playground 클리어 성공 (Ollama, PR용) |
| `docs/stage4-screenshots/playground-openai-refuse.png` | OpenAI는 동일 인젝션도 거절 (Ollama 전환 근거) |
| `docs/stage4-screenshots/playground-hard-clear.png` | HARD: 협박 거절 → JSON 우회 클리어 (PR용) |
| `docs/stage4-screenshots/flow-canvas.png` | Stage4 Langflow 캔버스 (Ollama EXAONE) |

## Notion API (`stage4`)

| Endpoint | Langflow |
|----------|----------|
| `POST /teacher/assignments/step4` | — |
| `GET /student/assignments/{id}/step4` | — |
| `POST /student/assignments/{id}/step4/chat` | **연동** |
| `POST /student/assignments/{id}/step4/submit` | — |

## 핵심 규칙

- 성공(클리어): AI 응답에 `secret_key` 문자열이 포함되면 성공
- 난이도 차이는 방어 프롬프트 강도만 (HARD는 단순 우회에서 키가 안 나오게)
- 보고서는 **클리어 후** 제출
- 채점: clear 40 + efficiency 30 + analysis 30 (`docs/stage4-scoring.md`)
- 힌트: 실패 2/4/6회 누적 시 level 1/2/3 (정답 문장 X, 방향만)

## TODO

- [x] Ollama EXAONE EASY 누설 Playground 확인
- [x] HARD Playground 체감 테스트
- [x] `flows/stage4-security-chat.json` Export
- [x] 힌트·채점 계약 (`docs/stage4-scoring.md`)
- [x] Langflow Prompt `{hint}` + 백엔드 Stage4 API
- [x] 난이도 캘리브레이션·채점 고도화
