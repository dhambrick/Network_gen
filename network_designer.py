#!/usr/bin/env python3
"""
Network Designer - Visual Network Topology to Terraform Converter
A Kivy-based GUI application for designing network topologies with Docker deployment
"""

import json
import uuid
import math
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from pathlib import Path

# Kivy configuration - must be before other kivy imports
os.environ['KIVY_NO_ARGS'] = '1'  # Prevent Kivy from parsing command line arguments

# Kivy imports
import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.config import Config

# Configure Kivy settings
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'minimum_width', '1200')
Config.set('graphics', 'minimum_height', '700')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Line, Color, Rectangle, Ellipse, RoundedRectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.uix.behaviors import DragBehavior
from kivy.vector import Vector

# SVG export support
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Data Models
class DeviceType(Enum):
    COMPUTER = "computer"
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    DATABASE = "database"
    LOADBALANCER = "loadbalancer"

class OSType(Enum):
    UBUNTU = "ubuntu:22.04"
    ALPINE = "alpine:latest"
    DEBIAN = "debian:11"
    CENTOS = "centos:8"
    NGINX = "nginx:latest"
    REDIS = "redis:latest"
    POSTGRES = "postgres:14"
    MYSQL = "mysql:8"
    MONGODB = "mongodb:5"

@dataclass
class NetworkInterface:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "eth0"
    ip_address: str = ""
    subnet: str = "24"
    connected_to: Optional[str] = None

@dataclass
class ComputerConfig:
    cpu_limit: float = 1.0  # CPU cores
    memory_limit: str = "512m"  # Memory limit
    storage_volume: str = ""  # Volume mount
    os: OSType = OSType.ALPINE
    environment_vars: Dict[str, str] = field(default_factory=dict)
    ports: List[str] = field(default_factory=list)  # Port mappings
    interfaces: List[NetworkInterface] = field(default_factory=list)
    command: str = ""  # Container command
    restart_policy: str = "unless-stopped"

@dataclass
class NetworkDevice:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: DeviceType = DeviceType.COMPUTER
    name: str = ""
    x: float = 0
    y: float = 0
    config: Optional[ComputerConfig] = None
    connections: List[str] = field(default_factory=list)
    network: str = "default"  # Docker network

    def __post_init__(self):
        if self.config is None:
            self.config = ComputerConfig()
            self.config.interfaces = [NetworkInterface()]

@dataclass
class Connection:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    network_name: str = "default"


