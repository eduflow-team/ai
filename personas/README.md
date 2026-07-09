# Personas

2단계(및 4단계)에서 **의도적 환각·역할 연기**에 쓰는 페르소나 가이드입니다.

## 누가 작성하나

| 대상 | 작성 주체 | 저장 위치 |
|------|-----------|-----------|
| **실제 과제 페르소나** | **교사** (서비스 UI) | DB — API `persona` 필드 |
| **예시·작성 가이드** | AI/LLM | 이 저장소 (`personas/`) |

과제마다 교사가 입력한 `persona` 문자열이 Langflow flow에 **그대로** 주입됩니다.  
`personas/`에 과제별 파일을 쌓지 않습니다.

## API와의 관계

`POST /teacher/assignments/step2` Request Body의 `persona`와 flow 입력이 **동일한 문자열**이어야 합니다.

```json
"persona": "장영실이 연을 만들었다고 믿고, 자격루를 서양 기술이라고 주장하는 선생님"
```

환각 **개수·타입**은 `hallucination_types`, `expected_error_count`로 별도 제어합니다.  
`persona`만으로 교육 목표가 달성되도록 flow 시스템 프롬프트가 보완해야 합니다.

## 이 저장소의 용도

| 파일 | 용도 |
|------|------|
| `_template.md` | 교사 UI 작성 가이드·기획 참고 (폼 항목 설계용) |
| `examples/jangyeongsil-teacher.md` | API 명세 예시, flow 테스트·PR **리뷰 기준선** |

## flow 개발·리뷰 시

1. `examples/` 문장으로 Playground·curl 테스트
2. **임의 `persona` 문자열**에도 `hallucination_types`·`expected_error_count`가 지켜지는지 확인
3. flow PR 리뷰: [flow-pr-review.mdc](../.cursor/rules/flow-pr-review.mdc)

## 파일

```
personas/
├── README.md
├── _template.md              ← UI 가이드 원본 (Git만)
└── examples/
    └── jangyeongsil-teacher.md   ← API 예시·리뷰 기준선
```
