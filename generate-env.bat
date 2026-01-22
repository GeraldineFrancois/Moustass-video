@echo off
REM Script batch de génération du fichier .env (Windows CMD)
REM Pour PowerShell (recommandé), utilisez: .\generate-env.ps1

echo.
echo ============================================================
echo  Moustass Video - Generateur de Configuration
echo ============================================================
echo.

if exist .env (
    echo [ATTENTION] Le fichier .env existe deja.
    set /p REPLY="Voulez-vous le remplacer ? (y/N): "
    if /i not "%REPLY%"=="y" (
        echo [ANNULE] Conservez votre fichier .env existant.
        pause
        exit /b 0
    )
    copy .env .env.backup >nul
    echo [OK] Backup cree: .env.backup
)

echo.
echo [INFO] Generation des secrets...
echo.
echo [ATTENTION] Ce script batch genere des secrets basiques.
echo             Pour une securite optimale, utilisez PowerShell:
echo             .\generate-env.ps1
echo.

REM Générer des "secrets" simples (moins sécurisés que PowerShell)
set JWT_SECRET=change-me-in-production-%RANDOM%%RANDOM%%RANDOM%
set MYSQL_ROOT_PASSWORD=root-%RANDOM%%RANDOM%
set VIDEO_DB_PASSWORD=video-%RANDOM%%RANDOM%
set AUTH_DB_PASSWORD=auth-%RANDOM%%RANDOM%
set SECURITY_DB_PASSWORD=security-%RANDOM%%RANDOM%

(
echo # ==========================================
echo # MOUSTASS VIDEO - CONFIGURATION
echo # ==========================================
echo # Genere automatiquement
echo # NE COMMITEZ JAMAIS CE FICHIER DANS GIT
echo # ==========================================
echo.
echo # JWT SECRET
echo JWT_SECRET=%JWT_SECRET%
echo.
echo # MYSQL ROOT
echo MYSQL_ROOT_PASSWORD=%MYSQL_ROOT_PASSWORD%
echo.
echo # BASE DE DONNEES VIDEOS
echo MYSQL_DATABASE=videos_db
echo VIDEO_DB_USER=video_user
echo VIDEO_DB_PASSWORD=%VIDEO_DB_PASSWORD%
echo VIDEO_DB_HOST=mysql
echo VIDEO_DB_PORT=3306
echo VIDEO_DB_NAME=videos_db
echo VIDEO_DATABASE_URL=mysql+pymysql://video_user:%VIDEO_DB_PASSWORD%@mysql:3306/videos_db
echo.
echo # BASE DE DONNEES AUTHENTIFICATION
echo AUTH_DB_USER=auth_user
echo AUTH_DB_PASSWORD=%AUTH_DB_PASSWORD%
echo AUTH_DB_NAME=auth_db
echo.
echo # BASE DE DONNEES SECURITE
echo SECURITY_DB_USER=security_user
echo SECURITY_DB_PASSWORD=%SECURITY_DB_PASSWORD%
echo.
echo # CONFIGURATION OPTIONNELLE
echo RSA_KEY_SIZE=3072
echo VIDEO_EXPIRATION_DAYS=60
echo CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8002
echo.
echo # TOKENS SECURITE (optionnel^)
echo SNYK_TOKEN=
echo SONAR_TOKEN=
echo SONAR_HOST_URL=http://localhost:9000
) > .env

echo.
echo [OK] Fichier .env cree avec succes!
echo.
echo [NEXT] Prochaine etape: start-services.bat
echo        ou (PowerShell): .\start-services.ps1
echo.
pause
