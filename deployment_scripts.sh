#!/bin/bash
# deploy.sh - Deployment script for Network Designer using uv

set -e  # Exit on error

echo "================================================"
echo "Network Designer - Deployment Script (uv)"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "unknown")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo -e "${GREEN}Detected OS: $OS${NC}"

# Function to install uv
install_uv() {
    echo -e "${YELLOW}Checking for uv installation...${NC}"
    
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}✓ uv is already installed${NC}"
        uv --version
        return 0
    fi
    
    echo -e "${YELLOW}Installing uv...${NC}"
    
    # Install uv using the official installer
    case $OS in
        linux|macos)
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Add to PATH for current session
            export PATH="$HOME/.cargo/bin:$PATH"
            ;;
        windows)
            powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
            ;;
        *)
            echo -e "${RED}Unsupported OS for automatic uv installation${NC}"
            echo "Please install uv manually from: https://github.com/astral-sh/uv"
            exit 1
            ;;
    esac
    
    # Verify installation
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}✓ uv installed successfully${NC}"
        uv --version
    else
        echo -e "${RED}Failed to install uv${NC}"
        echo "Please install manually from: https://github.com/astral-sh/uv"
        exit 1
    fi
}

# Function to check Python installation
check_python() {
    echo -e "${YELLOW}Checking Python installation...${NC}"
    
    # First try to use uv's Python detection
    if uv python list &> /dev/null; then
        PYTHON_VERSION=$(uv python list | grep -E "^\*" | awk '{print $2}')
        if [ -z "$PYTHON_VERSION" ]; then
            PYTHON_VERSION=$(uv python list | head -1 | awk '{print $1}')
        fi
        echo -e "${GREEN}✓ Python detected by uv: $PYTHON_VERSION${NC}"
    else
        # Fallback to system Python check
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}Python is not installed${NC}"
            echo "Installing Python with uv..."
            uv python install 3.11
            return $?
        fi
        
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        echo -e "${GREEN}✓ Found system Python: $PYTHON_VERSION${NC}"
    fi
    
    # Check if version is 3.7+
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 7 ]; then
        echo -e "${GREEN}✓ Python version is compatible${NC}"
    else
        echo -e "${YELLOW}Python 3.7+ is required. Installing Python 3.11 with uv...${NC}"
        uv python install 3.11
    fi
}

# Function to install Kivy dependencies
install_kivy_deps() {
    echo -e "${YELLOW}Installing Kivy system dependencies...${NC}"
    
    case $OS in
        linux)
            if [[ "$DISTRO" == "Ubuntu" ]] || [[ "$DISTRO" == "Debian" ]]; then
                echo -e "${YELLOW}Installing dependencies for Ubuntu/Debian...${NC}"
                sudo apt-get update
                sudo apt-get install -y \
                    python3-pip \
                    build-essential \
                    git \
                    python3-dev \
                    ffmpeg \
                    libsdl2-dev \
                    libsdl2-image-dev \
                    libsdl2-mixer-dev \
                    libsdl2-ttf-dev \
                    libportmidi-dev \
                    libswscale-dev \
                    libavformat-dev \
                    libavcodec-dev \
                    zlib1g-dev \
                    libgstreamer1.0-dev \
                    gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good
            elif [[ "$DISTRO" == "Fedora" ]] || [[ "$DISTRO" == "RedHat" ]]; then
                echo -e "${YELLOW}Installing dependencies for Fedora/RHEL...${NC}"
                sudo dnf install -y \
                    python3-devel \
                    SDL2-devel \
                    SDL2_image-devel \
                    SDL2_mixer-devel \
                    SDL2_ttf-devel \
                    gstreamer1-plugins-base \
                    gstreamer1-plugins-good
            elif [[ "$DISTRO" == "Arch" ]]; then
                echo -e "${YELLOW}Installing dependencies for Arch Linux...${NC}"
                sudo pacman -S --noconfirm \
                    python-pip \
                    sdl2 \
                    sdl2_image \
                    sdl2_mixer \
                    sdl2_ttf \
                    gstreamer \
                    gst-plugins-base \
                    gst-plugins-good
            else
                echo -e "${YELLOW}Please install SDL2 and GStreamer dependencies manually${NC}"
                echo "Or run: ./install_kivy_deps.sh"
            fi
            ;;
        macos)
            echo -e "${YELLOW}Installing dependencies for macOS...${NC}"
            if command -v brew &> /dev/null; then
                brew install \
                    sdl2 \
                    sdl2_image \
                    sdl2_ttf \
                    sdl2_mixer \
                    gstreamer \
                    pkg-config
            else
                echo -e "${RED}Homebrew not found. Please install it first:${NC}"
                echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            ;;
        windows)
            echo -e "${GREEN}Windows: Kivy wheels include dependencies${NC}"
            ;;
    esac
    
    echo -e "${GREEN}✓ System dependencies installed${NC}"
}

