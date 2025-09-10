#!/bin/bash
# install_kivy_deps.sh - Comprehensive Kivy Dependencies Installer
# Supports multiple Linux distributions, macOS, and Windows (WSL)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║        Kivy Dependencies Installer for                  ║"
    echo "║            Network Designer Application                  ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Detect operating system and distribution
detect_os() {
    echo -e "${BLUE}Detecting operating system...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        
        # Detect Linux distribution
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            DISTRO_VERSION=$VERSION_ID
            DISTRO_NAME=$NAME
        elif command -v lsb_release &> /dev/null; then
            DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
            DISTRO_VERSION=$(lsb_release -sr)
            DISTRO_NAME=$(lsb_release -sd)
        elif [ -f /etc/debian_version ]; then
            DISTRO="debian"
            DISTRO_VERSION=$(cat /etc/debian_version)
            DISTRO_NAME="Debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="rhel"
            DISTRO_NAME="Red Hat"
        else
            DISTRO="unknown"
            DISTRO_NAME="Unknown Linux"
        fi
        
        echo -e "${GREEN}✓ Detected: $DISTRO_NAME ($DISTRO $DISTRO_VERSION)${NC}"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
        DISTRO_VERSION=$(sw_vers -productVersion)
        DISTRO_NAME="macOS $DISTRO_VERSION"
        echo -e "${GREEN}✓ Detected: $DISTRO_NAME${NC}"
        
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        DISTRO="windows"
        DISTRO_NAME="Windows (using WSL recommended)"
        echo -e "${YELLOW}⚠ Detected: $DISTRO_NAME${NC}"
        
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        OS="freebsd"
        DISTRO="freebsd"
        DISTRO_NAME="FreeBSD"
        echo -e "${GREEN}✓ Detected: $DISTRO_NAME${NC}"
        
    else
        OS="unknown"
        DISTRO="unknown"
        DISTRO_NAME="Unknown OS"
        echo -e "${RED}✗ Unknown operating system: $OSTYPE${NC}"
    fi
}

# Check if running with sudo (for Linux)
check_sudo() {
    if [[ "$OS" == "linux" ]] && [[ $EUID -ne 0 ]]; then
        if command -v sudo &> /dev/null; then
            echo -e "${YELLOW}This script requires sudo privileges to install system packages.${NC}"
            echo -e "${YELLOW}You may be prompted for your password.${NC}"
            echo ""
        else
            echo -e "${RED}This script requires root privileges but sudo is not available.${NC}"
            echo -e "${RED}Please run as root or install sudo.${NC}"
            exit 1
        fi
    fi
}

# Check Python installation
check_python() {
    echo -e "${BLUE}Checking Python installation...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}✗ Python is not installed${NC}"
        echo -e "${YELLOW}Please install Python 3.7 or higher first${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
    
    # Check if pip is installed
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        echo -e "${YELLOW}pip is not installed. Installing pip...${NC}"
        if [[ "$OS" == "linux" ]]; then
            sudo apt-get install -y python3-pip || sudo dnf install -y python3-pip || sudo pacman -S --noconfirm python-pip
        elif [[ "$OS" == "macos" ]]; then
            $PYTHON_CMD -m ensurepip --upgrade
        fi
    fi
}

# Install dependencies for Ubuntu/Debian
install_ubuntu_debian() {
    echo -e "${BLUE}Installing Kivy dependencies for Ubuntu/Debian...${NC}"
    
    # Update package list
    sudo apt-get update
    
    # Install dependencies
    sudo apt-get install -y \
        python3-pip \
        python3-setuptools \
        python3-dev \
        build-essential \
        git \
        ffmpeg \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libportmidi-dev \
        libswscale-dev \
        libavformat-dev \
        libavcodec-dev \
        libfreetype6-dev \
        zlib1g-dev \
        libgstreamer1.0-dev \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        gstreamer1.0-tools \
        gstreamer1.0-x \
        gstreamer1.0-alsa \
        gstreamer1.0-gl \
        gstreamer1.0-gtk3 \
        gstreamer1.0-qt5 \
        gstreamer1.0-pulseaudio \
        libmtdev-dev \
        xclip \
        xsel \
        libjpeg-dev
    
    echo -e "${GREEN}✓ Ubuntu/Debian dependencies installed${NC}"
}

