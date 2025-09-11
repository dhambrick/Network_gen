#!/usr/bin/env python3
"""
Data models for Network Designer application
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class DeviceType(Enum):
    """Types of network devices"""
    COMPUTER = "computer"
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    DATABASE = "database"
    LOADBALANCER = "loadbalancer"


class OSType(Enum):
    """Container OS/Image types"""
    UBUNTU = "ubuntu:22.04"
    ALPINE = "alpine:latest"
    DEBIAN = "debian:11"
    CENTOS = "centos:8"
    NGINX = "nginx:latest"
    REDIS = "redis:latest"
    POSTGRES = "postgres:14"
    MYSQL = "mysql:8"
    MONGODB = "mongodb:5"
    CUSTOM = "custom"


@dataclass
class NetworkInterface:
    """Network interface configuration"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "eth0"
    ip_address: str = ""
    subnet_mask: str = "255.255.255.0"
    cidr: int = 24
    gateway: str = ""
    dns: List[str] = field(default_factory=list)
    mac_address: str = ""
    connected_to: Optional[str] = None
    vlan_id: Optional[int] = None
    is_primary: bool = False
    
    def get_network_address(self) -> str:
        """Calculate network address from IP and subnet"""
        if not self.ip_address:
            return ""
        
        try:
            ip_parts = [int(x) for x in self.ip_address.split('.')]
            mask_parts = [int(x) for x in self.subnet_mask.split('.')]
            network = [str(ip_parts[i] & mask_parts[i]) for i in range(4)]
            return '.'.join(network)
        except:
            return ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "cidr": self.cidr,
            "gateway": self.gateway,
            "dns": self.dns,
            "mac_address": self.mac_address,
            "connected_to": self.connected_to,
            "vlan_id": self.vlan_id,
            "is_primary": self.is_primary
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkInterface':
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "eth0"),
            ip_address=data.get("ip_address", ""),
            subnet_mask=data.get("subnet_mask", "255.255.255.0"),
            cidr=data.get("cidr", 24),
            gateway=data.get("gateway", ""),
            dns=data.get("dns", []),
            mac_address=data.get("mac_address", ""),
            connected_to=data.get("connected_to"),
            vlan_id=data.get("vlan_id"),
            is_primary=data.get("is_primary", False)
        )


@dataclass
class ComputerConfig:
    """Configuration for computer/container devices"""
    cpu_limit: float = 1.0  # CPU cores
    memory_limit: str = "512m"  # Memory limit
    storage_volume: str = ""  # Volume mount
    os: OSType = OSType.ALPINE
    custom_image: str = ""  # For custom Docker images
    environment_vars: Dict[str, str] = field(default_factory=dict)
    ports: List[str] = field(default_factory=list)  # Port mappings
    interfaces: List[NetworkInterface] = field(default_factory=list)
    command: str = ""  # Container command
    entrypoint: str = ""  # Container entrypoint
    restart_policy: str = "unless-stopped"
    labels: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    privileged: bool = False
    
    def __post_init__(self):
        """Initialize with default interface if none provided"""
        if not self.interfaces:
            self.interfaces = [NetworkInterface(name="eth0", is_primary=True)]
    
    def add_interface(self, interface: NetworkInterface) -> None:
        """Add a network interface"""
        # Set as primary if it's the first interface
        if not self.interfaces:
            interface.is_primary = True
        self.interfaces.append(interface)
    
    def remove_interface(self, interface_id: str) -> bool:
        """Remove a network interface by ID"""
        for i, iface in enumerate(self.interfaces):
            if iface.id == interface_id:
                self.interfaces.pop(i)
                # Set new primary if needed
                if iface.is_primary and self.interfaces:
                    self.interfaces[0].is_primary = True
                return True
        return False
    
    def get_primary_interface(self) -> Optional[NetworkInterface]:
        """Get the primary network interface"""
        for iface in self.interfaces:
            if iface.is_primary:
                return iface
        return self.interfaces[0] if self.interfaces else None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
            "storage_volume": self.storage_volume,
            "os": self.os.value,
            "custom_image": self.custom_image,
            "environment_vars": self.environment_vars,
            "ports": self.ports,
            "interfaces": [iface.to_dict() for iface in self.interfaces],
            "command": self.command,
            "entrypoint": self.entrypoint,
            "restart_policy": self.restart_policy,
            "labels": self.labels,
            "capabilities": self.capabilities,
            "privileged": self.privileged
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComputerConfig':
        """Create from dictionary"""
        config = cls(
            cpu_limit=data.get("cpu_limit", 1.0),
            memory_limit=data.get("memory_limit", "512m"),
            storage_volume=data.get("storage_volume", ""),
            os=OSType(data.get("os", OSType.ALPINE.value)),
            custom_image=data.get("custom_image", ""),
            environment_vars=data.get("environment_vars", {}),
            ports=data.get("ports", []),
            interfaces=[],
            command=data.get("command", ""),
            entrypoint=data.get("entrypoint", ""),
            restart_policy=data.get("restart_policy", "unless-stopped"),
            labels=data.get("labels", {}),
            capabilities=data.get("capabilities", []),
            privileged=data.get("privileged", False)
        )
        
        # Load interfaces
        for iface_data in data.get("interfaces", []):
            config.interfaces.append(NetworkInterface.from_dict(iface_data))
        
        return config