# Custom Kivy Widgets
class NetworkDeviceWidget(Widget):
    """Network device widget with visual representation"""
    
    device_id = StringProperty("")
    device_type = StringProperty("")
    device_name = StringProperty("")
    selected = BooleanProperty(False)
    
    def __init__(self, device: NetworkDevice, canvas_widget, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.canvas_widget = canvas_widget
        self.device_id = device.id
        self.device_type = device.type.value
        self.device_name = device.name
        self.size = (80, 100)
        self.size_hint = (None, None)
        self.pos = (device.x, device.y)
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # Bind to position changes
        self.bind(pos=self.on_pos_change)
        self.bind(selected=self.on_selection_change)
        
        # Draw the device
        Clock.schedule_once(lambda dt: self.draw_device(), 0)
    
    def on_pos_change(self, instance, value):
        """Update device position when widget moves"""
        self.device.x = self.x
        self.device.y = self.y
        if hasattr(self.canvas_widget, 'update_connections'):
            self.canvas_widget.update_connections()
    
    def on_selection_change(self, instance, value):
        """Redraw when selection changes"""
        self.draw_device()
    
    def draw_device(self):
        """Draw device icon and label"""
        self.canvas.clear()
        
        with self.canvas:
            # Selection highlight
            if self.selected:
                Color(0.2, 0.6, 1, 0.3)
                RoundedRectangle(
                    pos=(self.x - 5, self.y - 5),
                    size=(self.width + 10, self.height + 10),
                    radius=[(10, 10)]
                )
            
            # Device icon background
            icon_color = self.get_device_color()
            Color(*icon_color)
            
            # Draw device-specific shape
            if self.device.type == DeviceType.COMPUTER:
                # Computer - rectangular monitor
                Rectangle(pos=(self.x + 15, self.y + 30), size=(50, 35))
                Color(0.3, 0.3, 0.3, 1)
                Rectangle(pos=(self.x + 30, self.y + 20), size=(20, 10))
                
            elif self.device.type == DeviceType.ROUTER:
                # Router - triangle/diamond shape
                Color(*icon_color)
                # Draw as triangle using lines
                Line(points=[
                    self.x + 40, self.y + 20,  # bottom
                    self.x + 60, self.y + 45,  # right
                    self.x + 40, self.y + 70,  # top
                    self.x + 20, self.y + 45,  # left
                    self.x + 40, self.y + 20   # back to bottom
                ], width=2, close=True)
                
            elif self.device.type == DeviceType.SWITCH:
                # Switch - rectangular box
                Rectangle(pos=(self.x + 10, self.y + 30), size=(60, 30))
                Color(0.2, 0.2, 0.2, 1)
                # Port indicators
                for i in range(4):
                    Rectangle(pos=(self.x + 15 + i*13, self.y + 35), size=(8, 5))
                    Rectangle(pos=(self.x + 15 + i*13, self.y + 50), size=(8, 5))
                    
            elif self.device.type == DeviceType.FIREWALL:
                # Firewall - shield shape using lines
                Color(*icon_color)
                Line(points=[
                    self.x + 40, self.y + 15,  # bottom point
                    self.x + 55, self.y + 35,  # right mid
                    self.x + 55, self.y + 55,  # right top
                    self.x + 40, self.y + 65,  # top center
                    self.x + 25, self.y + 55,  # left top
                    self.x + 25, self.y + 35,  # left mid
                    self.x + 40, self.y + 15   # back to bottom
                ], width=2, close=True)
                
            elif self.device.type == DeviceType.DATABASE:
                # Database - cylinder shape
                Color(*icon_color)
                Ellipse(pos=(self.x + 20, self.y + 50), size=(40, 15))
                Rectangle(pos=(self.x + 20, self.y + 30), size=(40, 25))
                Ellipse(pos=(self.x + 20, self.y + 25), size=(40, 15))
                
            elif self.device.type == DeviceType.LOADBALANCER:
                # Load Balancer - circle
                Color(*icon_color)
                Ellipse(pos=(self.x + 20, self.y + 25), size=(40, 40))
    
    def get_device_color(self):
        """Get color based on device type"""
        colors = {
            DeviceType.COMPUTER: (0.3, 0.5, 0.8, 1),      # Blue
            DeviceType.ROUTER: (0.3, 0.7, 0.4, 1),        # Green
            DeviceType.SWITCH: (0.7, 0.7, 0.3, 1),        # Yellow
            DeviceType.FIREWALL: (0.8, 0.3, 0.3, 1),      # Red
            DeviceType.DATABASE: (0.6, 0.4, 0.7, 1),      # Purple
            DeviceType.LOADBALANCER: (0.4, 0.7, 0.7, 1)   # Cyan
        }
        return colors.get(self.device.type, (0.5, 0.5, 0.5, 1))
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.canvas_widget.edit_device(self.device)
                return True
            else:
                # Start dragging
                self.dragging = True
                self.drag_offset = (touch.x - self.x, touch.y - self.y)
                self.canvas_widget.select_device(self)
                return True
        return False
    
    def on_touch_move(self, touch):
        if self.dragging:
            # Update position while dragging
            self.x = touch.x - self.drag_offset[0]
            self.y = touch.y - self.drag_offset[1]
            return True
        return False
    
    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            return True
        return False


class NetworkCanvas(FloatLayout):
    """Main canvas for network diagram"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.devices = {}
        self.connections = {}
        self.device_widgets = {}
        self.selected_device = None
        self.connection_mode = False
        self.connection_start = None
        
        # Background
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Bind size changes
        self.bind(size=self.update_bg, pos=self.update_bg)
    
    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def add_device(self, device_type: DeviceType, x: float, y: float):
        """Add a new device to the canvas"""
        # Ensure position is within canvas bounds
        x = max(50, min(x, self.width - 100))
        y = max(50, min(y, self.height - 100))
        
        device = NetworkDevice(type=device_type, x=x, y=y)
        device.name = f"{device_type.value}_{len([d for d in self.devices.values() if d.type == device_type]) + 1}"
        
        self.devices[device.id] = device
        
        # Create widget
        widget = NetworkDeviceWidget(device, self)
        self.device_widgets[device.id] = widget
        self.add_widget(widget)
        
        return device
    
    def select_device(self, widget):
        """Select a device widget"""
        # Deselect previous
        if self.selected_device:
            self.selected_device.selected = False
        
        # Select new
        self.selected_device = widget
        widget.selected = True
        
        # Update properties panel
        if hasattr(self.app_instance, 'show_device_properties'):
            self.app_instance.show_device_properties(widget.device)
        
        # Handle connection mode
        if self.connection_mode:
            if self.connection_start is None:
                self.connection_start = widget
                if hasattr(self.app_instance, 'status_label'):
                    self.app_instance.status_label.text = f"Connection started from {widget.device_name}"
            elif widget != self.connection_start:
                self.create_connection(self.connection_start, widget)
                self.connection_start = None
                self.connection_mode = False
                if hasattr(self.app_instance, 'status_label'):
                    self.app_instance.status_label.text = "Connection created"
    
    def create_connection(self, source_widget, target_widget):
        """Create a connection between two devices"""
        conn = Connection(
            source_id=source_widget.device.id,
            target_id=target_widget.device.id
        )
        self.connections[conn.id] = conn
        
        # Update device connections
        source_widget.device.connections.append(target_widget.device.id)
        target_widget.device.connections.append(source_widget.device.id)
        
        self.draw_connections()
    
    def draw_connections(self):
        """Draw all connections"""
        # Clear previous connection lines
        self.canvas.before.clear()
        
        # Redraw background
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            
            # Draw connections
            Color(0.2, 0.2, 0.2, 0.8)
            for conn in self.connections.values():
                if conn.source_id in self.device_widgets and conn.target_id in self.device_widgets:
                    source = self.device_widgets[conn.source_id]
                    target = self.device_widgets[conn.target_id]
                    
                    # Calculate center points
                    start_x = source.x + source.width / 2
                    start_y = source.y + source.height / 2
                    end_x = target.x + target.width / 2
                    end_y = target.y + target.height / 2
                    
                    # Draw line
                    Line(points=[start_x, start_y, end_x, end_y], width=2)
    
    def update_connections(self):
        """Update connection drawings when devices move"""
        self.draw_connections()
    
    def edit_device(self, device):
        """Open device edit popup"""
        if hasattr(self.app_instance, 'open_device_editor'):
            self.app_instance.open_device_editor(device)
    
    def delete_selected(self):
        """Delete selected device and its connections"""
        if self.selected_device:
            device_id = self.selected_device.device.id
            
            # Remove connections
            conns_to_delete = []
            for conn_id, conn in self.connections.items():
                if conn.source_id == device_id or conn.target_id == device_id:
                    conns_to_delete.append(conn_id)
            
            for conn_id in conns_to_delete:
                del self.connections[conn_id]
            
            # Remove from other devices' connection lists
            for other_device in self.devices.values():
                if device_id in other_device.connections:
                    other_device.connections.remove(device_id)
            
            # Remove widget
            self.remove_widget(self.selected_device)
            del self.devices[device_id]
            del self.device_widgets[device_id]
            
            self.selected_device = None
            self.draw_connections()
    
    def clear_canvas(self):
        """Clear all devices and connections"""
        for widget in list(self.device_widgets.values()):
            self.remove_widget(widget)
        
        self.devices.clear()
        self.connections.clear()
        self.device_widgets.clear()
        self.selected_device = None
        self.draw_connections()
    
    def on_touch_down(self, touch):
        """Handle touch/click events"""
        # Check if we're placing a new device
        if hasattr(self.app_instance, 'placing_device_type'):
            device_type = self.app_instance.placing_device_type
            self.add_device(device_type, touch.x, touch.y)
            delattr(self.app_instance, 'placing_device_type')
            if hasattr(self.app_instance, 'status_label'):
                self.app_instance.status_label.text = f"Added {device_type.value}"
            return True
        
        # Let children handle the event first
        return super().on_touch_down(touch)
    
    def export_to_svg(self, filename):
        """Export the network diagram to SVG"""
        # Create SVG root
        svg = ET.Element('svg', {
            'width': str(int(self.width)),
            'height': str(int(self.height)),
            'xmlns': 'http://www.w3.org/2000/svg',
            'viewBox': f'0 0 {int(self.width)} {int(self.height)}'
        })
        
        # Add white background
        ET.SubElement(svg, 'rect', {
            'width': str(int(self.width)),
            'height': str(int(self.height)),
            'fill': 'white'
        })
        
        # Draw connections
        connections_group = ET.SubElement(svg, 'g', {'id': 'connections'})
        for conn in self.connections.values():
            if conn.source_id in self.device_widgets and conn.target_id in self.device_widgets:
                source = self.device_widgets[conn.source_id]
                target = self.device_widgets[conn.target_id]
                
                ET.SubElement(connections_group, 'line', {
                    'x1': str(int(source.x + source.width/2)),
                    'y1': str(int(self.height - (source.y + source.height/2))),
                    'x2': str(int(target.x + target.width/2)),
                    'y2': str(int(self.height - (target.y + target.height/2))),
                    'stroke': '#333333',
                    'stroke-width': '2'
                })
        
        # Draw devices
        devices_group = ET.SubElement(svg, 'g', {'id': 'devices'})
        for device_id, widget in self.device_widgets.items():
            device = widget.device
            color = '#{:02x}{:02x}{:02x}'.format(
                int(widget.get_device_color()[0] * 255),
                int(widget.get_device_color()[1] * 255),
                int(widget.get_device_color()[2] * 255)
            )
            
            # Device group
            device_g = ET.SubElement(devices_group, 'g', {'id': f'device_{device_id}'})
            
            # Device shape
            ET.SubElement(device_g, 'rect', {
                'x': str(int(widget.x + 10)),
                'y': str(int(self.height - (widget.y + 70))),
                'width': '60',
                'height': '40',
                'fill': color,
                'stroke': 'black',
                'stroke-width': '1',
                'rx': '5'
            })
            
            # Device label
            ET.SubElement(device_g, 'text', {
                'x': str(int(widget.x + 40)),
                'y': str(int(self.height - (widget.y - 10))),
                'text-anchor': 'middle',
                'font-family': 'Arial',
                'font-size': '12',
                'fill': 'black'
            }).text = device.name
        
        # Write to file
        tree = ET.ElementTree(svg)
        tree.write(filename, encoding='utf-8', xml_declaration=True)


class NetworkDesignerApp(App):
    """Main application class"""
    
    def build(self):
        self.title = "Network Designer - Docker Edition"
        
        # Main layout
        main_layout = BoxLayout(orientation='horizontal')
        
        # Left panel - Tools
        left_panel = BoxLayout(orientation='vertical', size_hint=(0.15, 1))
        left_panel.add_widget(Label(text='Network Elements', size_hint=(1, 0.05)))
        
        # Device buttons
        devices_grid = GridLayout(cols=1, spacing=5, padding=5, size_hint=(1, 0.6))
        
        device_buttons = [
            ("Computer", DeviceType.COMPUTER),
            ("Router", DeviceType.ROUTER),
            ("Switch", DeviceType.SWITCH),
            ("Firewall", DeviceType.FIREWALL),
            ("Database", DeviceType.DATABASE),
            ("Load Balancer", DeviceType.LOADBALANCER)
        ]
        
        for label, device_type in device_buttons:
            btn = Button(text=label, size_hint=(1, None), height=40)
            btn.bind(on_press=lambda x, dt=device_type: self.start_device_placement(dt))
            devices_grid.add_widget(btn)
        
        left_panel.add_widget(devices_grid)
        
        # Mode buttons
        left_panel.add_widget(Label(text='Mode', size_hint=(1, 0.05)))
        mode_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=5, padding=5)
        
        self.select_btn = Button(text='Select', size_hint=(1, None), height=35)
        self.select_btn.bind(on_press=self.set_select_mode)
        mode_layout.add_widget(self.select_btn)
        
        self.connect_btn = Button(text='Connect', size_hint=(1, None), height=35)
        self.connect_btn.bind(on_press=self.set_connect_mode)
        mode_layout.add_widget(self.connect_btn)
        
        self.delete_btn = Button(text='Delete Selected', size_hint=(1, None), height=35)
        self.delete_btn.bind(on_press=self.delete_selected)
        mode_layout.add_widget(self.delete_btn)
        
        left_panel.add_widget(mode_layout)
        
        # Action buttons
        actions_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.15), spacing=5, padding=5)
        
        clear_btn = Button(text='Clear Canvas', size_hint=(1, None), height=35)
        clear_btn.bind(on_press=self.clear_canvas)
        actions_layout.add_widget(clear_btn)
        
        export_tf_btn = Button(text='Export Terraform', size_hint=(1, None), height=35)
        export_tf_btn.bind(on_press=self.export_terraform)
        actions_layout.add_widget(export_tf_btn)
        
        export_svg_btn = Button(text='Export SVG', size_hint=(1, None), height=35)
        export_svg_btn.bind(on_press=self.export_svg)
        actions_layout.add_widget(export_svg_btn)
        
        left_panel.add_widget(actions_layout)
        
        # Center - Canvas
        center_layout = BoxLayout(orientation='vertical', size_hint=(0.65, 1))
        
        # Canvas header
        canvas_header = BoxLayout(size_hint=(1, 0.05), padding=5)
        canvas_header.add_widget(Label(text='Network Topology Canvas'))
        center_layout.add_widget(canvas_header)
        
        # Network canvas
        self.canvas_widget = NetworkCanvas(self, size_hint=(1, 0.9))
        center_layout.add_widget(self.canvas_widget)
        
        # Status bar
        self.status_label = Label(text='Ready', size_hint=(1, 0.05))
        center_layout.add_widget(self.status_label)
        
        # Right panel - Properties
        right_panel = BoxLayout(orientation='vertical', size_hint=(0.2, 1))
        right_panel.add_widget(Label(text='Properties', size_hint=(1, 0.05)))
        
        # Properties content in scroll view
        self.properties_scroll = ScrollView(size_hint=(1, 0.85))
        self.properties_content = BoxLayout(orientation='vertical', padding=10, spacing=5, size_hint_y=None)
        self.properties_content.bind(minimum_height=self.properties_content.setter('height'))
        self.properties_scroll.add_widget(self.properties_content)
        right_panel.add_widget(self.properties_scroll)
        
        # Project buttons
        project_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.1), padding=5, spacing=5)
        
        save_btn = Button(text='Save Project', size_hint=(1, None), height=30)
        save_btn.bind(on_press=self.save_project)
        project_layout.add_widget(save_btn)
        
        load_btn = Button(text='Load Project', size_hint=(1, None), height=30)
        load_btn.bind(on_press=self.load_project)
        project_layout.add_widget(load_btn)
        
        right_panel.add_widget(project_layout)
        
        # Add panels to main layout
        main_layout.add_widget(left_panel)
        main_layout.add_widget(center_layout)
        main_layout.add_widget(right_panel)
        
        return main_layout
    
    def start_device_placement(self, device_type):
        """Start device placement mode"""
        self.placing_device_type = device_type
        self.status_label.text = f"Click on canvas to place {device_type.value}"
    
    def set_select_mode(self, instance):
        """Set select mode"""
        self.canvas_widget.connection_mode = False
        self.canvas_widget.connection_start = None
        self.status_label.text = "Select mode - Click devices to select and drag"
    
    def set_connect_mode(self, instance):
        """Set connection mode"""
        self.canvas_widget.connection_mode = True
        self.canvas_widget.connection_start = None
        self.status_label.text = "Connect mode - Click two devices to connect"
    
    def delete_selected(self, instance):
        """Delete selected device"""
        self.canvas_widget.delete_selected()
        self.properties_content.clear_widgets()
        self.status_label.text = "Device deleted"
    
    def clear_canvas(self, instance):
        """Clear the canvas"""
        # Create confirmation popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Clear all devices and connections?'))
        
        buttons = BoxLayout(spacing=10, size_hint=(1, 0.4))
        yes_btn = Button(text='Yes')
        no_btn = Button(text='No')
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)
        
        popup = Popup(title='Confirm Clear', content=content, size_hint=(0.4, 0.3))
        
        yes_btn.bind(on_press=lambda x: self._do_clear_canvas(popup))
        no_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def _do_clear_canvas(self, popup):
        """Actually clear the canvas"""
        self.canvas_widget.clear_canvas()
        self.properties_content.clear_widgets()
        self.status_label.text = "Canvas cleared"
        popup.dismiss()
    
    def show_device_properties(self, device):
        """Show device properties in the properties panel"""
        self.properties_content.clear_widgets()
        
        # Device info header
        self.properties_content.add_widget(
            Label(text=f'Device: {device.name}', size_hint=(1, None), height=30)
        )
        self.properties_content.add_widget(
            Label(text=f'Type: {device.type.value}', size_hint=(1, None), height=25)
        )
        
        # Name edit
        name_layout = BoxLayout(size_hint=(1, None), height=35)
        name_layout.add_widget(Label(text='Name:', size_hint=(0.3, 1)))
        name_input = TextInput(text=device.name, size_hint=(0.7, 1), multiline=False)
        
        def update_name(instance, value):
            device.name = value
            # Update widget display
            if device.id in self.canvas_widget.device_widgets:
                widget = self.canvas_widget.device_widgets[device.id]
                widget.device_name = value
                widget.draw_device()
        
        name_input.bind(text=update_name)
        name_layout.add_widget(name_input)
        self.properties_content.add_widget(name_layout)
        
        # Docker network
        network_layout = BoxLayout(size_hint=(1, None), height=35)
        network_layout.add_widget(Label(text='Network:', size_hint=(0.3, 1)))
        network_input = TextInput(text=device.network, size_hint=(0.7, 1), multiline=False)
        network_input.bind(text=lambda instance, value: setattr(device, 'network', value))
        network_layout.add_widget(network_input)
        self.properties_content.add_widget(network_layout)
        
        if device.config:
            # Container image
            self.properties_content.add_widget(
                Label(text='Container Config', size_hint=(1, None), height=30)
            )
            
            os_layout = BoxLayout(size_hint=(1, None), height=35)
            os_layout.add_widget(Label(text='Image:', size_hint=(0.3, 1)))
            os_spinner = Spinner(
                text=device.config.os.value,
                values=[os.value for os in OSType],
                size_hint=(0.7, 1)
            )
            os_spinner.bind(text=lambda instance, value: setattr(device.config, 'os', 
                                                                OSType(value)))
            os_layout.add_widget(os_spinner)
            self.properties_content.add_widget(os_layout)
            
            # CPU limit
            cpu_layout = BoxLayout(size_hint=(1, None), height=35)
            cpu_layout.add_widget(Label(text='CPU:', size_hint=(0.3, 1)))
            cpu_slider = Slider(min=0.25, max=4, value=device.config.cpu_limit, step=0.25)
            cpu_label = Label(text=f'{device.config.cpu_limit:.2f}', size_hint=(0.2, 1))
            cpu_slider.bind(value=lambda instance, value: self._update_cpu(device, value, cpu_label))
            cpu_layout.add_widget(cpu_slider)
            cpu_layout.add_widget(cpu_label)
            self.properties_content.add_widget(cpu_layout)
            
            # Memory limit
            mem_layout = BoxLayout(size_hint=(1, None), height=35)
            mem_layout.add_widget(Label(text='Memory:', size_hint=(0.3, 1)))
            mem_input = TextInput(text=device.config.memory_limit, size_hint=(0.7, 1), 
                                multiline=False)
            mem_input.bind(text=lambda instance, value: setattr(device.config, 'memory_limit', value))
            mem_layout.add_widget(mem_input)
            self.properties_content.add_widget(mem_layout)
            
            # Ports
            ports_layout = BoxLayout(size_hint=(1, None), height=35)
            ports_layout.add_widget(Label(text='Ports:', size_hint=(0.3, 1)))
            ports_input = TextInput(
                text=','.join(device.config.ports),
                size_hint=(0.7, 1),
                multiline=False,
                hint_text='8080:80,3000:3000'
            )
            ports_input.bind(text=lambda instance, value: setattr(device.config, 'ports', 
                                                                 value.split(',') if value else []))
            ports_layout.add_widget(ports_input)
            self.properties_content.add_widget(ports_layout)
            
            # Edit button for advanced settings
            edit_btn = Button(text='Advanced Settings', size_hint=(1, None), height=35)
            edit_btn.bind(on_press=lambda x: self.open_device_editor(device))
            self.properties_content.add_widget(edit_btn)
    
    def _update_cpu(self, device, value, label):
        """Update CPU limit"""
        device.config.cpu_limit = value
        label.text = f'{value:.2f}'
    
    def open_device_editor(self, device):
        """Open advanced device editor popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Environment variables section
        content.add_widget(Label(text='Environment Variables', size_hint=(1, None), height=30))
        
        env_scroll = ScrollView(size_hint=(1, 0.3))
        env_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        env_layout.bind(minimum_height=env_layout.setter('height'))
        
        # Add existing environment variables
        env_inputs = []
        for key, value in device.config.environment_vars.items():
            row = BoxLayout(size_hint=(1, None), height=30)
            key_input = TextInput(text=key, hint_text='Variable name')
            value_input = TextInput(text=value, hint_text='Value')
            row.add_widget(key_input)
            row.add_widget(value_input)
            env_layout.add_widget(row)
            env_inputs.append((key_input, value_input))
        
        # Add empty row for new variable
        row = BoxLayout(size_hint=(1, None), height=30)
        key_input = TextInput(hint_text='New variable name')
        value_input = TextInput(hint_text='New value')
        row.add_widget(key_input)
        row.add_widget(value_input)
        env_layout.add_widget(row)
        env_inputs.append((key_input, value_input))
        
        env_scroll.add_widget(env_layout)
        content.add_widget(env_scroll)
        
        # Additional settings
        content.add_widget(Label(text='Additional Settings', size_hint=(1, None), height=30))
        
        # Volume
        vol_layout = BoxLayout(size_hint=(1, None), height=35)
        vol_layout.add_widget(Label(text='Volume:', size_hint=(0.3, 1)))
        vol_input = TextInput(text=device.config.storage_volume, size_hint=(0.7, 1),
                            multiline=False, hint_text='./data:/data')
        vol_layout.add_widget(vol_input)
        content.add_widget(vol_layout)
        
        # Command
        cmd_layout = BoxLayout(size_hint=(1, None), height=35)
        cmd_layout.add_widget(Label(text='Command:', size_hint=(0.3, 1)))
        cmd_input = TextInput(text=device.config.command, size_hint=(0.7, 1),
                            multiline=False)
        cmd_layout.add_widget(cmd_input)
        content.add_widget(cmd_layout)
        
        # Restart policy
        restart_layout = BoxLayout(size_hint=(1, None), height=35)
        restart_layout.add_widget(Label(text='Restart:', size_hint=(0.3, 1)))
        restart_spinner = Spinner(
            text=device.config.restart_policy,
            values=['no', 'always', 'unless-stopped', 'on-failure'],
            size_hint=(0.7, 1)
        )
        restart_layout.add_widget(restart_spinner)
        content.add_widget(restart_layout)
        
        # Buttons
        button_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        
        save_btn = Button(text='Save')
        cancel_btn = Button(text='Cancel')
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title=f'Edit {device.name}', content=content, size_hint=(0.6, 0.8))
        
        def save_config(instance):
            # Save environment variables
            device.config.environment_vars.clear()
            for key_input, value_input in env_inputs:
                if key_input.text and value_input.text:
                    device.config.environment_vars[key_input.text] = value_input.text
            
            # Save other settings
            device.config.storage_volume = vol_input.text
            device.config.command = cmd_input.text
            device.config.restart_policy = restart_spinner.text
            
            self.status_label.text = f"Updated {device.name} configuration"
            popup.dismiss()
        
        save_btn.bind(on_press=save_config)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def export_terraform(self, instance):
        """Export to Terraform with Docker provider"""
        if not self.canvas_widget.devices:
            self.status_label.text = "No devices to export"
            return
        
        # Create file chooser popup
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(path=os.getcwd())
        content.add_widget(file_chooser)
        
        # Filename input
        filename_layout = BoxLayout(size_hint=(1, None), height=40)
        filename_layout.add_widget(Label(text='Filename:', size_hint=(0.2, 1)))
        filename_input = TextInput(text='docker-compose.tf', size_hint=(0.8, 1), multiline=False)
        filename_layout.add_widget(filename_input)
        content.add_widget(filename_layout)
        
        # Buttons
        button_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        
        export_btn = Button(text='Export')
        cancel_btn = Button(text='Cancel')
        button_layout.add_widget(export_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title='Export Terraform Configuration', content=content, size_hint=(0.8, 0.8))
        
        def do_export(instance):
            filepath = os.path.join(file_chooser.path, filename_input.text)
            self._do_export_terraform(filepath, popup)
        
        export_btn.bind(on_press=do_export)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def _do_export_terraform(self, filepath, popup):
        """Generate and save Terraform configuration"""
        tf_content = self.generate_terraform()
        
        try:
            with open(filepath, 'w') as f:
                f.write(tf_content)
            
            # Also generate docker-compose.yml
            compose_path = filepath.replace('.tf', '.yml')
            compose_content = self.generate_docker_compose()
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            self.status_label.text = f"Exported to {os.path.basename(filepath)}"
            popup.dismiss()
        except Exception as e:
            self.status_label.text = f"Export failed: {str(e)}"
    
    def generate_terraform(self):
        """Generate Terraform configuration for Docker"""
        tf = []
        
        # Header
        tf.append("# Terraform Docker Network Configuration")
        tf.append("# Generated by Network Designer")
        tf.append("")
        tf.append("terraform {")
        tf.append("  required_providers {")
        tf.append("    docker = {")
        tf.append('      source  = "kreuzwerker/docker"')
        tf.append('      version = "~> 3.0"')
        tf.append("    }")
        tf.append("  }")
        tf.append("}")
        tf.append("")
        tf.append('provider "docker" {}')
        tf.append("")
        
        # Networks
        networks = set()
        for device in self.canvas_widget.devices.values():
            networks.add(device.network)
        
        for network in networks:
            safe_name = network.replace('-', '_').replace('.', '_')
            tf.append(f'resource "docker_network" "{safe_name}_network" {{')
            tf.append(f'  name = "{network}"')
            tf.append('  driver = "bridge"')
            tf.append("}")
            tf.append("")
        
        # Containers
        for device in self.canvas_widget.devices.values():
            resource_name = device.name.replace('-', '_').replace('.', '_')
            network_name = device.network.replace('-', '_').replace('.', '_')
            
            tf.append(f'resource "docker_container" "{resource_name}" {{')
            tf.append(f'  name  = "{device.name}"')
            tf.append(f'  image = "{device.config.os.value}"')
            tf.append("")
            
            # Networks
            tf.append("  networks_advanced {")
            tf.append(f'    name = docker_network.{network_name}_network.name')
            tf.append("  }")
            tf.append("")
            
            # Ports
            for port_mapping in device.config.ports:
                if ':' in port_mapping:
                    external, internal = port_mapping.split(':')
                    tf.append("  ports {")
                    tf.append(f'    internal = {internal}')
                    tf.append(f'    external = {external}')
                    tf.append("  }")
            
            # Environment variables
            if device.config.environment_vars:
                tf.append("  env = [")
                for key, value in device.config.environment_vars.items():
                    tf.append(f'    "{key}={value}",')
                tf.append("  ]")
                tf.append("")
            
            # Volumes
            if device.config.storage_volume and ':' in device.config.storage_volume:
                host_path, container_path = device.config.storage_volume.split(':')
                tf.append("  volumes {")
                tf.append(f'    host_path      = "{host_path}"')
                tf.append(f'    container_path = "{container_path}"')
                tf.append("  }")
                tf.append("")
            
            # Command
            if device.config.command:
                tf.append(f'  command = ["{device.config.command}"]')
                tf.append("")
            
            # Restart policy
            tf.append(f'  restart = "{device.config.restart_policy}"')
            tf.append("")
            
            # Resource limits
            if device.config.cpu_limit or device.config.memory_limit:
                tf.append("  # Resource limits")
                if device.config.cpu_limit:
                    tf.append(f'  cpu_shares = {int(device.config.cpu_limit * 1024)}')
                if device.config.memory_limit:
                    mem_value = device.config.memory_limit.replace('m', '').replace('g', '000')
                    try:
                        tf.append(f'  memory = {int(mem_value)}')
                    except:
                        tf.append(f'  memory = 512')
                tf.append("")
            
            tf.append("}")
            tf.append("")
        
        return '\n'.join(tf)
    
    def generate_docker_compose(self):
        """Generate docker-compose.yml"""
        compose = []
        
        compose.append("# Docker Compose Configuration")
        compose.append("# Generated by Network Designer")
        compose.append("")
        compose.append("version: '3.8'")
        compose.append("")
        compose.append("services:")
        
        for device in self.canvas_widget.devices.values():
            compose.append(f"  {device.name}:")
            compose.append(f"    image: {device.config.os.value}")
            compose.append(f"    container_name: {device.name}")
            
            if device.config.command:
                compose.append(f"    command: {device.config.command}")
            
            if device.config.ports:
                compose.append("    ports:")
                for port in device.config.ports:
                    compose.append(f'      - "{port}"')
            
            if device.config.environment_vars:
                compose.append("    environment:")
                for key, value in device.config.environment_vars.items():
                    compose.append(f"      - {key}={value}")
            
            if device.config.storage_volume:
                compose.append("    volumes:")
                compose.append(f"      - {device.config.storage_volume}")
            
            compose.append("    networks:")
            compose.append(f"      - {device.network}")
            
            if device.config.cpu_limit or device.config.memory_limit:
                compose.append("    deploy:")
                compose.append("      resources:")
                compose.append("        limits:")
                if device.config.cpu_limit:
                    compose.append(f"          cpus: '{device.config.cpu_limit}'")
                if device.config.memory_limit:
                    compose.append(f"          memory: {device.config.memory_limit}")
            
            compose.append(f"    restart: {device.config.restart_policy}")
            compose.append("")
        
        # Networks
        compose.append("networks:")
        networks = set()
        for device in self.canvas_widget.devices.values():
            networks.add(device.network)
        
        for network in networks:
            compose.append(f"  {network}:")
            compose.append("    driver: bridge")
        
        return '\n'.join(compose)
    
    def export_svg(self, instance):
        """Export diagram as SVG"""
        # Create file chooser popup
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(path=os.getcwd())
        content.add_widget(file_chooser)
        
        # Filename input
        filename_layout = BoxLayout(size_hint=(1, None), height=40)
        filename_layout.add_widget(Label(text='Filename:', size_hint=(0.2, 1)))
        filename_input = TextInput(text='network_diagram.svg', size_hint=(0.8, 1), multiline=False)
        filename_layout.add_widget(filename_input)
        content.add_widget(filename_layout)
        
        # Buttons
        button_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        
        export_btn = Button(text='Export')
        cancel_btn = Button(text='Cancel')
        button_layout.add_widget(export_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title='Export SVG Image', content=content, size_hint=(0.8, 0.8))
        
        def do_export(instance):
            filepath = os.path.join(file_chooser.path, filename_input.text)
            try:
                self.canvas_widget.export_to_svg(filepath)
                self.status_label.text = f"Exported SVG to {os.path.basename(filepath)}"
                popup.dismiss()
            except Exception as e:
                self.status_label.text = f"SVG export failed: {str(e)}"
        
        export_btn.bind(on_press=do_export)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def save_project(self, instance):
        """Save project to JSON"""
        project_data = {
            "devices": {},
            "connections": {}
        }
        
        # Serialize devices
        for dev_id, device in self.canvas_widget.devices.items():
            dev_dict = {
                "id": device.id,
                "type": device.type.value,
                "name": device.name,
                "x": device.x,
                "y": device.y,
                "network": device.network,
                "connections": device.connections
            }
            
            if device.config:
                dev_dict["config"] = {
                    "cpu_limit": device.config.cpu_limit,
                    "memory_limit": device.config.memory_limit,
                    "storage_volume": device.config.storage_volume,
                    "os": device.config.os.value,
                    "command": device.config.command,
                    "restart_policy": device.config.restart_policy,
                    "ports": device.config.ports,
                    "environment_vars": device.config.environment_vars,
                    "interfaces": [
                        {
                            "name": iface.name,
                            "ip_address": iface.ip_address,
                            "subnet": iface.subnet
                        } for iface in device.config.interfaces
                    ]
                }
            
            project_data["devices"][dev_id] = dev_dict
        
        # Serialize connections
        for conn_id, conn in self.canvas_widget.connections.items():
            project_data["connections"][conn_id] = {
                "id": conn.id,
                "source_id": conn.source_id,
                "target_id": conn.target_id,
                "network_name": conn.network_name
            }
        
        # Save to file
        try:
            with open('network_project.json', 'w') as f:
                json.dump(project_data, f, indent=2)
            self.status_label.text = "Project saved"
        except Exception as e:
            self.status_label.text = f"Save failed: {str(e)}"
    
    def load_project(self, instance):
        """Load project from JSON"""
        try:
            with open('network_project.json', 'r') as f:
                project_data = json.load(f)
            
            # Clear canvas
            self.canvas_widget.clear_canvas()
            
            # Load devices
            for dev_id, dev_dict in project_data["devices"].items():
                device = NetworkDevice(
                    id=dev_dict["id"],
                    type=DeviceType(dev_dict["type"]),
                    name=dev_dict["name"],
                    x=dev_dict["x"],
                    y=dev_dict["y"],
                    network=dev_dict.get("network", "default"),
                    connections=dev_dict["connections"]
                )
                
                if "config" in dev_dict:
                    config_dict = dev_dict["config"]
                    device.config = ComputerConfig(
                        cpu_limit=config_dict.get("cpu_limit", 1.0),
                        memory_limit=config_dict.get("memory_limit", "512m"),
                        storage_volume=config_dict.get("storage_volume", ""),
                        os=OSType(config_dict.get("os", "alpine:latest")),
                        command=config_dict.get("command", ""),
                        restart_policy=config_dict.get("restart_policy", "unless-stopped"),
                        ports=config_dict.get("ports", []),
                        environment_vars=config_dict.get("environment_vars", {}),
                        interfaces=[
                            NetworkInterface(
                                name=iface["name"],
                                ip_address=iface["ip_address"],
                                subnet=iface["subnet"]
                            ) for iface in config_dict.get("interfaces", [])
                        ]
                    )
                
                self.canvas_widget.devices[device.id] = device
                widget = NetworkDeviceWidget(device, self.canvas_widget)
                self.canvas_widget.device_widgets[device.id] = widget
                self.canvas_widget.add_widget(widget)
            
            # Load connections
            for conn_id, conn_dict in project_data["connections"].items():
                conn = Connection(
                    id=conn_dict["id"],
                    source_id=conn_dict["source_id"],
                    target_id=conn_dict["target_id"],
                    network_name=conn_dict.get("network_name", "default")
                )
                self.canvas_widget.connections[conn.id] = conn
            
            self.canvas_widget.draw_connections()
            self.status_label.text = "Project loaded"
            
        except FileNotFoundError:
            self.status_label.text = "No saved project found"
        except Exception as e:
            self.status_label.text = f"Load failed: {str(e)}"


def main():
    """Main entry point"""
    NetworkDesignerApp().run()


if __name__ == "__main__":
    main()