# Install dependencies for Fedora/RHEL/CentOS
install_fedora_rhel() {
    echo -e "${BLUE}Installing Kivy dependencies for Fedora/RHEL/CentOS...${NC}"
    
    # Install dependencies
    sudo dnf install -y \
        python3-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        git \
        SDL2-devel \
        SDL2_image-devel \
        SDL2_mixer-devel \
        SDL2_ttf-devel \
        portmidi-devel \
        libavformat-devel \
        libavcodec-devel \
        libswscale-devel \
        freetype-devel \
        zlib-devel \
        gstreamer1-devel \
        gstreamer1-plugins-base \
        gstreamer1-plugins-good \
        gstreamer1-plugins-bad-free \
        gstreamer1-plugins-ugly-free \
        gstreamer1-libav \
        gstreamer1-plugins-base-tools \
        mtdev-devel \
        xclip \
        xsel \
        libjpeg-turbo-devel
    
    echo -e "${GREEN}✓ Fedora/RHEL/CentOS dependencies installed${NC}"
}

# Install dependencies for Arch Linux
install_arch() {
    echo -e "${BLUE}Installing Kivy dependencies for Arch Linux...${NC}"
    
    # Install dependencies
    sudo pacman -S --noconfirm \
        python \
        python-pip \
        python-setuptools \
        base-devel \
        git \
        sdl2 \
        sdl2_image \
        sdl2_mixer \
        sdl2_ttf \
        portmidi \
        ffmpeg \
        freetype2 \
        zlib \
        gstreamer \
        gst-plugins-base \
        gst-plugins-good \
        gst-plugins-bad \
        gst-plugins-ugly \
        gst-libav \
        mtdev \
        xclip \
        xsel \
        libjpeg-turbo
    
    echo -e "${GREEN}✓ Arch Linux dependencies installed${NC}"
}

# Install dependencies for openSUSE
install_opensuse() {
    echo -e "${BLUE}Installing Kivy dependencies for openSUSE...${NC}"
    
    # Install dependencies
    sudo zypper install -y \
        python3-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        git \
        libSDL2-devel \
        libSDL2_image-devel \
        libSDL2_mixer-devel \
        libSDL2_ttf-devel \
        portmidi-devel \
        ffmpeg-devel \
        freetype-devel \
        zlib-devel \
        gstreamer-devel \
        gstreamer-plugins-base \
        gstreamer-plugins-good \
        gstreamer-plugins-bad \
        gstreamer-plugins-ugly \
        gstreamer-plugins-libav \
        mtdev-devel \
        xclip \
        xsel \
        libjpeg8-devel
    
    echo -e "${GREEN}✓ openSUSE dependencies installed${NC}"
}

# Install dependencies for Alpine Linux
install_alpine() {
    echo -e "${BLUE}Installing Kivy dependencies for Alpine Linux...${NC}"
    
    # Install dependencies
    sudo apk add --no-cache \
        python3 \
        python3-dev \
        py3-pip \
        build-base \
        git \
        sdl2-dev \
        sdl2_image-dev \
        sdl2_mixer-dev \
        sdl2_ttf-dev \
        portmidi-dev \
        ffmpeg-dev \
        freetype-dev \
        zlib-dev \
        gstreamer-dev \
        gst-plugins-base \
        gst-plugins-good \
        gst-plugins-bad \
        gst-plugins-ugly \
        gst-libav \
        mtdev-dev \
        xclip \
        jpeg-dev
    
    echo -e "${GREEN}✓ Alpine Linux dependencies installed${NC}"
}

