@echo off
rem Cai rieng nut Vach kinh (tab Archivina, pyRevit). Them -Go de go dang ky.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cai_dat.ps1" %*
pause
