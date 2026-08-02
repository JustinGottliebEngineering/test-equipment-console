@echo off
setlocal

cd /d "%~dp0"

echo.
echo ============================================
echo  Test Equipment Console - Windows Build
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Expected: .venv\Scripts\python.exe
    echo.
    echo Create it with:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -e ".[dev]"
    echo.
    exit /b 1
)

set "PYTHON=.venv\Scripts\python.exe"

echo Installing or updating PyInstaller...
"%PYTHON%" -m pip install --upgrade pyinstaller

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller installation failed.
    exit /b 1
)

echo.
echo Running tests before build...
"%PYTHON%" -m pytest

if errorlevel 1 (
    echo.
    echo ERROR: Tests failed. Build cancelled.
    exit /b 1
)

echo.
echo Removing previous build output...

if exist "build" (
    rmdir /s /q "build"
)

if exist "dist" (
    rmdir /s /q "dist"
)

if exist "TestEquipmentConsole.spec" (
    del /q "TestEquipmentConsole.spec"
)

echo.
echo Building standalone Windows executable...

"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onefile ^
    --name "TestEquipmentConsole" ^
    --collect-all pyvisa ^
    --collect-all PySide6 ^
    "run.py"

if errorlevel 1 (
    echo.
    echo ERROR: Windows build failed.
    exit /b 1
)

if not exist "dist\TestEquipmentConsole.exe" (
    echo.
    echo ERROR: Build completed without producing the expected executable.
    exit /b 1
)

echo.
echo ============================================
echo  Build completed successfully
echo ============================================
echo.
echo Executable:
echo   %CD%\dist\TestEquipmentConsole.exe
echo.

endlocal
exit /b 0