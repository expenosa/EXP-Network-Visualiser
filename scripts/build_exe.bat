@echo off
REM cd to project top level directory
cd /D "%~dp0"
cd ..

rmdir /q /s dist\
rmdir /q /s build\

REM Create a single exe file with the program
env\scripts\python -m PyInstaller --clean --specpath src\resources\ -i icon.ico --version-file file_version_info.txt^
 --noconsole --onefile --collect-all pyvis --collect-all nicegui src\python\expnetvis.py

copy README.md dist\
copy LICENSE.md dist\
xcopy lib\ dist\lib\ /E

cd dist\
rename expnetvis.exe "EXP Network Visualiser.exe"
..\env\scripts\python ..\scripts\zipfiles.py EXPNetworkVisualiser.zip lib\ *.md *.exe
cd ..
rmdir /q /s build\