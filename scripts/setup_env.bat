@echo off
REM cd to project top level directory
cd /D "%~dp0"
cd ..

REM create the virtual enviroment and install dependencies
python -m venv env
env\scripts\pip.exe install -r requirements.txt -r requirements.dev.txt