#!/bin/bash
# PhreakBot Setup Script for Unix-like systems (macOS, Linux)
# This script installs all dependencies and sets up PhreakBot

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}PhreakBot Setup${RESET}"
echo "================="
echo

# Check if Python is installed
echo -e "${BOLD}Checking Python installation...${RESET}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found. Please install Python 3.6 or higher.${RESET}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "Python version: ${GREEN}$PYTHON_VERSION${RESET}"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    echo -e "${RED}Error: Python 3.6 or higher is required.${RESET}"
    exit 1
fi

# Check if pip is installed
echo -e "\n${BOLD}Checking pip installation...${RESET}"
if ! $PYTHON_CMD -m pip --version &>/dev/null; then
    echo -e "${YELLOW}Warning: pip not found. Attempting to install pip...${RESET}"

    # Try to install pip
    if command -v curl &>/dev/null; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
    elif command -v wget &>/dev/null; then
        wget https://bootstrap.pypa.io/get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
    else
        echo -e "${RED}Error: Neither curl nor wget found. Please install pip manually.${RESET}"
        exit 1
    fi

    # Check if pip installation was successful
    if ! $PYTHON_CMD -m pip --version &>/dev/null; then
        echo -e "${RED}Error: Failed to install pip. Please install pip manually.${RESET}"
        exit 1
    fi
fi

echo -e "${GREEN}pip is installed.${RESET}"

# Install required packages
echo -e "\n${BOLD}Installing required packages...${RESET}"
$PYTHON_CMD -m pip install irc

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install required packages.${RESET}"
    exit 1
fi

echo -e "${GREEN}Required packages installed successfully.${RESET}"

# Create directories
echo -e "\n${BOLD}Creating directories...${RESET}"
mkdir -p modules extra_modules
echo -e "${GREEN}Directories created.${RESET}"

# Make scripts executable
echo -e "\n${BOLD}Making scripts executable...${RESET}"
chmod +x phreakbot.py install.py
echo -e "${GREEN}Scripts are now executable.${RESET}"

# Run installation script
echo -e "\n${BOLD}Running installation script...${RESET}"
echo "You can customize the bot configuration by providing arguments:"
echo "Example: ./install.py --server irc.example.com --nickname MyBot --channel \"#mychannel\""
echo
echo -e "${YELLOW}Press Enter to continue with default settings, or Ctrl+C to cancel and run with custom settings later.${RESET}"
read -r

$PYTHON_CMD install.py

echo -e "\n${BOLD}${GREEN}Setup complete!${RESET}"
echo -e "You can now start PhreakBot by running: ${BOLD}./phreakbot.py${RESET}"
echo -e "When the bot connects to IRC, claim ownership by typing: ${BOLD}!owner *!<user>@<hostname>${RESET}"
echo -e "(The bot will suggest an appropriate format based on your connection)"
