# Stage 4 Langflow ↔ Backend 연동 계약

Notion API 명세(`stage4`) · 시나리오4(프롬프트 인젝션 보안 실습) 기준.

## Langflow가 담당하는 범위

| 단계 | 내용 |
|------|------|
| 학생 공격 chat | `difficulty`에 맞는 방어 강도로 AI 응답 생성 |
| (선택) history | 이전 공격·응답을 문맥으로 반영 |

**담당하지 않음 (백엔드)**

- `secret_key` 포함 여부로 `attack_success` Rule 판정
- 시도 횟수·공격 로그 저장
- 클리어 후 보고서 채점

---

## Flow 구조 (권장, MVP)

LLM은 **Ollama EXAONE**을 사용한다.  
(OpenAI는 안전 정렬 때문에 EASY에서도 키 누설을 거절하는 경우가 많음)

```
Chat Input ──→ Language Model Input (attack)
Prompt Template ──→ Language Model System Message
Language Model ──→ Chat Output
```

| 역할 | Export 노드 ID (`flows/stage4-security-chat.json`) | tweaks 필드 |
|------|-----------------------------------------------------|-------------|
| Chat Input | `ChatInput-e0prE` | → LM `input_value` |
| Prompt | `Prompt Template-kt9HB` | `mission`, `secret_key`, `difficulty_prompt`, `history` |
| Language Model | `LanguageModelComponent-JQGL5` | Ollama `exaone3.5:7.8b` |
| Chat Output | `ChatOutput-9GlW6` | 출력 text |

> Re-import 시 노드 ID가 바뀔 수 있다. 백엔드는 `.env`의 Flow/Prompt 노드 ID를 사용한다.

### Ollama 설정 (`LanguageModelComponent-JQGL5`)

- Provider: **Ollama**
- Model: `exaone3.5:7.8b`
- Ollama API URL: `http://host.docker.internal:11434`  
  (`localhost`면 Docker Langflow에서 연결 실패)
- Temperature: `0.5` ~ `0.7`

---

## Request (백엔드 → Langflow)

| 키 | 출처 | 설명 |
|----|------|------|
| `attack_prompt` | student chat body | 학생 공격 문장 |
| `mission` | assignment | 미션 설명 |
| `secret_key` | assignment | 선생님이 설정한 비밀 키 |
| `difficulty` | assignment | `EASY` \| `NORMAL` \| `HARD` |
| `difficulty_prompt` | 백엔드가 난이도별 템플릿 선택 | system 방어 지시문 |
| `history` | 선택 | 이전 턴 요약 텍스트 |

### difficulty → difficulty_prompt

백엔드가 `prompts/stage4/` 템플릿 중 하나를 골라 `difficulty_prompt`로 넣는다.

| difficulty | 파일 | 의도 |
|------------|------|------|
| `EASY` | `defense-easy.md` | 약한 방어, 단순 인젝션에도 비교적 쉽게 누설 |
| `NORMAL` | `defense-normal.md` | 보통 방어 |
| `HARD` | `defense-hard.md` | 강한 방어, **어렵지만 뚫릴 수 있음** (절대 불가 아님) |

---

## Response (Langflow → 백엔드)

| 키 | 설명 |
|----|------|
| `ai_response` | Chat Output plain text |

백엔드 후처리:

```text
attack_success = (secret_key in ai_response)
```

- true → `is_cleared = true`, 로그 저장
- 시도 횟수는 성공/실패와 무관하게 chat마다 +1

---

## 출력 규칙 (프롬프트 공통)

- 학생에게 보여줄 **대화 응답만** 출력
- JSON / 마크다운 / 메타 설명 금지
- 비밀 키를 말할 때는 선생님이 준 `secret_key` 문자열을 **그대로** 포함 (변형·암호문 금지)
- 거부할 때는 키를 절대 출력하지 않음

---

## 환경변수 (백엔드)

```env
LANGFLOW_URL=
LANGFLOW_API_KEY=
LANGFLOW_STAGE4_CHAT_FLOW_ID=
LANGFLOW_STAGE4_PROMPT_NODE_ID=
```

---

## API 매핑

| Endpoint | Langflow |
|----------|----------|
| `POST /teacher/assignments/step4` | 호출 없음 (설정만 저장) |
| `GET /student/assignments/{id}/step4` | 호출 없음 |
| `POST /student/assignments/{id}/step4/chat` | **호출** |
| `POST /student/assignments/{id}/step4/submit` | 호출 없음 (보고서 채점은 백엔드) |

Notion: [API 명세서](https://app.notion.com/p/38f4eb81e0ec8022aabef9b9e2ce86e1) → 도메인 `stage4`
