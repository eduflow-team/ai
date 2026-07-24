# Stage 1 RAG Chat — handoff (요약)

## TL;DR

- **내가 구현한 것:** Langflow에서 **답변 생성(generation)** 만 하는 Stage 1 flow + 프롬프트
- **의도적으로 안 한 것:** 문서 검색(RAG)·시각화 숫자 조립은 **백엔드 담당**이라 flow에서 제외/미사용
- **다음 사람이 할 것:** AI 총괄이 백엔드에서 `context`를 주입하고 OpenAI `temperature`를 **tweaks로 덮어쓰기**

---

## 1) 산출물 / 메타

- **Flow JSON:** `flows/stage1-rag-chat.json`
- **Prompt:** `prompts/stage1/rag-chat.md`

| 항목 | 값 |
|------|-----|
| Flow ID | `06ffd41a-8e76-45bd-b5ff-22c167d5f4bf` |
| Langflow | `1.10.0` |
| LLM | `gpt-4o-mini` |
| temperature 기본값 | `1.0` |

---

## 2) 내가 어떻게 구현했나 (flow 구조)

### 운영에서 실제로 쓰는 경로

- `Chat Input` → `Prompt Template`(variables: `context`, `message`) → `OpenAI`(temperature) → `Chat Output`

### 프롬프트 정책

- 학생에게 `chunk_size/top_k/temperature` **설명하지 않음**
- 출력은 **plain text만** (JSON/Markdown 금지)
- **검색된 `context`에 있는 내용만** 사용. 없으면 「학습 자료에서 확인할 수 없습니다」
- 자료 밖 기관·인물·일화 **창작 금지**. 문장 수 강제 없음
- `temperature`는 문체만 조절 (새 사실 추가 금지)

---

## 3) 의도적으로 안 한 부분 & 이유

### A. 검색(`chunk_size`, `top_k`)을 flow에서 안 함

- Stage 1 API 계약상 `chunk_size/top_k`는 **백엔드가 검색에 사용**
- Langflow는 검색 결과 텍스트를 **`context`로 주입받아 생성만** 담당하도록 분리

### B. `rag_process_visualization`을 flow에서 만들지 않음

- 숫자는 LLM이 만들면 **환각** 위험이 있어, **백엔드가 조립**하도록 분리

### C. PGVector 브랜치를 “로컬 실험용”으로만 둠 (운영 미사용)

- `document_chunks` 스키마/embedding 상태 이슈로 **운영에서 신뢰 불가**
- Export JSON 기준으로 `Chat Input → PGVector search_query` 연결이 없어 **Playground 검색이 동작하지 않을 수 있음**
- 결론: 운영에서는 **백엔드 `context` 주입만 사용**

---

## 4) 다음 사람이 해야 할 일 (AI 총괄 / 백엔드)

### AI 총괄 (Langflow HTTP 연동)

- 매핑
  - `message` → Chat Input
  - `context`(검색 결과 텍스트) → Prompt Template의 `context`
  - `temperature` → OpenAI 노드의 `temperature` (tweaks로 덮어쓰기)
- 응답
  - Chat Output 텍스트 → `ai_response` (plain text)

**tweaks 대상 노드 ID (Export JSON 기준)**

- Chat Input: `ChatInput-rk5X4` (`input_value`)
- Prompt Template: `Prompt Template-gnr3c` (`context`)
- OpenAI: `OpenAIModel-seW7A` (`temperature`)
- Chat Output: `ChatOutput-laO0L` (출력 text)

> flow를 다시 저장/재export하면 노드 ID가 바뀔 수 있어, 연동 전 JSON에서 확인 필요.

### 백엔드

- `chunk_size`, `top_k`로 검색 → 청크를 합쳐 **`context` 문자열** 생성
- `rag_process_visualization` 조립 (`total_chunks`, `retrieved_chunks`, `vector_search_score`, `retrieved_chunk_previews`)

---

## 5) PR용 로컬 테스트(내가 한 방식)

- Prompt `{context}`에 **학습 자료 텍스트를 직접 붙여넣고** 테스트 (PGVector 경로 미사용)
- context 양·관련성을 바꿔 비교 (짧은 검색 vs 충분한 검색)
- temperature만 바꿀 때는 문체 차이만 나고 **새 사실이 추가되면 안 됨**

---

## 6) 시크릿 체크

```bash
grep -E 'sk-' flows/stage1-rag-chat.json || echo "OK"
```