# Function to check Kivy
check_kivy() {
    echo -e "${YELLOW}Checking Kivy installation...${NC}"
    
    # Try to import kivy using uv run
    if uv run python -c "import kivy" 2>/dev/null; then
        echo -e "${GREEN}✓ Kivy is installed${NC}"
        KIVY_VERSION=$(uv run python -c "import kivy; print(kivy.__version__)")
        echo -e "${GREEN}  Kivy version: $KIVY_VERSION${NC}"
    else
        echo -e "${YELLOW}Kivy is not installed. It will be installed with project dependencies.${NC}"
    fi
}

# Function to setup uv project
setup_uv_project() {
    echo -e "${YELLOW}Setting up uv project...${NC}"
    
    # Initialize uv project if not exists
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${YELLOW}Creating pyproject.toml...${NC}"
        cat > pyproject.toml << 'EOF'
[project]
name = "network-designer"
version = "2.0.0"
description = "Visual Network to Docker/Terraform Converter"
readme = "README.md"
requires-python = ">=3.7"
dependencies = [
    "kivy>=2.2.0",
    "kivymd>=1.1.0",
]

[project.scripts]
network-designer = "network_designer:main"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "black>=23.3.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pyinstaller>=5.13.0",
]

[build-system]
requires = ["setuptools>=61.0", "wheel", "cython>=0.29.0"]
build-backend = "setuptools.build_meta"
EOF
        echo -e "${GREEN}✓ pyproject.toml created${NC}"
    else
        echo -e "${GREEN}✓ pyproject.toml already exists${NC}"
    fi
    
    # Create .python-version file for uv
    if [ ! -f ".python-version" ]; then
        echo "3.11" > .python-version
        echo -e "${GREEN}✓ .python-version file created${NC}"
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        uv venv
        echo -e "${GREEN}✓ Virtual environment created in .venv${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    # Install dependencies including Kivy
    echo -e "${YELLOW}Installing Python dependencies with uv...${NC}"
    uv pip install kivy kivymd
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    
    # Sync any additional dependencies
    echo -e "${YELLOW}Syncing project dependencies...${NC}"
    uv sync
    echo -e "${GREEN}✓ Dependencies synced${NC}"
}

# Function to create run script
create_run_script() {
    echo -e "${YELLOW}Creating run script...${NC}"
    
    cat > run.sh << 'EOF'
#!/bin/bash
# Run script for Network Designer with uv

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Please run ./deploy.sh first"
    exit 1
fi

# Run the application using uv
echo "Starting Network Designer..."
uv run python network_designer.py "$@"
EOF
    
    chmod +x run.sh
    echo -e "${GREEN}✓ Run script created${NC}"
    
    # Create Windows batch file
    cat > run.bat << 'EOF'
@echo off
REM Run script for Network Designer with uv on Windows

cd /d "%~dp0"

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: uv is not installed
    echo Please run deploy.sh first
    pause
    exit /b 1
)

