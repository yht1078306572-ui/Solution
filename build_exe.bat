@echo off
rem CMSolution build script: rebuild exe + package zip after source changes
rem usage: double-click after editing source; result is CMSolution_<timestamp>.zip
cd /d "%~dp0"
set PY=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe

echo [1/4] PyInstaller building...
"%PY%" -m PyInstaller --noconfirm --clean --onedir --windowed --name CMSolution --icon "assets\cm_icon.ico" --add-data "templates;templates" --add-data "assets;assets" webview_app.py
if not exist "dist\CMSolution\CMSolution.exe" (
    echo [FAIL] exe build failed
    pause
    exit /b 1
)

echo [2/4] Copying README into dist...
copy /y "README.txt" "dist\CMSolution\README.txt" >nul

echo [3/4] Cleaning output dir...
if exist "dist\CMSolution\output" rd /s /q "dist\CMSolution\output"

echo [4/4] Creating zip...
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmm"') do set TS=%%i
set ZIP=CMSolution_%TS%.zip
if exist "%ZIP%" del /f "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\CMSolution\*' -DestinationPath '%ZIP%' -CompressionLevel Optimal"

if exist "%ZIP%" (
    echo.
    echo [OK] package ready: %ZIP%
) else (
    echo [FAIL] zip creation failed
)
pause
