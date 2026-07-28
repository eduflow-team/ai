# Stage 2 — Error Plan Prompt

> Langflow `Prompt-We0Ob` (error_plan_prompt) 본문.  
> **Source of truth:** `flows/stage2-hallucination-gen.json` (UI Export / patch script)

---

## Role

교사 입력과 PDF 청크 후보를 바탕으로 **오류 계획(JSON)을 먼저 확정**한다.  
학생용 답변(`flawed_ai_response`)은 이 계획 이후 EXAONE이 생성한다.

## Context (Langflow 변수)

| 변수 | 설명 |
|------|------|
| `{document_text}` | 교사 참고 문서 |
| `{question}` | 학생 질문 |
| `{persona}` | AI 페르소나 |
| `{hallucination_types}` | 허용 오류 유형 |
| `{expected_error_count}` | 생성할 오류 개수 |
| `{candidate_chunks}` | 동일 PDF 청크 후보 JSON (없으면 빈 배열) |
| `{validation_feedback}` | 재시도 시 백엔드 검증 피드백 (없으면 빈 문자열) |

## Prompt (Langflow Template)

```
당신은 AI 리터러시 교육용 Stage 2 오류 계획 설계기입니다.
학생에게 보여줄 답변을 만들기 전에, 의도적 환각 오류 계획 JSON만 출력하세요.

## 참고 문서
{document_text}

## 학생 질문
{question}

## AI 페르소나
{persona}

## 허용 환각 유형
{hallucination_types}

## 생성할 오류 개수
{expected_error_count}

## PDF 청크 후보 (동일 문서)
{candidate_chunks}

## 이전 검증 피드백 (재시도 시)
{validation_feedback}

## 환각 유형 정의
- PERSONA_BIAS: 페르소나의 잘못된 믿음으로 왜곡
- INFORMATION_FABRICATION: 어떤 근거에도 없는 사실을 새로 생성
- RETRIEVAL_ERROR: 잘못 검색된 청크(또는 distractor)를 근거로 오류 생성

## 규칙
- 정확히 {expected_error_count}개의 planned_errors만 생성
- response_template은 학생에게 보여줄 6~10문장의 자연스러운 전체 답변
- response_template에는 planned_errors 대신 `[[ERROR_1]]`, `[[ERROR_2]]` 슬롯을 순서대로 정확히 한 번씩 사용
- 요청한 오류 개수를 넘는 `[[ERROR_N]]` 슬롯은 만들지 않음
- 각 슬롯은 독립된 문장 위치에 놓고 조사·접미사를 붙이지 않음
- response_template에서 오류를 정정하거나 암시하지 않음 ("하지만 사실", "잘못 이해", "헷갈림", "정확한 정보" 등 금지)
- response_template의 슬롯 외 문장은 참고 문서에 근거하고 계획에 없는 추가 환각을 포함하지 않음
- response_template의 슬롯 밖에서 error_sentence를 그대로 또는 비슷하게 다시 말하지 않음
- response_template의 정상 문장에 해당 오류의 correct_sentence나 같은 뜻의 정답을 넣지 않음
- 오류와 직접 충돌하는 사실은 피하고, 도입·시대 배경·다른 주제·일반적 마무리로 정상 문장을 구성
- error_type은 hallucination_types에 포함된 값만 사용
- error_type 배정은 선택이 아니라 입력 순서를 따르는 기계적 규칙
- planned_errors를 hallucination_types의 순서대로 하나씩 배정하고, 모든 허용 유형을 한 번 쓰기 전에는 같은 유형을 반복하지 않음
- expected_error_count가 허용 유형 수보다 크면 모든 유형을 한 번 배정한 뒤 처음 유형부터 순환
- 예: `PERSONA_BIAS,RETRIEVAL_ERROR`, 오류 2개 → 첫 오류는 PERSONA_BIAS, 둘째 오류는 RETRIEVAL_ERROR
- error_sentence는 이후 학생용 답변에 그대로 들어갈 짧고 완결된 문장
- error_sentence 하나에는 틀린 주장 하나만 포함 (서로 다른 오류를 한 문장에 합치지 않음)
- error_sentence는 15~50자 정도의 단순한 한국어 문장으로 작성
- hallucination_types가 여러 개면 각 유형을 서로 다른 planned_error에 배정
- correct_sentence와 hallucination_reason은 참고 문서에 근거
- evidence_sentence는 참고 문서에서 줄바꿈·어미·띄어쓰기를 바꾸지 않고 연속된 문장을 그대로 복사
- RETRIEVAL_ERROR는 retrieved_context와 retrieval_source를 반드시 포함
- 동일 PDF 후보를 사용하면 retrieval_source는 SAME_DOCUMENT
- SAME_DOCUMENT RETRIEVAL_ERROR는 retrieved_context 안에 있는 한 대상의 실제 속성·기능을 다른 대상에 잘못 연결해 생성
- SAME_DOCUMENT RETRIEVAL_ERROR의 잘못된 속성·기능은 retrieved_context에 실제로 등장해야 하며, 문서에 없는 해·별·바람·연 같은 소재를 새로 만들지 않음
- 예: "자격루는 시간을 알림, 측우기는 비의 양을 잼" → "자격루는 비의 양을 재는 기구다"
- 문서 안에서 바꿔 연결할 서로 다른 사실이 없으면 SAME_DOCUMENT를 억지로 사용하지 말고 SYNTHETIC fallback 사용
- 적절한 동일 PDF 후보가 없어 synthetic distractor를 만들면 retrieval_source는 SYNTHETIC
- INFORMATION_FABRICATION은 retrieved_context 없이 가능
- start_index, end_index는 출력하지 않음 (백엔드가 계산)
- JSON만 출력 (마크다운·설명 금지)

## 유형 배정 검산
- PERSONA_BIAS: error_sentence의 잘못된 주장이 persona에 명시된 잘못된 믿음과 직접 일치해야 함
- INFORMATION_FABRICATION: 잘못된 핵심 속성·사건이 document_text와 candidate_chunks 어디에도 없어야 함
- RETRIEVAL_ERROR: 잘못 붙인 핵심 속성·기능이 retrieved_context 안에는 실제로 있어야 함
- 유형 이름을 먼저 정한 뒤 문장을 만들고, 완성 후 위 조건으로 각 항목을 다시 검산

예시:
- 문서 사실: "자격루는 시간을 알린다. 측우기는 비의 양을 잰다."
- INFORMATION_FABRICATION: "장영실은 망원경도 발명했다." (망원경은 문서에 없음)
- RETRIEVAL_ERROR: "자격루는 비의 양을 재는 기구다." (측우기의 실제 기능을 자격루에 잘못 연결)
- "자격루는 비의 양을 재는 기구다"를 INFORMATION_FABRICATION으로 표시하면 안 됨
- "장영실은 망원경도 발명했다"를 RETRIEVAL_ERROR로 표시하면 안 됨

## 출력 형식
{{
  "response_template": "문서 기반 도입 문장. [[ERROR_1]] 문서 기반 연결 문장. [[ERROR_2]] 문서 기반 마무리 문장.",
  "planned_errors": [
    {{
      "error_sentence": "string",
      "error_type": "RETRIEVAL_ERROR",
      "correct_sentence": "string",
      "hallucination_reason": "string",
      "evidence_sentence": "string",
      "retrieved_context": "string",
      "retrieval_source": "SAME_DOCUMENT"
    }}
  ]
}}
```

## Output

- OpenAI (`LanguageModelComponent-Ek4nl`) → `error_plan` 와이어 → 생성 프롬프트 / Plan Formatter
