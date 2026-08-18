# Stage 1 RAG Chat — handoff (요약)

## TL;DR

- Langflow: **생성만** (검색·visualization은 백엔드)
- 백엔드가 `context` / `temperature`를 tweaks로 주입
- 검색 품질에 따라 context에 **`[내부모드: WEAK|STRONG]`** 래핑 (+ WEAK 시 시대착오 노이즈)
- UI `retrieved_chunk_previews`에는 **실청크만** (노이즈·모드 헤더 미포함)
- Prompt `context`는 Parser 등과 **연결하지 말 것** (tweaks가 무시됨)

---

## 1) 산출물 / 메타

- **Flow JSON:** `flows/stage1-rag-chat.json`
- **Prompt:** `prompts/stage1/rag-chat.md` (하단 블록을 Langflow Prompt에 **재붙여넣기**)

| 항목 | 값 |
|------|-----|
| Flow ID | `06ffd41a-8e76-45bd-b5ff-22c167d5f4bf` |
| Langflow | `1.10.0` |
| LLM | `gpt-4o-mini` |
| temperature 기본값 | `1.0` |

---

## 2) flow 구조

- `Chat Input` → `Prompt Template`(variables: `context`, `message`) → `OpenAI`(temperature) → `Chat Output`

### 프롬프트 정책

- context의 **내부모드가 최우선**
- **WEAK**: 올바른 사전 지식 보강 금지 → 시대착오를 사실처럼 단정
- **STRONG**: 교재만 · 퀴즈 정답 한 줄 떠먹이기 금지
- 파라미터 이름 설명 금지 · plain text만

### 백엔드 WEAK 판정 (기본값)

- `approx_context_chars < 350` **또는**
- `vector_search_score < 0.42` **또는**
- `chunk_size <= 50 and top_k <= 2`

코드: `backend/app/services/stage1_context.py`

---

## 3) 의도적으로 안 한 부분

### A. 검색을 flow에서 안 함

- `chunk_size/top_k`는 백엔드 검색 전용. Langflow는 `context` 생성만.

### B. visualization을 flow에서 안 만듦

- 숫자는 백엔드 조립 (`retrieved_chunk_previews` 등).

### C. Stage2식 고정 환각 문장

- 파라미터와 무관하게 답이 고정되면 1단계 목표와 충돌 → WEAK일 때만 노이즈 주입.

---

## 4) 연동 메모

- `message` → Chat Input / `context` → Prompt / `temperature` → OpenAI
- `.env`의 `LANGFLOW_STAGE1_*_NODE_ID` 확인
- 프롬프트 파일 수정 후 **반드시 Langflow Prompt 노드에 붙여넣기**

---

## 5) 로컬 검증

- `50 / 1~2 / 1.0` → 시대착오·황당 단정
- `500+ / 5+ / 0.2` → 교재 근거, UI preview에 노이즈 없음

---

## 6) 시크릿 체크

```bash
grep -E 'sk-' flows/stage1-rag-chat.json || echo "OK"
```
