@echo off
REM Daily AI paper digest — entry point for Windows Task Scheduler or double-click.
REM Always runs from this folder so it finds sources.json / papers.csv.
cd /d "%~dp0"

set "PY=python"
where python >nul 2>&1 || set "PY=C:\Program Files\Python312\python.exe"

echo ==== %date% %time% ==== >> run.log
"%PY%" finding_papers.py --once >> run.log 2>&1
echo. >> run.log
