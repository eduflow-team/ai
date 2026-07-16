# Stage 2 백엔드 구현 가이드 (참고용)

> **이 문서는 `ai` 저장소에만 둡니다.** 실제 구현은 [backend](https://github.com/eduflow-team/backend)에서 진행하세요.  
> Langflow 연동 계약: [`stage2-langflow-contract.md`](./stage2-langflow-contract.md)

## 목표

`POST /api/v1/teacher/assignments/step2` 에서:

1. 교사가 업로드한 문서 → `documents.raw_text` 추출
2. Langflow `stage2-hallucination-gen` 호출 → `flawed_ai_response` + `generated_errors[]` 수신
3. `assignments`, `stage2_assignment_details`, `stage2_error_answers` 저장

---

## 1. 환경 변수 (`backend/.env`)

```env
LANGFLOW_URL=http://localhost:7860
LANGFLOW_API_KEY=<Langflow UI에서 발급>
LANGFLOW_STAGE2_FLOW_ID=<Import 후 Flow ID>
```

`app/core/config.py` 예시:

```python
LANGFLOW_URL: str = "http://localhost:7860"
LANGFLOW_API_KEY: str = ""
LANGFLOW_STAGE2_FLOW_ID: str = ""
```

---

## 2. Langflow 클라이언트

`app/clients/langflow_client.py` (신규):

```python
import json
import httpx

from app.core.config import settings


class Stage2LangflowResult:
    def __init__(self, flawed_ai_response: str, generated_errors: list[dict]) -> None:
        self.flawed_ai_response = flawed_ai_response
        self.generated_errors = generated_errors


class LangflowClient:
    PROMPT_GEN = "Prompt-s2gen"
    PROMPT_EXT = "Prompt-s2ext"

    def __init__(self) -> None:
        self.base_url = settings.LANGFLOW_URL.rstrip("/")
        self.api_key = settings.LANGFLOW_API_KEY

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def run_stage2_hallucination(
        self,
        *,
        document_text: str,
        question: str,
        persona: str,
        hallucination_types: list[str],
        expected_error_count: int,
    ) -> Stage2LangflowResult:
        types_str = ", ".join(hallucination_types)
        count_str = str(expected_error_count)
        shared = {
            "document_text": document_text,
            "hallucination_types": types_str,
            "expected_error_count": count_str,
        }
        payload = {
            "input_value": "",
            "tweaks": {
                self.PROMPT_GEN: {
                    **shared,
                    "question": question,
                    "persona": persona,
                },
                self.PROMPT_EXT: shared,
            },
        }
        url = f"{self.base_url}/api/v1/run/{settings.LANGFLOW_STAGE2_FLOW_ID}"
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
        return self._parse_stage2_outputs(data)

    def _parse_stage2_outputs(self, data: dict) -> Stage2LangflowResult:
        texts: list[str] = []
        for run_output in data.get("outputs", []):
            for inner in run_output.get("outputs", []):
                results = inner.get("results", {})
                message = results.get("message") or results.get("text")
                if isinstance(message, dict) and message.get("text"):
                    texts.append(message["text"])
                elif isinstance(message, str):
                    texts.append(message)

        if not texts:
            raise ValueError("Langflow 응답이 비어 있습니다.")

        flawed = texts[0]
        errors: list[dict] = []
        if len(texts) > 1:
            raw = texts[1].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(raw)
            errors = parsed.get("generated_errors", parsed if isinstance(parsed, list) else [])

        return Stage2LangflowResult(flawed_ai_response=flawed, generated_errors=errors)
```

> 노드 ID는 flow JSON 고정값 `Prompt-s2gen`, `Prompt-s2ext` 사용. Import 후 API 탭에서 확인.

---

## 3. API 스키마 (예시)

```python
# app/schemas/stage2.py
from pydantic import BaseModel, Field


class Step2CreateRequest(BaseModel):
    title: str
    document_id: int | None = None
    document_text: str | None = None  # 파일 업로드 시 서비스에서 추출
    question: str
    persona: str = Field(max_length=100)
    hallucination_types: list[str]  # ["RETRIEVAL_ERROR", "PERSONA_BIAS"]
    expected_error_count: int = Field(ge=1, le=5)


class Step2CreateResponse(BaseModel):
    assignment_id: int
    question: str
    flawed_ai_response: str
    expected_error_count: int
    generated_errors: list[dict] = []
```

---

## 4. 서비스 흐름

```python
# app/services/stage2_service.py (개념)
async def create_step2_assignment(body: Step2CreateRequest) -> Step2CreateResponse:
    raw_text = body.document_text or await document_repo.get_raw_text(body.document_id)
    result = await langflow.run_stage2_hallucination(...)
    assignment = await assignment_repo.create(stage=2, title=body.title)
    detail = await stage2_detail_repo.create(
        assignment_id=assignment.id,
        hallucinated_ai_answer=result.flawed_ai_response,
        ...
    )
    for err in result.generated_errors:
        await stage2_error_answer_repo.create(assignment_id=assignment.id, detail_id=detail.id, **err)
```

---

## 5. 학생 조회 (`GET /student/assignments/{id}/step2`)

응답에 포함할 필드 (스텁 → 실구현):

| 필드 | 출처 |
|------|------|
| `question` | `stage2_assignment_details.question` |
| `flawed_ai_response` | `stage2_assignment_details.hallucinated_ai_answer` |
| `expected_error_count` | `stage2_assignment_details.expected_error_count` |

하이라이트·수정 제출(8~21단계)은 Langflow 없이 백엔드만 처리.

---

## 6. 로컬 연동 체크리스트

- [ ] Ollama + OpenAI API Key (Langflow Settings)
- [ ] Langflow Import: `flows/stage2-hallucination-gen.json`
- [ ] Language Model → Ollama, URL `http://host.docker.internal:11434`
- [ ] Playground Run (장영실 baseline)
- [ ] API Key 발급 → `LANGFLOW_API_KEY`
- [ ] Flow ID 복사 → `LANGFLOW_STAGE2_FLOW_ID`
- [ ] `scripts/stage2-test.ps1` 또는 curl로 `/api/v1/run/{FLOW_ID}` 확인
- [ ] backend `LangflowClient` 연결 후 `POST step2` E2E

---

## 7. 이후 (선택)

- 출력 노드 단일 JSON Merge 컴포넌트
