# Stage 2 Langflow curl 테스트 (PowerShell)
# Usage:
#   $env:LANGFLOW_API_KEY = "<UI Settings → API Keys>"
#   $env:FLOW_ID = "<Import 후 Flow ID>"
#   .\scripts\stage2-test.ps1

$ErrorActionPreference = "Stop"

$LangflowUrl = if ($env:LANGFLOW_URL) { $env:LANGFLOW_URL } else { "http://localhost:7860" }
$ApiKey = $env:LANGFLOW_API_KEY
$FlowId = $env:FLOW_ID

if (-not $FlowId) {
    Write-Host "FLOW_ID 환경변수를 설정하세요. (Langflow UI → API 탭)" -ForegroundColor Yellow
    exit 1
}

$headers = @{ "Content-Type" = "application/json" }
if ($ApiKey) { $headers["x-api-key"] = $ApiKey }

$documentText = @"
장영실은 세종 대에 자격루와 측우기를 발명한 조선시대 최고의 과학자입니다.
자격루는 물의 흐름을 이용해 시간을 알리는 자동 물시계이고, 측우기는 비의 양을 재는 기구입니다.
"@.Trim()

$sharedTweaks = @{
    document_text        = $documentText
    question             = "장영실의 발명품에 대해 설명해줘."
    persona              = "장영실이 연을 만들었다고 믿고, 자격루를 서양 기술이라고 주장하는 선생님"
    hallucination_types  = "RETRIEVAL_ERROR, PERSONA_BIAS"
    expected_error_count = "2"
}

$candidateChunks = @{
    strategy                   = "SAME_DOCUMENT_THEN_SYNTHETIC"
    candidate_chunks           = @(
        @{
            chunk_id          = "chunk-0"
            source_index      = 0
            text              = $documentText
            relevance_score   = 0.8
            selection_bucket  = "TOP_RELEVANCE"
        }
    )
    synthetic_fallback_allowed = $true
} | ConvertTo-Json -Depth 6 -Compress

$body = @{
    input_value = ""
    session_id  = "stage2-test"
    tweaks      = @{
        "Prompt-fwk9l" = @{
            document_text        = $sharedTweaks.document_text
            question             = $sharedTweaks.question
            persona              = $sharedTweaks.persona
            hallucination_types  = $sharedTweaks.hallucination_types
            expected_error_count = $sharedTweaks.expected_error_count
        }
        "Prompt-We0Ob" = @{
            document_text        = $sharedTweaks.document_text
            question             = $sharedTweaks.question
            persona              = $sharedTweaks.persona
            hallucination_types  = $sharedTweaks.hallucination_types
            expected_error_count = $sharedTweaks.expected_error_count
            candidate_chunks     = $candidateChunks
            validation_feedback  = ""
        }
    }
} | ConvertTo-Json -Depth 6

Write-Host "POST $LangflowUrl/api/v1/run/$FlowId"
Write-Host "plan-first pipeline: OpenAI planner + Ollama generation + formatter"

try {
    $response = Invoke-RestMethod `
        -Uri "$LangflowUrl/api/v1/run/$FlowId" `
        -Method POST `
        -Headers $headers `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
        -TimeoutSec 180
    $response | ConvertTo-Json -Depth 12
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    exit 1
}
