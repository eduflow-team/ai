# flows/



Langflow UI에서 Export한 flow JSON 저장소.



## Stage 2 — `stage2-hallucination-gen.json`



**시나리오2** UI 튜닝 완료본 (Langflow Export → `stage2-hallucination-gen.json`).



```

[A] hallucination_gen_prompt (5 inputs)

         ↓

[B] Ollama EXAONE → Plain Text Sanitizer → flawed_ai_response

         ↓ (wire)

[C] error_extraction_prompt → OpenAI → generated_errors (JSON)

```



| 구역 | 노드 | 모델 |

|------|------|------|

| A+B | `Prompt-s2gen` → `LanguageModelComponent-s2oll` → `CustomComponent-s2san` | Ollama `exaone3.5:7.8b` |

| C | `Prompt-s2ext` → `LanguageModelComponent-s2oai` | OpenAI `gpt-4o-mini` |



**Functional nodes: 7** (+ Note 3개)



### Import 방법



1. Langflow UI (`http://localhost:7860`)

2. `flows/stage2-hallucination-gen.json` Upload / 드래그



### Import 후 필수 설정



1. **Ollama EXAONE (생성)** (`LanguageModelComponent-s2oll`)
   - Provider: **Ollama**
   - **Ollama API URL**: `http://host.docker.internal:11434` (`localhost` 사용 시 모델 안 뜸)
   - URL 입력 후 **새로고침(↻)** → `exaone3.5:7.8b` 선택
2. **OpenAI (오류 추출)** → OpenAI, `gpt-4o-mini`, Settings에 API Key
3. 저장 (Ctrl+S)

점검: `.\scripts\check-ollama-langflow.ps1`



### Playground 테스트



`prompts/stage2/hallucination-gen.md` 장영실 baseline.  

출력 2개 확인: `flawed_ai_response`, `generated_errors`.



### Export (PR 전)



1. 시크릿 없음 확인

2. Export → 이 폴더 덮어쓰기

3. Playground 스크린샷 + `scripts/stage2-test.ps1` 로그



### 프롬프트 수정



Langflow UI에서 수정 후 **Export → 이 파일 덮어쓰기**.  
문서 동기화: `prompts/stage2/hallucination-gen.md`, `error-extraction.md`



연동: [`docs/stage2-langflow-contract.md`](../docs/stage2-langflow-contract.md)


