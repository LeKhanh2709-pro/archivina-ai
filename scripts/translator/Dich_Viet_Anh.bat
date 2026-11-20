@echo off
rem Mo cua so dich Viet <-> Anh (bam dup file nay)
set "APP=%~dp0translator.py"
set "PYW=%~dp0..\..\_tools\venv\Scripts\pythonw.exe"
if exist "%PYW%" (
  start "" "%PYW%" "%APP%"
) else (
  start "" pyw "%APP%"
)
