@echo off
rem Cai tab ARV Tools (pyRevit). Them -Go de go dang ky.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cai_dat.ps1" %*
pause