REM Run the application using uv
echo Starting Network Designer...
uv run python network_designer.py %*
EOF
    
    echo -e "${GREEN}✓ Windows run script created${NC}"
}

# Function to create desktop shortcut
create_shortcut() {
    echo -e "${YELLOW}Creating desktop shortcut...${NC}"
    
    case $OS in
        linux)
            DESKTOP_FILE="$HOME/.local/share/applications/network-designer.desktop"
            mkdir -p "$HOME/.local/share/applications"
            cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Network Designer
Comment=Visual Network to Docker/Terraform Converter
Exec=$PWD/run.sh
Icon=$PWD/icon.png
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF
            chmod +x "$DESKTOP_FILE"
            echo -e "${GREEN}✓ Desktop shortcut created at $DESKTOP_FILE${NC}"
            ;;
            
        macos)
            echo -e "${YELLOW}Creating macOS app bundle...${NC}"
            ./create_macos_app.sh
            ;;
            
        windows)
            echo -e "${YELLOW}To create a Windows shortcut, run:${NC}"
            echo "  powershell -ExecutionPolicy Bypass -File create_windows_shortcut.ps1"
            ;;
    esac
}

# Function to install development dependencies
install_dev_deps() {
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    
    uv pip install pytest pytest-cov black ruff mypy pyinstaller
    
    echo -e "${GREEN}✓ Development dependencies installed${NC}"
}

# Function to create test runner script
create_test_script() {
    echo -e "${YELLOW}Creating test runner script...${NC}"
    
    cat > test.sh << 'EOF'
#!/bin/bash
# Test runner script for Network Designer

echo "Running tests with uv..."

# Run pytest with coverage if available
if uv run python -c "import pytest_cov" 2>/dev/null; then
    uv run pytest test_network_designer.py -v --cov=network_designer --cov-report=term-missing
else
    uv run pytest test_network_designer.py -v
fi
EOF
    
    chmod +x test.sh
    echo -e "${GREEN}✓ Test script created${NC}"
}

# Function to create build script
create_build_script() {
    echo -e "${YELLOW}Creating build scripts...${NC}"
    
    # Create build_executable.sh
    cat > build_executable.sh << 'EOF'
#!/bin/bash
# Build standalone executable for Network Designer using uv

set -e

echo "Building standalone executable with uv..."

# Install pyinstaller if not present
uv pip install pyinstaller

# Build executable
uv run pyinstaller --onefile \
    --windowed \
    --name "NetworkDesigner" \
    --add-data "README.md:." \
    --hidden-import kivy \
    --hidden-import kivymd \
    network_designer.py

echo "✓ Executable created in dist/NetworkDesigner"

# Create distribution package
echo "Creating distribution package..."
mkdir -p dist/NetworkDesigner-dist
cp dist/NetworkDesigner dist/NetworkDesigner-dist/
cp README.md dist/NetworkDesigner-dist/
cp -r projects dist/NetworkDesigner-dist/ 2>/dev/null || mkdir dist/NetworkDesigner-dist/projects

echo "✓ Distribution package created in dist/NetworkDesigner-dist/"
EOF
    
    chmod +x build_executable.sh
    echo -e "${GREEN}✓ Build script created${NC}"
}

