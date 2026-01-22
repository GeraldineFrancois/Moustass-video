# Script PowerShell pour lancer tous les services Moustass Video (Windows)
# Usage: .\start-services.ps1

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ Moustass Video - Lancement des Services (Windows)          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Vérifier que Docker est installé
try {
    $null = docker --version
} catch {
    Write-Host "❌ Docker n'est pas installé ou n'est pas dans le PATH." -ForegroundColor Red
    Write-Host "   Veuillez installer Docker Desktop pour Windows." -ForegroundColor Yellow
    exit 1
}

try {
    $null = docker compose version
} catch {
    Write-Host "❌ docker compose n'est pas disponible." -ForegroundColor Red
    exit 1
}

# Charger les variables d'environnement si .env existe
if (Test-Path ".env") {
    Write-Host "📝 Chargement de .env..." -ForegroundColor Green
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "⚠️  Fichier .env non trouvé. Utilisation des valeurs par défaut." -ForegroundColor Yellow
    Write-Host "   Exécutez d'abord: .\generate-env.ps1" -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("JWT_SECRET", "your-jwt-secret-change-in-production", "Process")
}

Write-Host ""
Write-Host "📦 Construire les images Docker..." -ForegroundColor Cyan
docker compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du build Docker" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Démarrer tous les services..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du démarrage des services" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Attendre que les services démarrent..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Vérifier l'état des services
Write-Host ""
Write-Host "🔍 Vérification de l'état des services..." -ForegroundColor Cyan
Write-Host ""

# Tester le service d'authentification
Write-Host "📌 Service d'authentification (port 8001):" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ OK - http://localhost:8001" -ForegroundColor Green
} catch {
    Write-Host "   ❌ ERREUR - Service non accessible" -ForegroundColor Red
}

# Tester le service vidéo
Write-Host "📌 Service vidéo (port 8002):" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/api/videos/health/status" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ OK - http://localhost:8002" -ForegroundColor Green
} catch {
    Write-Host "   ❌ ERREUR - Service non accessible" -ForegroundColor Red
}

# Tester le service sécurité
Write-Host "📌 Service sécurité (port 8003):" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ OK - http://localhost:8003" -ForegroundColor Green
} catch {
    Write-Host "   ❌ ERREUR - Service non accessible" -ForegroundColor Red
}

# Tester MySQL
Write-Host "📌 Base de données MySQL (port 3307):" -ForegroundColor White
$mysqlCheck = docker exec moustass-mysql mysqladmin ping -h localhost 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ OK" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Base de données en cours d'initialisation..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                   Services Démarrés                        ║" -ForegroundColor Green
Write-Host "╠════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║  🔐 Auth Service:     http://localhost:8001               ║" -ForegroundColor Green
Write-Host "║  🎥 Video Service:    http://localhost:8002               ║" -ForegroundColor Green
Write-Host "║  🔒 Security Service: http://localhost:8003               ║" -ForegroundColor Green
Write-Host "║  💾 MySQL:            localhost:3307                      ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║  📊 Logs:  docker compose logs -f                         ║" -ForegroundColor Green
Write-Host "║  🛑 Stop:  docker compose down                            ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
