# Q1 demo - managing the edge device with Docker
# Run from the project folder:   powershell -ExecutionPolicy Bypass -File scripts\docker_demo.ps1
$ErrorActionPreference = "Continue"
function Step($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan; Read-Host "press Enter" | Out-Null }
function Check() {
    try { Invoke-WebRequest http://localhost:1880/ui -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host "dashboard: AVAILABLE" -ForegroundColor Green }
    catch { Write-Host "dashboard: UNAVAILABLE" -ForegroundColor Red }
}

Step "1. Running containers and their health"
docker compose ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"

Step "2. Gateway logs (last 15 lines - CRITICAL alerts are printed here)"
docker logs --tail 15 library-edge-gateway

Step "3. Failure test: STOP the gateway"
docker compose stop nodered
docker compose ps nodered
Check

Step "4. RESTART the gateway (recover from failure)"
docker compose start nodered
Start-Sleep 15
docker inspect --format "health = {{.State.Health.Status}}" library-edge-gateway
Check

Step "5. UPDATE the gateway from v1 to v2 (new image, alerts now include an action)"
$env:GATEWAY_VERSION = "v2"
docker compose up -d --build nodered
Start-Sleep 15
docker compose ps nodered --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"
Check

Step "6. Roll back to v1 (optional)"
$env:GATEWAY_VERSION = "v1"
docker compose up -d nodered
docker compose ps nodered --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"
