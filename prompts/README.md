# Prompts

Langflow **System Prompt** 표준 저장소입니다.

## 역할

| 작성 | 담당 |
|------|------|
| `_template-system.md`, `stage{N}/README.md` (틀) | AI/LLM |
| `stage{N}/*.md` 본문 | **해당 단계 flow 담당자** |

## 사용 방법

1. `stage{N}/` 아래 템플릿을 복사 (예: `stage1/system.template.md` → `stage1/rag-chat.md`)
2. `[TODO]` 구역만 채움
3. Langflow UI의 Prompt / System Message 컴포넌트에 붙여넣기
4. flow Export → `flows/stage{N}-....json` PR

## 공통 규칙

- 존댓말, 교육용 톤
- API Request/Response 필드는 **Notion API 명세** 참조 (여기서 REST 중복 정의하지 않음)
- `.cursor/rules/prompt-persona.mdc` 준수

## 디렉터리

```
prompts/
├── README.md                 ← 이 파일
├── _template-system.md       ← 시스템 프롬프트 섹션 구조
├── stage1/                   ← 1단계 (RAG·파라미터)
├── stage2/                   ← 2단계 (의도적 환각)
├── stage3/                   ← 3단계 (명세 확정 후)
└── stage4/                   ← 4단계 (보안, AI/LLM)
```
