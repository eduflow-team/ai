# Personas

2단계(및 4단계)에서 **의도적 환각·역할 연기**에 쓰는 페르소나 정의입니다.

## 역할

| 작성 | 담당 |
|------|------|
| `_template.md`, `examples/` (기준선) | AI/LLM |
| 과제별 페르소나 본문 | **2단계 담당자** (또는 교사 UI 입력 → flow가 그대로 사용) |

## API와의 관계

2단계 과제 생성 API의 `persona` 필드와 **동일한 문장**을 flow에 주입할 수 있어야 한다.

## 사용 방법

1. `_template.md` 복사
2. `[TODO]` 필드 채움
3. Langflow Prompt 변수 또는 API `persona` 문자열로 전달
4. `personas/`에 저장 (선택) + flow PR

## 파일

```
personas/
├── README.md
├── _template.md
└── examples/
    └── jangyeongsil-teacher.md   ← API 명세 예시 (리뷰 기준선)
```
