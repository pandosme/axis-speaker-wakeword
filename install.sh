#!/bin/bash
# Installation script for Axis Speaker Wakeword Monitor

set -e  # Exit on error

echo "============================================================"
echo "  Axis Speaker Wakeword Monitor - Installation"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda is not installed!${NC}"
    echo ""
    echo "Please install Miniconda or Anaconda first:"
    echo "  1. Download Miniconda:"
    echo "     wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  2. Install:"
    echo "     bash Miniconda3-latest-Linux-x86_64.sh"
    echo "  3. Restart your terminal and run this script again"
    exit 1
fi

echo -e "${GREEN}✓ Conda found${NC}"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  FFmpeg is not installed${NC}"
    echo ""
    echo "Installing FFmpeg..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    else
        echo -e "${RED}Please install FFmpeg manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ FFmpeg found${NC}"

# Check if environment already exists
if conda env list | grep -q "^wakeword "; then
    echo ""
    echo -e "${YELLOW}Conda environment 'wakeword' already exists${NC}"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda env remove -n wakeword -y
    else
        echo "Skipping environment creation"
        echo "To activate existing environment: conda activate wakeword"
        exit 0
    fi
fi

# Create conda environment
echo ""
echo "Creating conda environment 'wakeword'..."
conda env create -f environment.yml

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate the environment:"
echo "     conda activate wakeword"
echo ""
echo "  2. Run the setup wizard:"
echo "     python setup.py"
echo ""
echo "  3. Start the service:"
echo "     python app.py"
echo ""
