# Script PowerShell de génération automatique du fichier .env (Windows)
# Usage: .\generate-env.ps1

$ErrorActionPreference = "Stop"

Write-Host "🔐 Générateur de Configuration Sécurisée - Moustass Video" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si .env existe déjà
if (Test-Path ".env") {
    Write-Host "⚠️  Le fichier .env existe déjà." -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous le remplacer ? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-Host "❌ Annulé. Conservez votre fichier .env existant." -ForegroundColor Red
        exit 0
    }
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    Copy-Item ".env" ".env.backup.$timestamp"
    Write-Host "✅ Backup créé: .env.backup.$timestamp" -ForegroundColor Green
}

# Fonction pour générer un mot de passe aléatoire
function Generate-Password {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    $password = -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
    return $password
}

# Fonction pour générer un secret JWT (plus long)
function Generate-JwtSecret {
    return Generate-Password -Length 64
}

Write-Host "🔑 Génération des secrets aléatoires..." -ForegroundColor Cyan
Write-Host ""

# Générer les secrets
$JWT_SECRET = Generate-JwtSecret
$MYSQL_ROOT_PASSWORD = Generate-Password
$VIDEO_DB_PASSWORD = Generate-Password
$AUTH_DB_PASSWORD = Generate-Password
$SECURITY_DB_PASSWORD = Generate-Password

$currentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Créer le fichier .env
$envContent = @"
# ==========================================
# MOUSTASS VIDEO - CONFIGURATION
# ==========================================
# Généré automatiquement le $currentDate
# ⚠️  Ne commitez JAMAIS ce fichier dans git
# ==========================================

# ==========================================
# JWT SECRET
# ==========================================
JWT_SECRET=$JWT_SECRET

# ==========================================
# MYSQL ROOT
# ==========================================
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD

# ==========================================
# BASE DE DONNÉES VIDÉOS
# ==========================================
MYSQL_DATABASE=videos_db
VIDEO_DB_USER=video_user
VIDEO_DB_PASSWORD=$VIDEO_DB_PASSWORD
VIDEO_DB_HOST=mysql
VIDEO_DB_PORT=3306
VIDEO_DB_NAME=videos_db

# URL complète de connexion
VIDEO_DATABASE_URL=mysql+pymysql://video_user:$VIDEO_DB_PASSWORD@mysql:3306/videos_db

# ==========================================
# BASE DE DONNÉES AUTHENTIFICATION
# ==========================================
AUTH_DB_USER=auth_user
AUTH_DB_PASSWORD=$AUTH_DB_PASSWORD
AUTH_DB_NAME=auth_db

# ==========================================
# BASE DE DONNÉES SÉCURITÉ
# ==========================================
SECURITY_DB_USER=security_user
SECURITY_DB_PASSWORD=$SECURITY_DB_PASSWORD

# ==========================================
# CONFIGURATION OPTIONNELLE
# ==========================================
RSA_KEY_SIZE=3072
VIDEO_EXPIRATION_DAYS=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8002

# ==========================================
# TOKENS SÉCURITÉ (optionnel)
# ==========================================
SNYK_TOKEN=
SONAR_TOKEN=
SONAR_HOST_URL=http://localhost:9000
"@

# Écrire avec encodage UTF-8 sans BOM et fins de ligne LF
$envContent | Out-File -FilePath ".env" -Encoding utf8NoBOM -NoNewline
# Corriger les fins de ligne pour être compatible Linux/Docker
(Get-Content ".env" -Raw) -replace "`r`n", "`n" | Set-Content ".env" -NoNewline

Write-Host ""
Write-Host "✅ Fichier .env créé avec succès!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Résumé des secrets générés:" -ForegroundColor Cyan
Write-Host "   - JWT_SECRET:            $($JWT_SECRET.Substring(0,8))..." -ForegroundColor White
Write-Host "   - MYSQL_ROOT_PASSWORD:   $($MYSQL_ROOT_PASSWORD.Substring(0,8))..." -ForegroundColor White
Write-Host "   - VIDEO_DB_PASSWORD:     $($VIDEO_DB_PASSWORD.Substring(0,8))..." -ForegroundColor White
Write-Host "   - AUTH_DB_PASSWORD:      $($AUTH_DB_PASSWORD.Substring(0,8))..." -ForegroundColor White
Write-Host "   - SECURITY_DB_PASSWORD:  $($SECURITY_DB_PASSWORD.Substring(0,8))..." -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Ne partagez jamais ces secrets!" -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Prochaine étape: .\start-services.ps1" -ForegroundColor Cyan
Write-Host ""
