@echo off
REM Script batch pour lancer les services Moustass Video (Windows CMD)
REM Pour PowerShell, utilisez: .\start-services.ps1

echo.
echo ============================================================
echo  Moustass Video - Lancement des Services (Windows)
echo ============================================================
echo.

REM Vérifier Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installe ou n'est pas dans le PATH.
    echo          Veuillez installer Docker Desktop pour Windows.
    pause
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] docker compose n'est pas disponible.
    pause
    exit /b 1
)

REM Charger .env si existe
if exist .env (
    echo [OK] Fichier .env trouve.
) else (
    echo [ATTENTION] Fichier .env non trouve.
    echo             Executez d'abord: .\generate-env.ps1
    echo             Utilisation des valeurs par defaut...
)

echo.
echo [BUILD] Construction des images Docker...
docker compose build --no-cache
if errorlevel 1 (
    echo [ERREUR] Echec du build Docker
    pause
    exit /b 1
)

echo.
echo [START] Demarrage des services...
docker compose up -d
if errorlevel 1 (
    echo [ERREUR] Echec du demarrage
    pause
    exit /b 1
)

echo.
echo [WAIT] Attente du demarrage des services (10 secondes)...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================
echo                   Services Demarres
echo ============================================================
echo.
echo   Auth Service:     http://localhost:8001
echo   Video Service:    http://localhost:8002
echo   Security Service: http://localhost:8003
echo   MySQL:            localhost:3307
echo.
echo   Logs:  docker compose logs -f
echo   Stop:  docker compose down
echo.
echo ============================================================
echo.
pause
