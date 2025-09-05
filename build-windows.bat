@echo off
rem memAI Windows Build Script
rem Run this on Windows to create memAI-windows.exe

echo Building memAI Windows executable...
echo.

rem Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

rem Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

rem Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist\memAI-windows.exe del dist\memAI-windows.exe
if exist memAI-windows.exe.spec del memAI-windows.exe.spec

rem Build Windows executable
echo Building Windows executable...
pyinstaller --onefile --name memAI-windows.exe memai.py

echo.
if exist dist\memAI-windows.exe (
    echo SUCCESS: Windows executable created at dist\memAI-windows.exe
    echo File size: 
    dir dist\memAI-windows.exe | find "memAI-windows.exe"
) else (
    echo ERROR: Build failed
)

echo.
pause
