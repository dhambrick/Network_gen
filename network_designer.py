#!/usr/bin/env python3
"""
Network Designer - Modern Network Topology Designer
Visual network design tool with Docker/Terraform export capabilities

Author: Network Designer Team
Version: 2.0.0
License: MIT
"""

import sys
import os
from pathlib import Path

# Add the application directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import and run the main application
from app import main

if __name__ == "__main__":
    main()
