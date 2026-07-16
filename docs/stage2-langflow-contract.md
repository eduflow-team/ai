# Stage 2 Langflow ↔ Backend 연동 계약



Notion **시나리오2** · **개발 단계** 기준. 2단계 파이프라인: Ollama 생성 + OpenAI 구조화.



## Langflow가 담당하는 범위



| Notion 단계 | 내용 |

|-------------|------|

| 5 | 문서 + 페르소나 기반 AI 첫 답변 생성 |

| 6 | 의도적 오류 포함 |

| 7 (일부) | `generated_errors[]` 메타데이터 (채점·DB용) |



학생 하이라이트·채점(8~21)은 **백엔드** 담당.



---



## Flow 구조 (7 functional nodes)



```

hallucination_gen_prompt → Ollama EXAONE → Plain Text Sanitizer → flawed_ai_response

                                              ↓ (wire)

                    error_extraction_prompt → OpenAI → generated_errors

```



| 노드 ID | Display Name | 역할 |

|---------|--------------|------|

| `Prompt-s2gen` | hallucination_gen_prompt | 1차 프롬프트 + 교사 입력 |

| `LanguageModelComponent-s2oll` | Ollama EXAONE (생성) | 의도적 환각 답변 |

| `CustomComponent-s2san` | Plain Text Sanitizer | 마크다운 제거 |

| `ChatOutput-s2flaw` | flawed_ai_response | 학생용 AI 답변 |

| `Prompt-s2ext` | error_extraction_prompt | 2차 오류 추출 프롬프트 |

| `LanguageModelComponent-s2oai` | OpenAI (오류 추출) | JSON 구조화 |

| `ChatOutput-s2err` | generated_errors | 오류 메타 JSON |



---



## Import 후 필수 설정



### Ollama (`LanguageModelComponent-s2oll`)

- Provider: **Ollama**

- Model: `exaone3.5:7.8b`

- Ollama API URL: `http://host.docker.internal:11434`

- Temperature: `0.85`



### OpenAI (`LanguageModelComponent-s2oai`)

- Provider: **OpenAI**

- Model: `gpt-4o-mini`

- Langflow **Settings → OpenAI API Key** 설정

- Temperature: `0.2`



---



## 입력 (tweaks)



| 노드 | 키 | 타입 | 출처 |

|------|-----|------|------|

| `Prompt-s2gen` | `document_text` | string | `documents.raw_text` |

| `Prompt-s2gen` | `question` | string | 교사 입력 |

| `Prompt-s2gen` | `persona` | string | 교사 입력 |

| `Prompt-s2gen` | `hallucination_types` | string | 쉼표 구분 enum |

| `Prompt-s2gen` | `expected_error_count` | string | `"2"` 등 |

| `Prompt-s2ext` | `document_text` | string | 동일 (근거 추출용) |

| `Prompt-s2ext` | `hallucination_types` | string | 동일 |

| `Prompt-s2ext` | `expected_error_count` | string | 동일 |



> `flawed_ai_response`는 **와이어**로 자동 주입. tweaks 불필요.



### 예시 payload



```json

{

  "input_value": "",

  "tweaks": {

    "Prompt-s2gen": {

      "document_text": "장영실은 세종 대에 자격루와 측우기를 발명한...",

      "question": "장영실의 발명품에 대해 설명해줘.",

      "persona": "장영실이 연을 만들었다고 믿고, 자격루를 서양 기술이라고 주장하는 선생님",

      "hallucination_types": "RETRIEVAL_ERROR, PERSONA_BIAS",

      "expected_error_count": "2"

    },

    "Prompt-s2ext": {

      "document_text": "장영실은 세종 대에 자격루와 측우기를 발명한...",

      "hallucination_types": "RETRIEVAL_ERROR, PERSONA_BIAS",

      "expected_error_count": "2"

    }

  }

}

```



---



## 출력



### Must



| 키 | 출처 노드 | 설명 |

|----|-----------|------|

| `flawed_ai_response` | `ChatOutput-s2flaw` | 학생에게 보여줄 AI 답변 |

| `generated_errors` | `ChatOutput-s2err` | JSON 문자열 또는 파싱된 객체 |



```json

{

  "flawed_ai_response": "조선시대 최고의 과학자 장영실은...",

  "generated_errors": [

    {

      "error_sentence": "장영실은 연을 발명했습니다.",

      "error_type": "PERSONA_BIAS",

      "start_index": 12,

      "end_index": 28,

      "correct_sentence": "장영실의 대표 발명은 자격루와 측우기입니다.",

      "hallucination_reason": "페르소나 편향으로 참고 문서에 없는 연 발명을 사실처럼 서술",

      "evidence_sentence": "자격루는 물의 흐름을 이용해 시간을 알리는 자동 물시계이고..."

    }

  ]

}

```



Langflow run 응답에서는 **출력 노드별로** 텍스트가 분리되어 옵니다. 백엔드 `LangflowClient`가 두 Chat Output을 파싱해 위 형태로 합칩니다.



---



## 백엔드 DB 매핑



| Langflow / API | DB 테이블.컬럼 |

|----------------|----------------|

| `flawed_ai_response` | `stage2_assignment_details.hallucinated_ai_answer` |

| `generated_errors[]` | `stage2_error_answers` 행들 |

| `document_text` | `documents.raw_text` |

| `expected_error_count` | `stage2_assignment_details.expected_error_count` |

| `persona` | `stage2_assignment_details.persona` |

| `hallucination_types` | `stage2_assignment_details.hallucination_types` (JSON) |



---



## 백엔드 `.env`



```env

LANGFLOW_URL=http://localhost:7860

LANGFLOW_API_KEY=

LANGFLOW_STAGE2_FLOW_ID=

```



---



## API 응답 (교사 과제 생성)



`POST /api/v1/teacher/assignments/step2` → 201



```json

{

  "assignment_id": 201,

  "question": "장영실의 발명품에 대해 설명해줘.",

  "flawed_ai_response": "...",

  "expected_error_count": 2,

  "generated_errors": []

}

```



---



## 프롬프트 소스



| 파일 | 노드 |

|------|------|

| `prompts/stage2/hallucination-gen.md` | `Prompt-s2gen` |

| `prompts/stage2/error-extraction.md` | `Prompt-s2ext` |



동기화: Langflow UI Export → `flows/stage2-hallucination-gen.json` 덮어쓰기


