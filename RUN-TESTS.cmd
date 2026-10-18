@echo off
py -3.14 -X utf8 -I -B "%~dp0run_tests.py"
exit /b %errorlevel%