@dataclass
class NetworkDevice:
    """Network device representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: DeviceType = DeviceType.COMPUTER
    name: str = ""
    x: float = 0
    y: float = 0
    config: Optional[ComputerConfig] = None
    connections: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=lambda: ["default"])
    
    def __post_init__(self):
        """Initialize device configuration"""
        if self.config is None and self.type in [DeviceType.COMPUTER, DeviceType.DATABASE]:
            self.config = ComputerConfig()
    
    def add_connection(self, device_id: str) -> None:
        """Add a connection to another device"""
        if device_id not in self.connections:
            self.connections.append(device_id)
    
    def remove_connection(self, device_id: str) -> bool:
        """Remove a connection to another device"""
        if device_id in self.connections:
            self.connections.remove(device_id)
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "config": self.config.to_dict() if self.config else None,
            "connections": self.connections,
            "networks": self.networks
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkDevice':
        """Create from dictionary"""
        device = cls(
            id=data.get("id", str(uuid.uuid4())),
            type=DeviceType(data.get("type", DeviceType.COMPUTER.value)),
            name=data.get("name", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            config=None,
            connections=data.get("connections", []),
            networks=data.get("networks", ["default"])
        )
        
        # Load config if present
        if data.get("config"):
            device.config = ComputerConfig.from_dict(data["config"])
        
        return device


@dataclass
class Connection:
    """Connection between network devices"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    source_interface_id: Optional[str] = None
    target_interface_id: Optional[str] = None
    network_name: str = "default"
    bandwidth: Optional[str] = None  # e.g., "1Gbps"
    latency: Optional[str] = None    # e.g., "10ms"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_interface_id": self.source_interface_id,
            "target_interface_id": self.target_interface_id,
            "network_name": self.network_name,
            "bandwidth": self.bandwidth,
            "latency": self.latency
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Connection':
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            source_interface_id=data.get("source_interface_id"),
            target_interface_id=data.get("target_interface_id"),
            network_name=data.get("network_name", "default"),
            bandwidth=data.get("bandwidth"),
            latency=data.get("latency")
        )


@dataclass
class NetworkProject:
    """Complete network project"""
    name: str = "Untitled Project"
    description: str = ""
    version: str = "1.0.0"
    created_at: str = ""
    modified_at: str = ""
    devices: Dict[str, NetworkDevice] = field(default_factory=dict)
    connections: Dict[str, Connection] = field(default_factory=dict)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def add_device(self, device: NetworkDevice) -> None:
        """Add a device to the project"""
        self.devices[device.id] = device
    
    def remove_device(self, device_id: str) -> bool:
        """Remove a device and its connections"""
        if device_id in self.devices:
            # Remove connections
            conns_to_remove = []
            for conn_id, conn in self.connections.items():
                if conn.source_id == device_id or conn.target_id == device_id:
                    conns_to_remove.append(conn_id)
            
            for conn_id in conns_to_remove:
                del self.connections[conn_id]
            
            # Remove device
            del self.devices[device_id]
            return True
        return False
    
    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the project"""
        self.connections[connection.id] = connection
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "devices": {k: v.to_dict() for k, v in self.devices.items()},
            "connections": {k: v.to_dict() for k, v in self.connections.items()},
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkProject':
        """Create from dictionary"""
        project = cls(
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            devices={},
            connections={},
            metadata=data.get("metadata", {})
        )
        
        # Load devices
        for dev_id, dev_data in data.get("devices", {}).items():
            project.devices[dev_id] = NetworkDevice.from_dict(dev_data)
        
        # Load connections
        for conn_id, conn_data in data.get("connections", {}).items():
            project.connections[conn_id] = Connection.from_dict(conn_data)
        
        return project