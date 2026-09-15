@echo off
title A.U.S.T.I.N. - Inicializacao

echo.
echo ========================================
echo          A.U.S.T.I.N. ONLINE
echo ========================================
echo.

:: ========================================
:: REDIS - DOCKER
:: ========================================

echo [1/4] Verificando Redis...

docker start austin-redis >nul 2>&1

if %errorlevel% neq 0 (
    echo Container austin-redis nao encontrado.
    echo Tentando iniciar pelo Docker Compose...

    cd /d "%~dp0"

    docker compose up -d redis

    if %errorlevel% neq 0 (
        echo.
        echo ERRO: Nao foi possivel iniciar o Redis.
        echo Verifique se o Docker Desktop esta aberto.
        echo.
        pause
        exit /b 1
    )
)

echo Redis iniciado.

:: ========================================
:: SOM DE INICIALIZACAO
:: ========================================

if exist "%~dp0startup.mp3" (
    start "" "%~dp0startup.mp3"
)

:: ========================================
:: BACKEND - PYTHON / FASTAPI
:: ========================================

echo [2/4] Iniciando sistema Python...

start "A.U.S.T.I.N. - Backend" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%~dp0backend && python -m backend.main"

:: ========================================
:: FRONTEND - REACT / VITE
:: ========================================

echo [3/4] Iniciando interface...

start "A.U.S.T.I.N. - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: ========================================
:: AGUARDA O VITE
:: ========================================

echo [4/4] Aguardando interface...

timeout /t 5 /nobreak >nul

:: ========================================
:: ABRE O NAVEGADOR
:: ========================================

start "" "http://localhost:5173"

echo.
echo ========================================
echo       A.U.S.T.I.N. INICIADO
echo ========================================
echo.

exit