# Install dependencies for macOS
install_macos() {
    echo -e "${BLUE}Installing Kivy dependencies for macOS...${NC}"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew is not installed. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    
    # Update Homebrew
    brew update
    
    # Install dependencies
    brew install \
        python3 \
        pkg-config \
        sdl2 \
        sdl2_image \
        sdl2_ttf \
        sdl2_mixer \
        portmidi \
        ffmpeg \
        freetype \
        zlib \
        gstreamer \
        gst-plugins-base \
        gst-plugins-good \
        gst-plugins-bad \
        gst-plugins-ugly \
        gst-libav \
        jpeg
    
    # Install Xcode command line tools if not present
    if ! xcode-select -p &> /dev/null; then
        echo -e "${YELLOW}Installing Xcode command line tools...${NC}"
        xcode-select --install
    fi
    
    echo -e "${GREEN}✓ macOS dependencies installed${NC}"
}

# Install dependencies for FreeBSD
install_freebsd() {
    echo -e "${BLUE}Installing Kivy dependencies for FreeBSD...${NC}"
    
    # Install dependencies
    sudo pkg install -y \
        python3 \
        py39-pip \
        git \
        sdl2 \
        sdl2_image \
        sdl2_mixer \
        sdl2_ttf \
        portmidi \
        ffmpeg \
        freetype2 \
        gstreamer1 \
        gstreamer1-plugins-base \
        gstreamer1-plugins-good \
        gstreamer1-plugins-bad \
        gstreamer1-plugins-ugly \
        gstreamer1-libav \
        mtdev \
        xclip \
        xsel \
        jpeg
    
    echo -e "${GREEN}✓ FreeBSD dependencies installed${NC}"
}

# Install dependencies for Windows (WSL)
install_windows_wsl() {
    echo -e "${BLUE}For Windows, we recommend using WSL (Windows Subsystem for Linux)${NC}"
    echo -e "${YELLOW}Please follow these steps:${NC}"
    echo ""
    echo "1. Install WSL2:"
    echo "   wsl --install"
    echo ""
    echo "2. Install Ubuntu in WSL:"
    echo "   wsl --install -d Ubuntu"
    echo ""
    echo "3. Run this script inside WSL Ubuntu"
    echo ""
    echo -e "${CYAN}Alternatively, for native Windows:${NC}"
    echo "1. Install Python from python.org"
    echo "2. Install Visual Studio Build Tools"
    echo "3. Run: pip install kivy[base,media,dev]"
    echo ""
    read -p "Press Enter to continue..."
}

# Install Python packages
install_python_packages() {
    echo -e "${BLUE}Installing Python packages...${NC}"
    
    # Upgrade pip
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel
    
    # Install Cython (required for Kivy compilation)
    $PYTHON_CMD -m pip install --upgrade Cython==0.29.36
    
    # Install Kivy and dependencies
    echo -e "${YELLOW}Installing Kivy...${NC}"
    
    if [[ "$OS" == "macos" ]]; then
        # macOS specific installation
        $PYTHON_CMD -m pip install --upgrade kivy[base,media,osx,dev]
    elif [[ "$OS" == "linux" ]]; then
        # Linux specific installation
        $PYTHON_CMD -m pip install --upgrade kivy[base,media,x11,dev]
    else
        # Generic installation
        $PYTHON_CMD -m pip install --upgrade kivy[base,media,dev]
    fi
    
    # Install KivyMD for Material Design
    $PYTHON_CMD -m pip install --upgrade kivymd
    
    echo -e "${GREEN}✓ Python packages installed${NC}"
}

# Verify installation
verify_installation() {
    echo -e "${BLUE}Verifying Kivy installation...${NC}"
    
    # Test Kivy import
    if $PYTHON_CMD -c "import kivy; print(f'Kivy version: {kivy.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✓ Kivy installed successfully${NC}"
        KIVY_VERSION=$($PYTHON_CMD -c "import kivy; print(kivy.__version__)")
        echo -e "${GREEN}  Version: $KIVY_VERSION${NC}"
    else
        echo -e "${RED}✗ Kivy installation failed${NC}"
        echo -e "${YELLOW}Trying alternative installation method...${NC}"
        
        # Try installing from source
        install_from_source
    fi
    
    # Test KivyMD import
    if $PYTHON_CMD -c "import kivymd; print(f'KivyMD version: {kivymd.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✓ KivyMD installed successfully${NC}"
        KIVYMD_VERSION=$($PYTHON_CMD -c "import kivymd; print(kivymd.__version__)")
        echo -e "${GREEN}  Version: $KIVYMD_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ KivyMD installation failed (optional)${NC}"
    fi
}

