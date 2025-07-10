#!/bin/bash
# Install script for PhreakBot pydle version

echo "Installing PhreakBot pydle version dependencies..."

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "pip not found. Installing pip..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "Could not install pip. Please install pip manually and run this script again."
        exit 1
    fi
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if config.json exists, if not, create it from the example
if [ ! -f config.json ]; then
    echo "Creating config.json from example..."
    cp config.json.pydle.example config.json
    echo "Please edit config.json to configure your bot."
else
    echo "config.json already exists. You may need to update it for the pydle version."
    echo "See config.json.pydle.example for reference."
fi

echo "Installation complete!"
echo "To run the bot, use: python3 phreakbot_pydle.py"