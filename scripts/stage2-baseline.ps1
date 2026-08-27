# Stage 2 Langflow baseline 측정 (Flow JSON 수정 없음)
# Usage:
#   $env:LANGFLOW_API_KEY = "<UI Settings → API Keys>"
#   $env:FLOW_ID = "<Import 후 Flow ID>"
#   .\scripts\stage2-baseline.ps1
# Optional:
#   $env:RUNS_PER_CASE = "3"
#   $env:OUTPUT_DIR = "baseline-results/stage2-$(Get-Date -Format yyyyMMdd-HHmmss)"

$ErrorActionPreference = "Stop"

$LangflowUrl = if ($env:LANGFLOW_URL) { $env:LANGFLOW_URL } else { "http://localhost:7860" }
$ApiKey = $env:LANGFLOW_API_KEY
$FlowId = $env:FLOW_ID
$RunsPerCase = if ($env:RUNS_PER_CASE) { [int]$env:RUNS_PER_CASE } else { 3 }
$OutputDir = if ($env:OUTPUT_DIR) { $env:OUTPUT_DIR } else { "baseline-results/stage2-$(Get-Date -Format yyyyMMdd-HHmmss)" }

if (-not $FlowId) {
    Write-Host "FLOW_ID 환경변수를 설정하세요." -ForegroundColor Yellow
    exit 1
}
if (-not $ApiKey) {
    Write-Host "LANGFLOW_API_KEY 환경변수를 설정하세요." -ForegroundColor Yellow
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$JangDoc = @"
장영실은 세종 대에 자격루와 측우기를 발명한 조선시대 최고의 과학자입니다.
자격루는 물의 흐름을 이용해 시간을 알리는 자동 물시계이고, 측우기는 비의 양을 재는 기구입니다.
"@.Trim()

$PersonaBaseline = "장영실이 연을 만들었다고 믿고, 자격루를 서양 기술이라고 주장하는 선생님"

$TestCases = @(
    @{
        id = "jangyeongsil-baseline"
        name = "장영실 baseline (stage2-test.ps1 동일)"
        document_text = $JangDoc
        question = "장영실의 발명품에 대해 설명해줘."
        persona = $PersonaBaseline
        hallucination_types = "RETRIEVAL_ERROR, PERSONA_BIAS"
        expected_error_count = 2
    },
    @{
        id = "jangyeongsil-fabrication-retrieval"
        name = "장영실 — INFORMATION_FABRICATION + RETRIEVAL_ERROR"
        document_text = $JangDoc
        question = "장영실의 발명품에 대해 설명해줘."
        persona = $PersonaBaseline
        hallucination_types = "INFORMATION_FABRICATION, RETRIEVAL_ERROR"
        expected_error_count = 2
    },
    @{
        id = "jangyeongsil-single-bias"
        name = "장영실 — PERSONA_BIAS 단일 오류"
        document_text = $JangDoc
        question = "장영실은 어떤 발명을 했나요?"
        persona = "장영실이 연을 만들었다고 확신하는 역사 선생님"
        hallucination_types = "PERSONA_BIAS"
        expected_error_count = 1
    },
    @{
        id = "jangyeongsil-triple-types"
        name = "장영실 — 3유형 3오류"
        document_text = $JangDoc
        question = "장영실의 과학적 업적을 알려줘."
        persona = $PersonaBaseline
        hallucination_types = "PERSONA_BIAS, INFORMATION_FABRICATION, RETRIEVAL_ERROR"
        expected_error_count = 3
    },
    @{
        id = "jangyeongsil-alt-question"
        name = "장영실 — 다른 질문, 동일 설정"
        document_text = $JangDoc
        question = "자격루와 측우기는 각각 무엇인가요?"
        persona = $PersonaBaseline
        hallucination_types = "RETRIEVAL_ERROR, PERSONA_BIAS"
        expected_error_count = 2
    }
)

function Build-Payload {
    param($Case)
    $countStr = [string]$Case.expected_error_count
    $typesStr = $Case.hallucination_types
    $shared = @{
        document_text = $Case.document_text
        hallucination_types = $typesStr
        expected_error_count = $countStr
    }
    return @{
        input_value = ""
        session_id = "stage2-baseline-$($Case.id)"
        tweaks = @{
            "Prompt-fwk9l" = @{
                document_text = $Case.document_text
                question = $Case.question
                persona = $Case.persona
                hallucination_types = $typesStr
                expected_error_count = $countStr
            }
            "Prompt-We0Ob" = $shared
        }
    }
}

function Extract-Outputs {
    param($ResponseObj)
    $texts = @()
    foreach ($runOutput in ($ResponseObj.outputs | ForEach-Object { $_ })) {
        foreach ($inner in ($runOutput.outputs | ForEach-Object { $_ })) {
            $results = $inner.results
            if (-not $results) { continue }
            $message = $results.message
            if (-not $message) { $message = $results.text }
            if ($message -is [hashtable] -or $message -is [pscustomobject]) {
                if ($message.text) { $texts += [string]$message.text }
            } elseif ($message) {
                $texts += [string]$message
            }
        }
    }
    return $texts
}

function Parse-GeneratedErrors {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null, "empty generated_errors text" }
    $clean = $Raw.Trim()
    $fence = '```'
    if ($clean.StartsWith($fence)) {
        $parts = $clean -split [Environment]::NewLine, 2
        $clean = if ($parts.Count -gt 1) { $parts[1] } else { $clean }
        $clean = ($clean -split $fence)[0].Trim()
    }
    try {
        $parsed = $clean | ConvertFrom-Json
    } catch {
        return $null, "JSON parse failed: $($_.Exception.Message)"
    }
    if ($parsed.generated_errors) { return @($parsed.generated_errors), $null }
    if ($parsed -is [array]) { return @($parsed), $null }
    return $null, "generated_errors key missing"
}