# Install from source (fallback)
install_from_source() {
    echo -e "${YELLOW}Installing Kivy from source...${NC}"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Clone Kivy repository
    git clone https://github.com/kivy/kivy.git
    cd kivy
    
    # Install dependencies
    $PYTHON_CMD -m pip install -r requirements.txt
    
    # Build and install
    $PYTHON_CMD setup.py build_ext --inplace
    $PYTHON_CMD -m pip install .
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Create test script
create_test_script() {
    echo -e "${BLUE}Creating Kivy test script...${NC}"
    
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
    except Exception as e:
        print(f"✗ Kivy test failed: {e}")
        return False

def test_kivymd():
    try:
        import kivymd
        print(f"✓ KivyMD {kivymd.__version__} is installed")
        return True
    except ImportError:
        print("ℹ KivyMD is not installed (optional)")
        return True  # Not critical

if __name__ == "__main__":
    kivy_ok = test_kivy()
    kivymd_ok = test_kivymd()
    
    if kivy_ok:
        print("\n✓ All required dependencies are installed!")
        print("You can now run the Network Designer application.")
        sys.exit(0)
    else:
        print("\n✗ Some dependencies failed to install.")
        print("Please check the error messages above.")
        sys.exit(1)
EOF
    
    chmod +x test_kivy.py
    echo -e "${GREEN}✓ Test script created: test_kivy.py${NC}"
}

# Main installation function
main() {
    print_banner
    
    # Detect OS
    detect_os
    
    # Check sudo privileges
    check_sudo
    
    # Check Python
    check_python
    
    # Install system dependencies based on OS/distro
    case "$DISTRO" in
        ubuntu|debian|raspbian|linuxmint|pop|elementary)
            install_ubuntu_debian
            ;;
        fedora|rhel|centos|rocky|almalinux)
            install_fedora_rhel
            ;;
        arch|manjaro|endeavouros)
            install_arch
            ;;
        opensuse|suse)
            install_opensuse
            ;;
        alpine)
            install_alpine
            ;;
        macos)
            install_macos
            ;;
        freebsd)
            install_freebsd
            ;;
        windows)
            install_windows_wsl
            ;;
        *)
            echo -e "${RED}Unsupported distribution: $DISTRO${NC}"
            echo -e "${YELLOW}Please install the following packages manually:${NC}"
            echo "  - SDL2 development libraries"
            echo "  - GStreamer development libraries"
            echo "  - FFmpeg"
            echo "  - Python development headers"
            echo "  - Build tools (gcc, make, etc.)"
            echo ""
            read -p "Continue with Python package installation anyway? [y/N]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    # Install Python packages
    install_python_packages
    
    # Verify installation
    verify_installation
    
    # Create test script
    create_test_script
    
    # Final message
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}        Kivy Dependencies Installation Complete!           ${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Test the installation: ${BOLD}python3 test_kivy.py${NC}"
    echo -e "  2. Run the application: ${BOLD}python3 network_designer.py${NC}"
    echo ""
    echo -e "${YELLOW}If you encounter any issues:${NC}"
    echo -e "  - Check the log output above for errors"
    echo -e "  - Ensure your display server (X11/Wayland) is running"
    echo -e "  - Try running with: ${BOLD}KIVY_LOG_LEVEL=debug python3 network_designer.py${NC}"
    echo ""
}

# Handle script arguments
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --test         Run test after installation"
    echo "  --no-python    Skip Python package installation"
    echo "  --force        Force installation even if already installed"
    echo ""
    exit 0
fi

# Run main function
main

# Run test if requested
if [[ "$1" == "--test" ]] || [[ "$2" == "--test" ]]; then
    echo ""
    echo -e "${BLUE}Running Kivy test...${NC}"
    $PYTHON_CMD test_kivy.py
fi
