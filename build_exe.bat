@echo off
echo ==========================================
echo Building Huawei Screenshot Generator .exes
echo ==========================================

:: Check pyinstaller exists
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pyinstaller not found. Run: pip install pyinstaller
    pause
    exit /b 1
)

:: Clean old builds
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

:: 1. run.exe - main processor (needs playwright browser)
echo [1/6] Building run.exe ...
pyinstaller --onefile --name run ^
    --add-data "run_config.json;." ^
    --add-data "templates;templates" ^
    run.py

:: 2. log_stats.exe - log analyzer (bonus utility)
echo [2/6] Building log_stats.exe ...
pyinstaller --onefile --name log_stats ^
    --add-data "run_config.json;." ^
    log_stats.py

:: 3. putpnginxlsx.exe - Excel inserter
echo [3/6] Building putpnginxlsx.exe ...
pyinstaller --onefile --name putpnginxlsx ^
    --add-data "putpnginxlsx_config.json;." ^
    putpnginxlsx.py

:: 4. putpnginword.exe - Word inserter (needs win32com)
echo [4/6] Building putpnginword.exe ...
pyinstaller --onefile --name putpnginword ^
    --add-data "putpnginword_config.json;." ^
    --hidden-import pythoncom ^
    --hidden-import pywintypes ^
    --hidden-import win32com.client ^
    putpnginword.py

:: 5. whitelist_gui.exe - GUI whitelist picker
echo [5/6] Building whitelist_gui.exe ...
pyinstaller --onefile --name whitelist_gui ^
    --add-data "run_config.json;." ^
    whitelist_gui.py

REM Unified CLI (huawei-tool)
echo [6/7] Building huawei-tool.exe ...
pyinstaller --clean -y HuaweiScreenshotTool_Unify.spec

echo.

echo [7/7] Copying huawei-tool.exe to HuaweiScreenshotTool folder...
if not exist HuaweiScreenshotTool\NUL mkdir HuaweiScreenshotTool
copy /Y "dist\huawei-tool.exe" "HuaweiScreenshotTool\huawei-tool.exe" >nul
if errorlevel 1 (
    echo ERROR: copy failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build complete! Output in dist\ folder
echo ==========================================
echo.
echo Files created:
dir /b dist\*.exe 2>nul
echo.
echo huawei-tool.exe also copied to: HuaweiScreenshotTool\huawei-tool.exe
echo.
pause
