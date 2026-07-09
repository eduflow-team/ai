# EduFlow AI (Langflow)

EduFlow 프로젝트의 **Langflow 플로우·프롬프트·로컬 개발 환경**을 관리하는 저장소입니다.

> REST API 필드 정의·에러 코드는 API 명세서를 따릅니다.  
> 이 문서는 Langflow 로컬 환경 구축과 flow JSON PR 방법만 다룹니다.

백엔드 저장소: [eduflow-team/backend](https://github.com/eduflow-team/backend)

---

## 사전 요구 사항

- [Docker Desktop](https://docs.docker.com/get-docker/) (또는 Docker Engine + Compose v2)
- Git ([CONTRIBUTING.md](./CONTRIBUTING.md) 컨벤션 준수)

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/eduflow-team/ai.git
cd ai

# 2. 환경 변수 파일 생성
cp .env.example .env

# 3. Langflow 실행
docker compose up -d

# 4. 브라우저 접속
open http://localhost:7860
```

최초 실행 시 `langflowai/langflow:1.10.0` 이미지 다운로드에 몇 분 걸릴 수 있습니다.

---

## API Key 발급 (개인별)

1. http://localhost:7860 접속 후 계정 생성(로컬 전용)
2. **Settings → API Keys**에서 키 발급
3. `.env`의 `LANGFLOW_API_KEY`에만 입력
4. **키 값은 팀 채널에 공유하지 않습니다**

백엔드 연동용 `LANGFLOW_URL` / `FLOW_ID` 설정은 `backend` 저장소에서 관리합니다.

---

## 디렉터리 구조

```
ai/
├── .cursor/rules/       # Cursor AI 규칙 (Langflow·프롬프트·flow 리뷰)
├── docker-compose.yml   # Langflow + PostgreSQL (버전 고정)
├── .env.example
├── prompts/             # 시스템 프롬프트 틀 (단계 담당자가 채움)
├── personas/            # 페르소나 틀·예시 (2단계 등)
├── flows/               # UI에서 Export한 flow JSON
├── CONTRIBUTING.md      # 팀 Git 컨벤션
└── README.md
```

### prompts / personas

| 작성 | 담당 |
|------|------|
| `_template*.md`, `stage*/README.md`, `examples/` | AI/LLM |
| 단계별 프롬프트·페르소나 **본문** | 1·2단계 flow 담당자 |

자세한 규칙: [prompts/README.md](./prompts/README.md), [personas/README.md](./personas/README.md)

---

## Flow 작업 · PR 규칙

1. Langflow UI에서 플로우 작성
2. **Export** → `flows/{stage}-{기능}.json` 저장  
   - 예: `flows/stage1-rag-chat.json`, `flows/stage2-hallucination-gen.json`
3. `main`에서 `feat/...` 브랜치 생성 후 PR
4. PR에 Playground 스크린샷 + 로컬 curl 테스트 결과 첨부

### Flow JSON PR 체크리스트

- [ ] API Key·시크릿이 JSON에 포함되지 않았는지 확인
- [ ] 파일명 규칙 준수
- [ ] Playground에서 입출력이 API 명세와 일치하는지 확인 (리뷰: AI 담당자)

---

## 로컬 API 테스트 (curl)

UI에서 flow를 저장한 뒤 **Flow ID**를 확인하고, 본인 API Key로 테스트합니다.

```bash
curl -X POST "http://localhost:7860/api/v1/run/{FLOW_ID}" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${LANGFLOW_API_KEY}" \
  -d '{
    "input_value": "테스트 메시지",
    "tweaks": {}
  }'
```

Flow 입출력 필드명(tweaks 키)은 백엔드 팀과 합의한 연동 계약을 따릅니다.

---

## 자주 쓰는 명령

```bash
# 로그 확인
docker compose logs -f langflow

# 중지
docker compose down

# 데이터까지 초기화 (flow·DB 전부 삭제)
docker compose down -v
```

---

## 버전 정책

- Langflow 이미지: `langflowai/langflow:1.10.0` (팀 전원 동일 버전 사용)
- 버전 변경 시 `docker-compose.yml` 수정 후 팀 채널에 공지

---

## Git 워크플로

[CONTRIBUTING.md](./CONTRIBUTING.md)와 동일합니다.

```bash
git checkout main
git pull origin main
git checkout -b feat/stage1-rag-chat
# 작업 후 PR → main
```

---

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `7860` 포트 점유 | 다른 프로세스 종료 또는 `docker-compose.yml` 포트 변경 |
| 컨테이너 재시작 후 flow 사라짐 | `docker compose down -v` 사용 여부 확인 (볼륨 삭제됨) |
| 이미지 pull 실패 | Docker 로그인·네트워크 확인 후 `docker compose pull` |

---

## 역할 분담

| 영역 | 담당 |
|------|------|
| 이 저장소 (Docker, flow JSON, 프롬프트) | AI/LLM |
| `backend` (FastAPI, DB, Langflow HTTP 클라이언트) | 백엔드 |
| API 명세 (Notion) | 백엔드 (참조) |
