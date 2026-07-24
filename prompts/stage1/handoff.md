# Stage 1 RAG Chat — handoff (요약)

## TL;DR

- Langflow: **생성만** (검색·visualization은 백엔드)
- 백엔드가 `context` / `temperature`를 tweaks로 주입 (연동 완료)
- Prompt `context`는 Parser 등과 **연결하지 말 것** (tweaks가 무시됨)

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
- **답변은 항상 작성** (거절 / 「확인할 수 없습니다」만 출력 금지)
- 검색 자료가 충분하면 **교재 우선**, 빈약하면 일반 지식 보완 허용(틀린 답 가능)
- `temperature` 높을수록 자유로운(부정확할 수 있는) 서술 허용

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

## 4) 연동 메모

- `message` → Chat Input / `context` → Prompt / `temperature` → OpenAI
- 노드 ID는 re-export 시 바뀔 수 있음 → `.env`의 `LANGFLOW_STAGE1_*_NODE_ID` 확인
- 백엔드: 검색 → `context` 조립 + `retrieved_chunk_previews`
---

## 5) PR용 로컬 테스트(내가 한 방식)

- Prompt `{context}`에 **학습 자료 텍스트를 직접 붙여넣고** 테스트 (PGVector 경로 미사용)
- context 양·temperature를 바꿔 비교
- 짧은 검색+고온 → 틀린/부정확한 답이 **나와야** 함(거부 금지)
- 긴 검색+저온 → 교재에 가까운 답

---

## 6) 시크릿 체크

```bash
grep -E 'sk-' flows/stage1-rag-chat.json || echo "OK"
```
