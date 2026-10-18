@echo off
py -3.14 -X utf8 -I -B "%~dp0single_bridge.py" --offline-demo
exit /b %errorlevel%
