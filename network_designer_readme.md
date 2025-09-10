# Network Designer - Visual Network to Docker/Terraform Converter

## Overview

Network Designer is a modern Python application with a Kivy-based graphical interface for designing computer network topologies and automatically generating Docker and Terraform configurations. The application features an intuitive drag-and-drop interface with distinct visual icons for each network component, easy connection management, and comprehensive device configuration options.

## Features

### Core Functionality
- **Modern Kivy UI**: Beautiful, responsive interface with distinct icons for each device type
- **Visual Network Design**: Intuitive drag-and-drop interface for creating network topologies
- **Device Types**: 
  - 🖥️ **Computer**: Containers with full configuration
  - 🔀 **Router**: Network routing and gateway functions
  - 🔌 **Switch**: Network switching and segmentation
  - 🛡️ **Firewall**: Security boundaries
  - 🗄️ **Database**: Database servers
  - ⚖️ **Load Balancer**: Traffic distribution
- **Easy Connection Management**: Click-to-connect mode with visual feedback
- **Docker/Terraform Export**: Generate Docker Compose and Terraform configurations
- **SVG Export**: Export network diagrams as scalable vector graphics
- **Project Management**: Save and load network designs as JSON files

### Device Configuration
- **Container Settings**:
  - Docker image selection (Ubuntu, Alpine, Debian, CentOS, Nginx, Redis, PostgreSQL, MySQL, MongoDB)
  - CPU limits (0.25 - 4 cores)
  - Memory limits (configurable)
  - Port mappings
  - Environment variables
  - Volume mounts
  - Custom commands
  - Restart policies
  
- **Network Configuration**:
  - Multiple network interfaces
  - IP address assignment
  - Docker network assignment
  - Inter-container connectivity

### User Interface
- **Canvas**: Interactive drawing area with visual device representations
- **Tool Panel**: Device palette with clear icons
- **Properties Panel**: Real-time device configuration
- **Connection Mode**: Easy click-to-connect functionality
- **Status Bar**: Real-time operation feedback

## Installation

### Prerequisites
- Python 3.7 or higher
- uv package manager
- Kivy dependencies (SDL2, GStreamer)

### Quick Setup with uv

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository and run deployment:
```bash
git clone <repository-url>
cd network-designer
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:
- Install uv if needed
- Check Python version
- Install Kivy system dependencies
- Create virtual environment
- Install all Python packages
- Create run scripts

### Manual Installation

1. **Install System Dependencies**:

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    gstreamer1.0-plugins-base
```

macOS:
```bash
brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
```

2. **Install Python packages with uv**:
```bash
uv venv
uv pip install kivy kivymd
```

3. **Run the application**:
```bash
uv run python network_designer.py
```

## Usage Guide

### Creating a Network Topology

1. **Adding Devices**:
   - Click on a device button in the left panel (Computer, Router, Switch, etc.)
   - Click on the canvas to place the device
   - Each device has a distinct visual icon for easy identification

2. **Connecting Devices**:
   - Click the "Connect" button to enter connection mode
   - Click on the first device (connection points will be highlighted)
   - Click on the second device to create a connection
   - Connections are drawn with smooth lines between devices

3. **Configuring Devices**:
   - Click "Select" mode
   - Click on any device to select it
   - Use the Properties panel on the right to configure:
     - Container image
     - Resource limits (CPU, memory)
     - Port mappings
     - Environment variables
     - Network settings
   - Double-click for advanced settings

4. **Managing the Canvas**:
   - Drag devices to reposition them
   - Use "Delete Selected" to remove devices
   - "Clear Canvas" to start fresh

### Exporting Configurations

#### Docker Compose Export:
1. Click "Export Terraform" button
2. Choose location and filename
3. Two files are generated:
   - `docker-compose.yml` - Docker Compose configuration
   - `docker-compose.tf` - Terraform configuration for Docker provider

#### SVG Export:
1. Click "Export SVG" button
2. Choose location and filename
3. Creates a scalable vector graphic of your network diagram

### Docker Deployment

The generated Docker configurations include:

#### Docker Compose Features:
- Service definitions for each container
- Network configurations
- Resource limits
- Environment variables
- Port mappings
- Volume mounts
- Restart policies

#### Terraform Docker Provider:
```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

resource "docker_network" "network_name" {
  name   = "network_name"
  driver = "bridge"
}

resource "docker_container" "container_name" {
  name  = "container_name"
  image = "ubuntu:22.04"
  
  networks_advanced {
    name = docker_network.network_name.name
  }
  
  ports {
    internal = 80
    external = 8080
  }
  
  env = [
    "ENV_VAR=value"
  ]
  
  restart = "unless-stopped"
}
```

### Deployment Commands

Deploy with Docker Compose:
```bash
docker-compose up -d
```

Deploy with Terraform:
```bash
terraform init
terraform plan
terraform apply
```

## Visual Design Elements

### Device Icons
Each device type has a unique visual representation:
- **Computer**: Rectangular monitor with base
- **Router**: Diamond shape with antennas
- **Switch**: Rectangular box with port indicators
- **Firewall**: Shield shape
- **Database**: Cylinder shape
- **Load Balancer**: Circle with arrow indicators

### Connection Points
- Devices have four connection points (top, bottom, left, right)
- Connection points are highlighted when in connect mode
- Connections automatically route to the nearest points

## Example Configurations

### Web Application Stack
1. Add Load Balancer
2. Add 2-3 Web Servers (Nginx containers)
3. Add Application Server (Node.js or Python container)
4. Add Database (PostgreSQL or MySQL)
5. Connect Load Balancer → Web Servers → App Server → Database
6. Configure ports and environment variables
7. Export and deploy

