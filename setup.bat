@echo off
:: PhreakBot Setup Script for Windows
:: This script installs all dependencies and sets up PhreakBot

echo PhreakBot Setup
echo ===============
echo.

:: Check if Python is installed
echo Checking Python installation...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python 3.6 or higher.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=*" %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%a
echo Python version: %PYTHON_VERSION%

:: Extract major and minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.6 or higher is required.
    pause
    exit /b 1
) else (
    if %PYTHON_MAJOR% EQU 3 (
        if %PYTHON_MINOR% LSS 6 (
            echo Error: Python 3.6 or higher is required.
            pause
            exit /b 1
        )
    )
)

:: Check if pip is installed
echo.
echo Checking pip installation...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Warning: pip not found. Attempting to install pip...

    :: Try to download get-pip.py
    powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py"
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to download get-pip.py. Please install pip manually.
        pause
        exit /b 1
    )

    :: Run get-pip.py
    python get-pip.py
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install pip. Please install pip manually.
        del get-pip.py
        pause
        exit /b 1
    )

    del get-pip.py

    :: Check if pip installation was successful
    python -m pip --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install pip. Please install pip manually.
        pause
        exit /b 1
    )
)

echo pip is installed.

:: Install required packages
echo.
echo Installing required packages...
python -m pip install irc
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install required packages.
    pause
    exit /b 1
)

echo Required packages installed successfully.

:: Create directories
echo.
echo Creating directories...
if not exist modules mkdir modules
if not exist extra_modules mkdir extra_modules
echo Directories created.

:: Run installation script
echo.
echo Running installation script...
echo You can customize the bot configuration by providing arguments:
echo Example: python install.py --server irc.example.com --nickname MyBot --channel "#mychannel"
echo.
echo Press Enter to continue with default settings, or Ctrl+C to cancel and run with custom settings later.
pause > nul

python install.py

echo.
echo Setup complete!
echo You can now start PhreakBot by running: python phreakbot.py
echo When the bot connects to IRC, claim ownership by typing: !owner *!^<user^>@^<hostname^>
echo (The bot will suggest an appropriate format based on your connection)

pause
