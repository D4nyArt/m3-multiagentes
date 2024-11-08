@echo off
setlocal

REM Set the path to your Python executable and main.py script
set PYTHON_PATH=python
set SCRIPT_PATH=Main.py

REM Run the simulation 5 times with mode = 1
for /L %%i in (1,1,10) do (
    echo Running simulation %%i 
    %PYTHON_PATH% %SCRIPT_PATH% Simulacion --cars 5 --Delta 1
)

endlocal