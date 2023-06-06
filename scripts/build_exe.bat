@echo off
REM cd to project top level directory
cd /D "%~dp0"
cd ..

rmdir /q /s dist\
rmdir /q /s build\

REM Create a single exe file with the program

REM env\scripts\python -m PyInstaller --clean -i src\resources\ffmpeg_icon.ico --version-file src\resources\file_version_info.txt --onefile --collect-all pyvis --add-data env\Lib\site-packages\nicegui;nicegui src\python\network_ui.py
env\scripts\python -m PyInstaller --clean --specpath src\resources\ -i icon.ico --version-file file_version_info.txt^
 --noconsole --onefile --collect-all pyvis --collect-all nicegui src\python\network_ui.py

copy README.md dist\
xcopy lib\ dist\lib\ /E

cd dist\
..\env\scripts\python ..\scripts\zipfiles.py NetworkVisualiser.zip lib\ README.md *.exe
cd ..
rmdir /q /s build\