function Test-IndexAccuracy {
    param([string]$Flawed, $ErrorObj)
    $sentence = [string]$ErrorObj.error_sentence
    $start = [int]$ErrorObj.start_index
    $end = [int]$ErrorObj.end_index
    if ($start -lt 0 -or $end -le $start) { return $false, "invalid range $start..$end" }
    if ($end -gt $Flawed.Length) { return $false, "end_index $end > text length $($Flawed.Length)" }
    $slice = $Flawed.Substring($start, $end - $start)
    if ($slice -eq $sentence) { return $true, $null }
    return $false, "slice mismatch: '$slice' != '$sentence'"
}

function Evaluate-Run {
    param($Case, $RunIndex, $Flawed, $Errors, $ParseError, $ElapsedMs, $HttpOk)
    $checks = [ordered]@{}
    $checks.call_success = $HttpOk
    $checks.json_parse_success = ($null -eq $ParseError)
    $checks.error_count_match = $false
    $checks.error_types_valid = $true
    $checks.error_sentence_in_flawed = $true
    $checks.evidence_in_document = $true
    $checks.index_accuracy = $true
    $failReasons = @()

    if ($ParseError) { $failReasons += $ParseError }
    if (-not $HttpOk) { $failReasons += "HTTP call failed" }

    $allowedTypes = @($Case.hallucination_types -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $expectedCount = [int]$Case.expected_error_count

    if ($Errors) {
        $checks.error_count_match = ($Errors.Count -eq $expectedCount)
        if (-not $checks.error_count_match) {
            $failReasons += "expected $expectedCount errors, got $($Errors.Count)"
        }
        foreach ($err in $Errors) {
            $etype = [string]$err.error_type
            if ($allowedTypes -notcontains $etype) {
                $checks.error_types_valid = $false
                $failReasons += "error_type $etype not in allowed [$($allowedTypes -join ', ')]"
            }
            $es = [string]$err.error_sentence
            if ($Flawed -and $es -and ($Flawed.IndexOf($es) -lt 0)) {
                $checks.error_sentence_in_flawed = $false
                $failReasons += "error_sentence not found in flawed_ai_response"
            }
            $ev = [string]$err.evidence_sentence
            if ($ev -and ($Case.document_text.IndexOf($ev) -lt 0)) {
                $checks.evidence_in_document = $false
                $failReasons += "evidence_sentence not found in document_text"
            }
            if ($Flawed) {
                $idxOk, $idxReason = Test-IndexAccuracy -Flawed $Flawed -ErrorObj $err
                if (-not $idxOk) {
                    $checks.index_accuracy = $false
                    $failReasons += $idxReason
                }
            }
        }
    } elseif (-not $ParseError) {
        $failReasons += "no errors array"
    }

    $autoPass = $checks.call_success -and $checks.json_parse_success -and $checks.error_count_match `
        -and $checks.error_types_valid -and $checks.error_sentence_in_flawed `
        -and $checks.evidence_in_document -and $checks.index_accuracy

    return [pscustomobject]@{
        case_id = $Case.id
        case_name = $Case.name
        run = $RunIndex
        elapsed_ms = $ElapsedMs
        auto_pass = $autoPass
        checks = $checks
        fail_reasons = $failReasons
        flawed_ai_response = $Flawed
        generated_errors = $Errors
        manual_review = @{
            unintended_extra_hallucination = "REVIEW"
            naturalness = "REVIEW"
            assignment_appropriateness = "REVIEW"
        }
    }
}

$headers = @{
    "Content-Type" = "application/json; charset=utf-8"
    "x-api-key" = $ApiKey
}

$allResults = @()
Write-Host "Stage 2 baseline: $($TestCases.Count) cases x $RunsPerCase runs" -ForegroundColor Cyan
Write-Host "Output: $OutputDir"
Write-Host "Flow ID: $FlowId (Langflow: $LangflowUrl)"
Write-Host ""

foreach ($case in $TestCases) {
    Write-Host "Case: $($case.id)" -ForegroundColor Yellow
    for ($r = 1; $r -le $RunsPerCase; $r++) {
        $payload = Build-Payload -Case $case
        $jsonBody = $payload | ConvertTo-Json -Depth 8
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $httpOk = $false
        $flawed = $null
        $errors = $null
        $parseError = $null
        $rawResponse = $null

        try {
            $webResp = Invoke-WebRequest `
                -Uri "$LangflowUrl/api/v1/run/$FlowId" `
                -Method POST `
                -Headers $headers `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($jsonBody)) `
                -TimeoutSec 180 `
                -UseBasicParsing
            $httpOk = $true
            $rawResponse = $webResp.Content | ConvertFrom-Json
            $texts = Extract-Outputs -ResponseObj $rawResponse
            if ($texts.Count -ge 1) { $flawed = $texts[0] }
            if ($texts.Count -ge 2) {
                $errors, $parseError = Parse-GeneratedErrors -Raw $texts[1]
            } else {
                $parseError = "missing generated_errors output (got $($texts.Count) text outputs)"
            }
        } catch {
            $parseError = $_.Exception.Message
            if ($_.ErrorDetails.Message) { $parseError += " | $($_.ErrorDetails.Message)" }
        } finally {
            $sw.Stop()
        }

        $result = Evaluate-Run -Case $case -RunIndex $r -Flawed $flawed -Errors $errors `
            -ParseError $parseError -ElapsedMs $sw.ElapsedMilliseconds -HttpOk $httpOk
        $allResults += $result

        $status = if ($result.auto_pass) { "PASS" } else { "FAIL" }
        $color = if ($result.auto_pass) { "Green" } else { "Red" }
        Write-Host "  run $r : $status ($($result.elapsed_ms) ms)" -ForegroundColor $color
        if (-not $result.auto_pass -and $result.fail_reasons.Count -gt 0) {
            Write-Host "    -> $($result.fail_reasons -join '; ')" -ForegroundColor DarkYellow
        }

        $artifact = @{
            meta = @{
                case_id = $case.id
                run = $r
                elapsed_ms = $result.elapsed_ms
                auto_pass = $result.auto_pass
            }
            input = $case
            output = @{
                flawed_ai_response = $flawed
                generated_errors = $errors
            }
            checks = $result.checks
            fail_reasons = $result.fail_reasons
        }
        $artifactPath = Join-Path $OutputDir "$($case.id)-run$r.json"
        $artifact | ConvertTo-Json -Depth 10 | Out-File -FilePath $artifactPath -Encoding utf8
    }
}

# Summary
$total = $allResults.Count
$passed = @($allResults | Where-Object { $_.auto_pass }).Count
$byCase = $TestCases | ForEach-Object {
    $cid = $_.id
    $caseRuns = @($allResults | Where-Object { $_.case_id -eq $cid })
    $casePass = @($caseRuns | Where-Object { $_.auto_pass }).Count
    [pscustomobject]@{
        case_id = $cid
        name = $_.name
        pass = $casePass
        total = $caseRuns.Count
        pass_rate = if ($caseRuns.Count) { [math]::Round(100 * $casePass / $caseRuns.Count, 1) } else { 0 }
        avg_ms = [math]::Round(($caseRuns | Measure-Object -Property elapsed_ms -Average).Average, 0)
    }
}

$failExamples = @($allResults | Where-Object { -not $_.auto_pass } | Select-Object -First 5)
$reviewSamples = @($allResults | Sort-Object { Get-Random } | Select-Object -First 5)

$report = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    flow_id = $FlowId
    langflow_url = $LangflowUrl
    runs_per_case = $RunsPerCase
    total_runs = $total
    auto_pass_count = $passed
    auto_pass_rate = if ($total) { [math]::Round(100 * $passed / $total, 1) } else { 0 }
    avg_elapsed_ms = [math]::Round(($allResults | Measure-Object -Property elapsed_ms -Average).Average, 0)
    by_case = $byCase
    representative_failures = $failExamples | ForEach-Object {
        [ordered]@{
            case_id = $_.case_id
            run = $_.run
            fail_reasons = $_.fail_reasons
            flawed_preview = if ($_.flawed_ai_response) { $_.flawed_ai_response.Substring(0, [Math]::Min(200, $_.flawed_ai_response.Length)) } else { $null }
        }
    }
    manual_review_samples = $reviewSamples | ForEach-Object {
        [ordered]@{
            case_id = $_.case_id
            run = $_.run
            auto_pass = $_.auto_pass
            elapsed_ms = $_.elapsed_ms
            flawed_ai_response = $_.flawed_ai_response
            generated_errors = $_.generated_errors
            manual_review = $_.manual_review
        }
    }
}

$reportPath = Join-Path $OutputDir "baseline-report.json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding utf8

Write-Host ""
Write-Host "=== Baseline Summary ===" -ForegroundColor Cyan
Write-Host "Auto pass: $passed / $total ($($report.auto_pass_rate)%)"
Write-Host "Avg response: $($report.avg_elapsed_ms) ms"
Write-Host "Report: $reportPath"
$byCase | Format-Table -AutoSize

exit $(if ($passed -lt $total) { 1 } else { 0 })
