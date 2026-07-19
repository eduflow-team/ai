# Stage 2 — 로컬 테스트 스크립트

## Flow Import (UI 권장)

1. http://localhost:7860 접속
2. **Upload a flow** 또는 JSON 드래그
3. `flows/stage2-hallucination-gen.json` 선택
4. Language Model → Ollama, `exaone3.5:7.8b`, URL `http://host.docker.internal:11434`
5. 저장 후 **API** 탭에서 Flow ID 복사

## Ollama (호스트 PC) 연결

```powershell
.\scripts\check-ollama-langflow.ps1
```

`docker-compose.yml`에 `OLLAMA_BASE_URL=http://host.docker.internal:11434` 설정됨.

## curl 테스트

```powershell
$env:LANGFLOW_API_KEY = "<UI Settings → API Keys>"
$env:FLOW_ID = "<Import 후 Flow ID>"
.\scripts\stage2-test.ps1
```

## Flow JSON 수정

프롬프트·노드 튜닝은 **Langflow UI**에서 하고 **Export → `flows/stage2-hallucination-gen.json` 덮어쓰기**.

프롬프트 문서 동기화: `prompts/stage2/hallucination-gen.md`, `error-extraction.md`
