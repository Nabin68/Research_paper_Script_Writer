@echo off
title Growth School - Agent Console
cd /d "%~dp0"

if not exist "node_modules" (
  echo First run - installing dependencies. This takes a minute...
  call npm install
  if errorlevel 1 (
    echo.
    echo Install failed. Make sure Node.js is installed, then try again.
    pause
    exit /b 1
  )
)

echo.
echo   Starting the agent console...
echo   It will open at http://localhost:5180
echo   Close this window to stop it.
echo.

call npm run dev
pause
