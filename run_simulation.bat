@echo off
setlocal

REM ============================================================
REM Pegasus Simulator - Windows 11 Launcher
REM ============================================================
REM This script sets up the environment and launches the
REM Pegasus Simulator with Isaac Sim 6.2 on Windows 11.
REM ============================================================

REM Check if ISAAC_HOME is set
if not defined ISAAC_HOME (
    echo ERROR: ISAAC_HOME environment variable is not set.
    echo Please set it to your Isaac Sim 6.2 installation path.
    echo Example: setx ISAAC_HOME "C:\Users\YourUser\AppData\Local\ov\pkg\isaac_sim-6.2.0"
    pause
    exit /b 1
)

REM Set the Python path to use the Isaac Sim bundled Python
set "ISAAC_PYTHON=%ISAAC_HOME%\python.bat"

REM Set the path to the Isaac Sim kit executable
set "ISAAC_KIT=%ISAAC_HOME%\kit\isaac-sim.bat"

REM Add the extension to the Isaac Sim extension search path
set "OMNI_KIT_ALLOW_ROOT=1"
set "ISAAC_EXTENSIONS=%~dp0extensions"

REM Run the link script to register the extension with Isaac Sim
echo Registering Pegasus Simulator extension with Isaac Sim...
call "%~dp0tools\packman\python.bat" "%~dp0tools\scripts\link_app.py" --path "%ISAAC_HOME%"
if %errorlevel% neq 0 (
    echo Warning: Could not link extension automatically. You may need to enable it manually in the Isaac Sim Extension Manager.
)

REM Launch Isaac Sim with the Pegasus Simulator extension
echo Starting Pegasus Simulator with Isaac Sim 6.2...
call "%ISAAC_KIT%" --exts "pegasus.simulator" --no-window

endlocal