# Function to create uv-specific helper scripts
create_uv_helpers() {
    echo -e "${YELLOW}Creating uv helper scripts...${NC}"
    
    # Create update script
    cat > update.sh << 'EOF'
#!/bin/bash
# Update Network Designer dependencies with uv

echo "Updating Network Designer..."

# Self-update uv
echo "Updating uv..."
uv self update

# Update dependencies
echo "Updating dependencies..."
uv sync --upgrade

echo "✓ Update complete"
EOF
    
    chmod +x update.sh
    
    # Create shell activation script
    cat > shell.sh << 'EOF'
#!/bin/bash
# Activate Network Designer environment shell

echo "Activating Network Designer environment..."
uv run $SHELL
EOF
    
    chmod +x shell.sh
    
    # Create pip install helper
    cat > install-package.sh << 'EOF'
#!/bin/bash
# Install additional packages to Network Designer environment

if [ $# -eq 0 ]; then
    echo "Usage: ./install-package.sh <package-name>"
    exit 1
fi

echo "Installing $@ with uv..."
uv pip install "$@"
echo "✓ Package installed"
EOF
    
    chmod +x install-package.sh
    
    echo -e "${GREEN}✓ Helper scripts created${NC}"
}

# Create macOS app creation script
create_macos_app_script() {
    cat > create_macos_app.sh << 'EOF'
#!/bin/bash
# Create macOS .app bundle for Network Designer with uv

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "This script is for macOS only"
    exit 1
fi

APP_NAME="Network Designer"
APP_DIR="$APP_NAME.app"

echo "Creating macOS app bundle..."

# Create app structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Network Designer</string>
    <key>CFBundleDisplayName</key>
    <string>Network Designer</string>
    <key>CFBundleIdentifier</key>
    <string>com.networkdesigner.app</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>NetworkDesigner</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Create launcher script
cat > "$APP_DIR/Contents/MacOS/NetworkDesigner" << LAUNCHER
#!/bin/bash
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$DIR/../../../"

# Check for uv
if ! command -v uv &> /dev/null; then
    osascript -e 'display alert "uv not found" message "Please install uv and run deploy.sh first"'
    exit 1
fi

# Run with uv
uv run python network_designer.py
LAUNCHER

chmod +x "$APP_DIR/Contents/MacOS/NetworkDesigner"

# Copy resources
cp network_designer.py "$APP_DIR/Contents/Resources/"
cp README.md "$APP_DIR/Contents/Resources/" 2>/dev/null || true

echo "✓ macOS app bundle created: $APP_DIR"
echo "To install: drag $APP_DIR to /Applications"
EOF
    
    chmod +x create_macos_app.sh
}

# Create Windows PowerShell shortcut script
create_windows_shortcut_script() {
    cat > create_windows_shortcut.ps1 << 'EOF'
# PowerShell script to create Windows shortcut for Network Designer with uv

$ShortcutPath = "$env:USERPROFILE\Desktop\Network Designer.lnk"
$TargetPath = "$PSScriptRoot\run.bat"
$WorkingDirectory = $PSScriptRoot

Write-Host "Creating Windows shortcut..." -ForegroundColor Yellow

# Create run.bat if it doesn't exist
if (!(Test-Path "run.bat")) {
    Write-Host "run.bat already exists" -ForegroundColor Green
}

# Create shortcut
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDirectory
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Visual Network to Docker/Terraform Converter"
$Shortcut.Save()

Write-Host "✓ Windows shortcut created on Desktop" -ForegroundColor Green
EOF
}

# Create uninstall script
create_uninstall_script() {
    cat > uninstall.sh << 'EOF'
#!/bin/bash
# Uninstall script for Network Designer

echo "Uninstalling Network Designer..."

# Remove virtual environment
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "✓ Virtual environment removed"
fi

# Remove uv cache for this project
if command -v uv &> /dev/null; then
    uv cache clean
    echo "✓ uv cache cleaned"
fi

# Remove desktop shortcut (Linux)
if [ -f "$HOME/.local/share/applications/network-designer.desktop" ]; then
    rm "$HOME/.local/share/applications/network-designer.desktop"
    echo "✓ Desktop shortcut removed"
fi

# Remove macOS app bundle
if [ -d "Network Designer.app" ]; then
    rm -rf "Network Designer.app"
    echo "✓ macOS app bundle removed"
fi

# Remove build artifacts
if [ -d "build" ]; then
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi
if [ -f "*.spec" ]; then
    rm *.spec
fi

# Remove __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "✓ Uninstall completed"
echo "Note: The application files are still present. Delete the directory to completely remove."
EOF
    
    chmod +x uninstall.sh
}

# Create Kivy test script
create_kivy_test() {
    cat > test_kivy.py << 'EOF'
#!/usr/bin/env python3
"""Test script to verify Kivy installation"""

import sys

def test_kivy():
    try:
        import kivy
        print(f"✓ Kivy {kivy.__version__} is installed and working")
        
        # Test Kivy App
        from kivy.app import App
        from kivy.uix.label import Label
        
        class TestApp(App):
            def build(self):
                return Label(text='Kivy is working!\nClose this window to continue.')
        
        # Only run GUI test if not in CI/headless environment
        import os
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            print("Starting test window...")
            TestApp().run()
        else:
            print("No display detected, skipping GUI test")
            
        return True
        
    except ImportError as e:
        print(f"✗ Kivy import failed: {e}")
        return False

def test_kivymd():
    try:
        import kivymd
        print(f"✓ KivyMD {kivymd.__version__} is installed")
        return True
    except ImportError:
        print("ℹ KivyMD is not installed (optional)")
        return True

if __name__ == "__main__":
    kivy_ok = test_kivy()
    kivymd_ok = test_kivymd()
    
    if kivy_ok:
        print("\n✓ All required dependencies are installed!")
        sys.exit(0)
    else:
        print("\n✗ Some dependencies failed to install.")
        sys.exit(1)
EOF
    
    chmod +x test_kivy.py
}

# Main deployment process
main() {
    echo ""
    echo -e "${GREEN}Starting deployment process...${NC}"
    echo "------------------------------"
    
    # Install uv
    install_uv
    
    # Check Python
    check_python
    
    # Ask about Kivy dependencies
    read -p "Install Kivy system dependencies? (recommended) [y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_kivy_deps
    else
        echo -e "${YELLOW}Skipping system dependencies. You may need to install them manually.${NC}"
        echo "Run ./install_kivy_deps.sh for comprehensive installation"
    fi
    
    # Setup uv project
    setup_uv_project
    
    # Check Kivy
    check_kivy
    
    # Create scripts
    create_run_script
    create_test_script
    create_build_script
    create_uv_helpers
    create_macos_app_script
    create_windows_shortcut_script
    create_uninstall_script
    create_kivy_test
    
    # Ask about development dependencies
    read -p "Install development dependencies (testing, linting, building)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_dev_deps
    fi
    
    # Create desktop shortcut
    read -p "Create desktop shortcut? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_shortcut
    fi
    
    echo ""
    echo "================================================"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo "================================================"
    echo ""
    echo -e "${YELLOW}Available commands:${NC}"
    echo "  ./run.sh                 - Run the application"
    echo "  ./test.sh                - Run tests"
    echo "  ./test_kivy.py           - Test Kivy installation"
    echo "  ./update.sh              - Update dependencies"
    echo "  ./shell.sh               - Activate environment shell"
    echo "  ./build_executable.sh    - Build standalone executable"
    echo "  ./install-package.sh     - Install additional packages"
    echo "  ./install_kivy_deps.sh   - Install system dependencies (comprehensive)"
    echo "  ./uninstall.sh          - Uninstall the application"
    echo ""
    echo -e "${YELLOW}Using uv directly:${NC}"
    echo "  uv run python network_designer.py    - Run directly with uv"
    echo "  uv pip list                          - List installed packages"
    echo "  uv pip install <package>             - Install a package"
    echo "  uv sync                              - Sync dependencies"
    echo "  uv python list                       - List Python versions"
    echo ""
    echo -e "${YELLOW}Testing Kivy:${NC}"
    echo "  python3 test_kivy.py                 - Test Kivy installation"
    echo ""
}

# Run main function
main
