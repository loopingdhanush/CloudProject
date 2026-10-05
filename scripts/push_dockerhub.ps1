# Push the project images to Docker Hub.
# 1) set DOCKERHUB_USER in the .env file to your Docker Hub username
# 2) docker login
# 3) powershell -ExecutionPolicy Bypass -File scripts\push_dockerhub.ps1
$user = (Get-Content .env | Select-String '^DOCKERHUB_USER=').ToString().Split('=')[1].Trim()
Write-Host "Pushing images for Docker Hub user: $user"

$env:GATEWAY_VERSION = "v1"; docker compose build
docker compose push nodered nginx simulator
$env:GATEWAY_VERSION = "v2"; docker compose build nodered
docker compose push nodered
Remove-Item Env:GATEWAY_VERSION

Write-Host "`nDone:"
Write-Host "  $user/library-gateway:v1, $user/library-gateway:v2"
Write-Host "  $user/library-sensors:1.0, $user/library-ditto-nginx:1.0"
