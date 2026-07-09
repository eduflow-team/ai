# Ollama (호스트 PC) ↔ Langflow (Docker) 연결 점검
# Usage: .\scripts\check-ollama-langflow.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== 1. 호스트 Ollama 모델 ===" -ForegroundColor Cyan
try {
    $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 15
    $names = $tags.models | ForEach-Object { $_.name }
    $names | ForEach-Object { Write-Host "  - $_" }
    if ($names -contains "exaone3.5:7.8b") {
        Write-Host "  OK: exaone3.5:7.8b" -ForegroundColor Green
    } else {
        Write-Host "  WARN: exaone3.5:7.8b 없음 → ollama pull exaone3.5:7.8b" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  FAIL: 호스트 Ollama 미응답 (트레이 앱 실행 또는 ollama serve)" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== 2. Docker Langflow → 호스트 Ollama ===" -ForegroundColor Cyan
$container = "eduflow_langflow"
$running = docker ps --filter "name=$container" --format "{{.Names}}" 2>$null
if (-not $running) {
    Write-Host "  FAIL: $container 컨테이너 없음 → docker compose up -d" -ForegroundColor Red
    exit 1
}

$dockerOut = docker exec $container curl -s --connect-timeout 10 "http://host.docker.internal:11434/api/tags" 2>&1
if ($dockerOut -match "exaone3.5:7.8b") {
    Write-Host "  OK: 컨테이너에서 exaone3.5:7.8b 조회됨" -ForegroundColor Green
} elseif ($dockerOut -match "models") {
    Write-Host "  OK: Ollama 연결됨 (exaone 태그명 확인 필요)" -ForegroundColor Yellow
    Write-Host $dockerOut.Substring(0, [Math]::Min(200, $dockerOut.Length))
} else {
    Write-Host "  FAIL: host.docker.internal:11434 연결 실패" -ForegroundColor Red
    Write-Host $dockerOut
    Write-Host "`n  시도: 사용자 환경변수 OLLAMA_HOST=0.0.0.0:11434 설정 후 Ollama 앱 재시작" -ForegroundColor Yellow
    Write-Host '  [System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")'
    exit 1
}

Write-Host "`n=== 3. Langflow UI 설정 (Import 후 1회) ===" -ForegroundColor Cyan
Write-Host @"
  1. 노드 'Ollama EXAONE (생성)' 클릭
  2. Language Model → Provider: Ollama 선택
  3. Ollama API URL: http://host.docker.internal:11434
     (localhost:11434 아님 — Docker 안에서는 호스트 PC를 가리키지 않음)
  4. URL 옆 새로고침(↻) 클릭 → 모델 목록 로드
  5. Model: exaone3.5:7.8b 선택
  6. Ctrl+S 저장
"@

Write-Host "`n완료." -ForegroundColor Green