### Microservices Architecture
1. Add API Gateway (Router)
2. Add multiple service containers
3. Add message queue (Redis)
4. Add databases for each service
5. Connect components
6. Set up Docker networks for isolation
7. Export and deploy

## Keyboard Shortcuts

- **Delete**: Remove selected device
- **Escape**: Cancel current operation
- **Ctrl+S**: Save project
- **Ctrl+O**: Open project
- **Ctrl+E**: Export to Docker/Terraform

## Project File Format

Projects are saved as JSON with the following structure:
```json
{
  "devices": {
    "device_id": {
      "type": "computer",
      "name": "web_server",
      "x": 100,
      "y": 200,
      "network": "frontend",
      "config": {
        "os": "nginx:latest",
        "cpu_limit": 1.0,
        "memory_limit": "512m",
        "ports": ["80:80"],
        "environment_vars": {
          "NODE_ENV": "production"
        }
      }
    }
  },
  "connections": {
    "connection_id": {
      "source_id": "device_id1",
      "target_id": "device_id2",
      "network_name": "frontend"
    }
  }
}
```

## Terraform Deployment

### Prerequisites for Deployment

1. Install Terraform:
```bash
# macOS
brew install terraform

# Linux
sudo apt-get update && sudo apt-get install terraform

# Windows
# Download from https://www.terraform.io/downloads
```

2. Configure AWS credentials:
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### Deploying the Infrastructure

1. Navigate to the directory with your exported .tf file:
```bash
cd /path/to/terraform/file
```

2. Initialize Terraform:
```bash
terraform init
```

3. Review the plan:
```bash
terraform plan
```

4. Apply the configuration:
```bash
terraform apply
# Type 'yes' when prompted
```

5. To destroy the infrastructure:
```bash
terraform destroy
# Type 'yes' when prompted
```

## Keyboard Shortcuts

- **Delete**: Delete key removes selected device
- **Escape**: Cancel current operation
- **Ctrl+S**: Save project (when implemented)
- **Ctrl+O**: Open project (when implemented)
- **Ctrl+E**: Export to Terraform (when implemented)

## Design Patterns and Best Practices

### Network Design Tips

1. **Hierarchical Layout**: Place routers at the top, switches in the middle, and computers at the bottom
2. **Logical Grouping**: Keep related devices close together
3. **Clear Naming**: Use descriptive names for devices (e.g., web_server_1, database_server)
4. **IP Planning**: Plan your IP addressing scheme before configuring interfaces

### Terraform Considerations

1. **Instance Sizing**: The application maps device configurations to appropriate AWS instance types
2. **Region Selection**: Default region is us-west-2; modify in the .tf file if needed
3. **Security Groups**: Review and adjust security group rules for production use
4. **Costs**: Be aware of AWS costs associated with deployed resources

## Troubleshooting

### Common Issues

1. **Canvas not responding**:
   - Ensure you've selected the appropriate mode (Select/Connect/Delete)
   - Check the status bar for current operation state

2. **Connections not visible**:
   - Connections are drawn behind devices
   - Ensure both devices exist before connecting

3. **Terraform export fails**:
   - Ensure at least one device exists on the canvas
   - Check file write permissions

4. **Device properties not saving**:
   - Click "Update" button after changing text fields
   - Spinbox values save automatically

## Architecture

### Application Structure

```
network_designer.py
├── Data Models
│   ├── DeviceType (Enum)
│   ├── OSType (Enum)
│   ├── NetworkInterface (dataclass)
│   ├── ComputerConfig (dataclass)
│   ├── NetworkDevice (dataclass)
│   └── Connection (dataclass)
├── NetworkDesignerApp (Main Class)
│   ├── UI Components
│   │   ├── Menu Bar
│   │   ├── Tool Panel
│   │   ├── Canvas
│   │   └── Properties Panel
│   ├── Device Management
│   │   ├── add_device()
│   │   ├── delete_device()
│   │   └── edit_device()
│   ├── Connection Management
│   │   ├── add_connection()
│   │   └── delete_connection()
│   ├── File Operations
│   │   ├── save_project()
│   │   └── load_project()
│   └── Export Functions
│       └── export_terraform()
└── main()
```

### Data Persistence

Projects are saved as JSON with the following structure:
```json
{
  "devices": {
    "device_id": {
      "id": "uuid",
      "type": "computer|router|switch",
      "name": "device_name",
      "x": 100,
      "y": 200,
      "connections": ["device_id2"],
      "config": {
        "cpu_cores": 2,
        "memory_gb": 4,
        "storage_gb": 20,
        "os": "ubuntu-22.04",
        "interfaces": [...]
      }
    }
  },
  "connections": {
    "connection_id": {
      "id": "uuid",
      "source_id": "device_id1",
      "target_id": "device_id2"
    }
  }
}
```

## Future Enhancements

Potential improvements for future versions:

1. **Additional Cloud Providers**: Support for Azure, GCP, OpenStack
2. **Advanced Networking**: VLANs, NAT, Firewall rules
3. **Import Functionality**: Import existing Terraform configurations
4. **Validation**: Network connectivity and configuration validation
5. **Templates**: Pre-built network topology templates
6. **Export Formats**: Support for Ansible, CloudFormation
7. **Simulation**: Basic network traffic simulation
8. **Cost Estimation**: AWS cost estimates for the configuration

## License

This software is provided as-is for educational and development purposes. Modify and distribute as needed for your use case.

## Support

For issues, questions, or contributions:
1. Check the Troubleshooting section
2. Review the Usage Guide
3. Examine the generated Terraform files for AWS-specific issues

## Version History

- **v1.0.0**: Initial release
  - Core network designer functionality
  - Support for computers, routers, and switches
  - Terraform export for AWS
  - Project save/load capability