@echo off

title A.U.S.T.I.N. - Desligamento

echo.
echo ========================================
echo       A.U.S.T.I.N. OFFLINE
echo ========================================
echo.

:: ========================================
:: SOM DE ENCERRAMENTO
:: ========================================

if exist "%~dp0shutdown.mp3" (
    start "" "%~dp0shutdown.mp3"
)

:: ========================================
:: BACKEND - PYTHON / FASTAPI
:: ========================================

echo [1/3] Encerrando sistema Python...

for /f %%A in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and $_.CommandLine -like '*python -m backend.main*' }).ProcessId"') do (
    taskkill /PID %%A /T /F >nul 2>&1
)

echo Backend encerrado.

:: ========================================
:: FRONTEND - REACT / VITE
:: ========================================

echo [2/3] Encerrando interface...

for /f %%A in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and $_.CommandLine -like '*npm run dev*' }).ProcessId"') do (
    taskkill /PID %%A /T /F >nul 2>&1
)

echo Frontend encerrado.

:: ========================================
:: REDIS - DOCKER
:: ========================================

echo [3/3] Encerrando Redis...

docker stop austin-redis >nul 2>&1

if %errorlevel% neq 0 (
    echo Container austin-redis nao encontrado ou ja esta parado.
) else (
    echo Redis encerrado.
)

:: ========================================
:: FINAL
:: ========================================

echo.
echo ========================================
echo       A.U.S.T.I.N. DESLIGADO
echo ========================================
echo.

timeout /t 2 /nobreak >nul

exit