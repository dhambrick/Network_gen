#!/usr/bin/env python3
"""
Network Designer - Main Application
A modern network topology designer with Docker/Terraform export
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Kivy configuration
os.environ['KIVY_NO_ARGS'] = '1'

import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.config import Config

# Configure Kivy
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'minimum_width', '1200')
Config.set('graphics', 'minimum_height', '700')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'multisamples', '4')  # Anti-aliasing

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation

# Import application modules
from models import (
    NetworkProject, NetworkDevice, DeviceType, OSType, 
    ComputerConfig, NetworkInterface, Connection
)
from widgets import NetworkCanvas, NetworkInterfaceEditor
from exporters import TerraformExporter, DockerComposeExporter, SVGExporter


class NetworkDesignerApp(App):
    """Main application class"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project = NetworkProject(
            name="New Project",
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        self.project_file = None
        
    def build(self):
        """Build the application UI"""
        self.title = "Network Designer - Docker Edition"
        self.icon = None
        
        # Set window properties
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # Create main layout
        main_layout = BoxLayout(orientation='horizontal')
        
        # Build UI components
        left_panel = self.build_left_panel()
        center_panel = self.build_center_panel()
        right_panel = self.build_right_panel()
        
        # Add panels with proper sizing
        main_layout.add_widget(left_panel)
        main_layout.add_widget(center_panel)
        main_layout.add_widget(right_panel)
        
        # Schedule initial setup
        Clock.schedule_once(self.post_build_init, 0)
        
        return main_layout
    
    def build_left_panel(self):
        """Build left tools panel"""
        panel = BoxLayout(orientation='vertical', size_hint=(0.15, 1), spacing=5)
        
        # Title
        title = Label(
            text='[b]Network Elements[/b]',
            markup=True,
            size_hint=(1, 0.05),
            color=(0.2, 0.2, 0.2, 1)
        )
        panel.add_widget(title)
        
        # Device buttons grid
        devices_scroll = ScrollView(size_hint=(1, 0.5))
        devices_grid = GridLayout(
            cols=1,
            spacing=5,
            padding=10,
            size_hint_y=None
        )
        devices_grid.bind(minimum_height=devices_grid.setter('height'))
        
        # Device type buttons with better styling
        device_types = [
            ("💻 Computer", DeviceType.COMPUTER, "#4d7fc7"),
            ("🔀 Router", DeviceType.ROUTER, "#4db34d"),
            ("🔌 Switch", DeviceType.SWITCH, "#b3b34d"),
            ("🛡️ Firewall", DeviceType.FIREWALL, "#cc4d4d"),
            ("🗄️ Database", DeviceType.DATABASE, "#9966cc"),
            ("⚖️ Load Balancer", DeviceType.LOADBALANCER, "#66b3b3")
        ]
        
        for label, device_type, color in device_types:
            btn = Button(
                text=label,
                size_hint=(1, None),
                height=45,
                background_normal='',
                background_color=self.hex_to_rgba(color)
            )
            btn.bind(on_press=lambda x, dt=device_type: self.start_device_placement(dt))
            devices_grid.add_widget(btn)
        
        devices_scroll.add_widget(devices_grid)
        panel.add_widget(devices_scroll)
        
        # Mode selection
        panel.add_widget(Label(
            text='[b]Mode[/b]',
            markup=True,
            size_hint=(1, 0.05),
            color=(0.2, 0.2, 0.2, 1)
        ))
        
        mode_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.25), spacing=5, padding=10)
        
        # Mode buttons
        self.mode_buttons = {}
        modes = [
            ("Select/Move", "select", self.set_select_mode),
            ("Connect", "connect", self.set_connect_mode),
            ("Delete", "delete", self.set_delete_mode)
        ]
        
        for label, mode, callback in modes:
            btn = Button(text=label, size_hint=(1, None), height=40)
            btn.bind(on_press=callback)
            self.mode_buttons[mode] = btn
            mode_layout.add_widget(btn)
        
        # Highlight default mode
        self.mode_buttons["select"].background_color = (0.3, 0.6, 1, 1)
        
        panel.add_widget(mode_layout)
        
        # Actions
        panel.add_widget(Label(
            text='[b]Actions[/b]',
            markup=True,
            size_hint=(1, 0.05),
            color=(0.2, 0.2, 0.2, 1)
        ))
        
        actions_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.15), spacing=5, padding=10)
        
        clear_btn = Button(text='Clear Canvas', size_hint=(1, None), height=35)
        clear_btn.bind(on_press=self.clear_canvas)
        actions_layout.add_widget(clear_btn)
        
        export_menu_btn = Button(text='Export Options ▼', size_hint=(1, None), height=35)
        export_menu_btn.bind(on_press=self.show_export_menu)
        actions_layout.add_widget(export_menu_btn)
        
        panel.add_widget(actions_layout)
        
        return panel
    
    def build_center_panel(self):
        """Build center canvas panel"""
        panel = BoxLayout(orientation='vertical', size_hint=(0.65, 1))
        
        # Header with project info
        header = BoxLayout(size_hint=(1, 0.05), padding=5, spacing=10)
        
        self.project_label = Label(
            text=f'[b]Project: {self.project.name}[/b]',
            markup=True,
            size_hint=(0.6, 1),
            halign='left',
            color=(0.2, 0.2, 0.2, 1)
        )
        header.add_widget(self.project_label)
        
        # Quick actions
        save_btn = Button(text='💾', size_hint=(None, 1), width=40)
        save_btn.bind(on_press=self.quick_save)
        header.add_widget(save_btn)
        
        undo_btn = Button(text='↶', size_hint=(None, 1), width=40)
        undo_btn.bind(on_press=self.undo)
        header.add_widget(undo_btn)
        
        redo_btn = Button(text='↷', size_hint=(None, 1), width=40)
        redo_btn.bind(on_press=self.redo)
        header.add_widget(redo_btn)
        
        panel.add_widget(header)
        
        # Canvas
        self.canvas_widget = NetworkCanvas(self, size_hint=(1, 0.9))
        panel.add_widget(self.canvas_widget)
        
        # Status bar
        self.status_label = Label(
            text='Ready',
            size_hint=(1, 0.05),
            color=(0.3, 0.3, 0.3, 1)
        )
        panel.add_widget(self.status_label)
        
        return panel
    
    def build_right_panel(self):
        """Build right properties panel"""
        panel = TabbedPanel(size_hint=(0.2, 1), do_default_tab=False)
        
        # Properties tab
        properties_tab = TabbedPanelItem(text='Properties')
        self.properties_scroll = ScrollView()
        self.properties_content = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=5,
            size_hint_y=None
        )
        self.properties_content.bind(minimum_height=self.properties_content.setter('height'))
        self.properties_scroll.add_widget(self.properties_content)
        properties_tab.add_widget(self.properties_scroll)
        panel.add_widget(properties_tab)
        
        # Project tab
        project_tab = TabbedPanelItem(text='Project')
        project_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Project name
        name_layout = BoxLayout(size_hint=(1, None), height=35)
        name_layout.add_widget(Label(text='Name:', size_hint=(0.3, 1)))
        self.project_name_input = TextInput(
            text=self.project.name,
            size_hint=(0.7, 1),
            multiline=False
        )
        self.project_name_input.bind(text=self.update_project_name)
        name_layout.add_widget(self.project_name_input)
        project_layout.add_widget(name_layout)
        
        # Project description
        desc_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100)
        desc_layout.add_widget(Label(text='Description:', size_hint=(1, None), height=25))
        self.project_desc_input = TextInput(
            text=self.project.description,
            size_hint=(1, None),
            height=75,
            multiline=True
        )
        self.project_desc_input.bind(text=self.update_project_description)
        desc_layout.add_widget(self.project_desc_input)
        project_layout.add_widget(desc_layout)
        
        # Project actions
        save_btn = Button(text='Save Project', size_hint=(1, None), height=35)
        save_btn.bind(on_press=self.save_project)
        project_layout.add_widget(save_btn)
        
        load_btn = Button(text='Load Project', size_hint=(1, None), height=35)
        load_btn.bind(on_press=self.load_project)
        project_layout.add_widget(load_btn)
        
        new_btn = Button(text='New Project', size_hint=(1, None), height=35)
        new_btn.bind(on_press=self.new_project)
        project_layout.add_widget(new_btn)
        
        # Spacer
        project_layout.add_widget(Label(size_hint=(1, 1)))
        
        project_tab.add_widget(project_layout)
        panel.add_widget(project_tab)
        
        # Settings tab
        settings_tab = TabbedPanelItem(text='Settings')
        settings_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Grid snap
        grid_layout = BoxLayout(size_hint=(1, None), height=35)
        grid_layout.add_widget(Label(text='Grid Snap:', size_hint=(0.6, 1)))
        self.grid_snap_check = CheckBox(active=True, size_hint=(0.4, 1))
        grid_layout.add_widget(self.grid_snap_check)
        settings_layout.add_widget(grid_layout)
        
        # Animation speed
        anim_layout = BoxLayout(size_hint=(1, None), height=35)
        anim_layout.add_widget(Label(text='Animation:', size_hint=(0.4, 1)))
        self.anim_slider = Slider(min=0, max=1, value=0.5, size_hint=(0.6, 1))
        anim_layout.add_widget(self.anim_slider)
        settings_layout.add_widget(anim_layout)
        
        # Spacer
        settings_layout.add_widget(Label(size_hint=(1, 1)))
        
        settings_tab.add_widget(settings_layout)
        panel.add_widget(settings_tab)
        
        return panel
    
    def post_build_init(self, dt):
        """Post-build initialization"""
        self.current_mode = "select"
        self.status_label.text = "Ready - Select mode active"
    
    def hex_to_rgba(self, hex_color):
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)) + (0.8,)
    
    def start_device_placement(self, device_type):
        """Start device placement mode"""
        self.placing_device_type = device_type
        self.status_label.text = f"Click on canvas to place {device_type.value}"
        
        # Visual feedback
        Window.set_system_cursor('crosshair')
    
    def set_select_mode(self, instance):
        """Set select/move mode"""
        self.current_mode = "select"
        self.canvas_widget.connection_mode = False
        self.canvas_widget.connection_start = None
        self.status_label.text = "Select mode - Click to select, drag to move"
        
        # Update button states
        for mode, btn in self.mode_buttons.items():
            btn.background_color = (0.3, 0.6, 1, 1) if mode == "select" else (1, 1, 1, 1)
        
        Window.set_system_cursor('arrow')
    
    def set_connect_mode(self, instance):
        """Set connection mode"""
        self.current_mode = "connect"
        self.canvas_widget.connection_mode = True
        self.canvas_widget.connection_start = None
        self.status_label.text = "Connect mode - Click two devices to connect"
        
        # Update button states
        for mode, btn in self.mode_buttons.items():
            btn.background_color = (0.3, 0.6, 1, 1) if mode == "connect" else (1, 1, 1, 1)
        
        Window.set_system_cursor('hand')
    
    def set_delete_mode(self, instance):
        """Set delete mode"""
        self.current_mode = "delete"
        self.status_label.text = "Delete mode - Click devices or connections to delete"
        
        # Update button states
        for mode, btn in self.mode_buttons.items():
            btn.background_color = (0.3, 0.6, 1, 1) if mode == "delete" else (1, 1, 1, 1)
        
        Window.set_system_cursor('no')
    
    def show_device_properties(self, device):
        """Show device properties in the properties panel"""
        self.properties_content.clear_widgets()
        
        # Device header
        header = Label(
            text=f'[b]{device.name}[/b]',
            markup=True,
            size_hint=(1, None),
            height=30,
            color=(0.2, 0.2, 0.2, 1)
        )
        self.properties_content.add_widget(header)
        
        # Device type
        type_label = Label(
            text=f'Type: {device.type.value}',
            size_hint=(1, None),
            height=25,
            color=(0.4, 0.4, 0.4, 1)
        )
        self.properties_content.add_widget(type_label)
        
        # Name edit
        name_layout = BoxLayout(size_hint=(1, None), height=35)
        name_layout.add_widget(Label(text='Name:', size_hint=(0.3, 1)))
        name_input = TextInput(text=device.name, size_hint=(0.7, 1), multiline=False)
        
        def update_name(instance, value):
            device.name = value
            if device.id in self.canvas_widget.device_widgets:
                widget = self.canvas_widget.device_widgets[device.id]
                widget.device_name = value
                widget.draw_device()
        
        name_input.bind(text=update_name)
        name_layout.add_widget(name_input)
        self.properties_content.add_widget(name_layout)
        
        # Networks
        networks_layout = BoxLayout(size_hint=(1, None), height=35)
        networks_layout.add_widget(Label(text='Networks:', size_hint=(0.3, 1)))
        networks_input = TextInput(
            text=','.join(device.networks),
            size_hint=(0.7, 1),
            multiline=False,
            hint_text='default,frontend,backend'
        )
        
        def update_networks(instance, value):
            device.networks = [n.strip() for n in value.split(',') if n.strip()]
        
        networks_input.bind(text=update_networks)
        networks_layout.add_widget(networks_input)
        self.properties_content.add_widget(networks_layout)
        
        if device.config:
            # Separator
            self.properties_content.add_widget(
                Label(text='─' * 20, size_hint=(1, None), height=20)
            )
            
            # Container configuration
            self.properties_content.add_widget(
                Label(
                    text='[b]Container Config[/b]',
                    markup=True,
                    size_hint=(1, None),
                    height=25,
                    color=(0.2, 0.2, 0.2, 1)
                )
            )
            
            # OS/Image
            os_layout = BoxLayout(size_hint=(1, None), height=35)
            os_layout.add_widget(Label(text='Image:', size_hint=(0.3, 1)))
            
            if device.config.os == OSType.CUSTOM:
                os_input = TextInput(
                    text=device.config.custom_image,
                    size_hint=(0.7, 1),
                    multiline=False,
                    hint_text='custom:image'
                )
                os_input.bind(text=lambda i, v: setattr(device.config, 'custom_image', v))
                os_layout.add_widget(os_input)
            else:
                os_spinner = Spinner(
                    text=device.config.os.value,
                    values=[os.value for os in OSType],
                    size_hint=(0.7, 1)
                )
                
                def update_os(instance, value):
                    device.config.os = OSType(value)
                    if device.config.os == OSType.CUSTOM:
                        self.show_device_properties(device)  # Refresh to show custom input
                
                os_spinner.bind(text=update_os)
                os_layout.add_widget(os_spinner)
            
            self.properties_content.add_widget(os_layout)
            
            # CPU limit
            cpu_layout = BoxLayout(size_hint=(1, None), height=35)
            cpu_layout.add_widget(Label(text='CPU:', size_hint=(0.3, 1)))
            cpu_slider = Slider(min=0.25, max=4, value=device.config.cpu_limit, step=0.25)
            cpu_label = Label(text=f'{device.config.cpu_limit:.2f}', size_hint=(0.2, 1))
            
            def update_cpu(instance, value):
                device.config.cpu_limit = value
                cpu_label.text = f'{value:.2f}'
            
            cpu_slider.bind(value=update_cpu)
            cpu_layout.add_widget(cpu_slider)
            cpu_layout.add_widget(cpu_label)
            self.properties_content.add_widget(cpu_layout)
            
            # Memory limit
            mem_layout = BoxLayout(size_hint=(1, None), height=35)
            mem_layout.add_widget(Label(text='Memory:', size_hint=(0.3, 1)))
            mem_input = TextInput(
                text=device.config.memory_limit,
                size_hint=(0.7, 1),
                multiline=False,
                hint_text='512m, 1g'
            )
            mem_input.bind(text=lambda i, v: setattr(device.config, 'memory_limit', v))
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
            
            def update_ports(instance, value):
                device.config.ports = [p.strip() for p in value.split(',') if p.strip()]
            
            ports_input.bind(text=update_ports)
            ports_layout.add_widget(ports_input)
            self.properties_content.add_widget(ports_layout)
            
            # Volumes
            vol_layout = BoxLayout(size_hint=(1, None), height=35)
            vol_layout.add_widget(Label(text='Volume:', size_hint=(0.3, 1)))
            vol_input = TextInput(
                text=device.config.storage_volume,
                size_hint=(0.7, 1),
                multiline=False,
                hint_text='./data:/data'
            )
            vol_input.bind(text=lambda i, v: setattr(device.config, 'storage_volume', v))
            vol_layout.add_widget(vol_input)
            self.properties_content.add_widget(vol_layout)
            
            # Advanced buttons
            self.properties_content.add_widget(
                Label(text='─' * 20, size_hint=(1, None), height=20)
            )
            
            # Network interfaces button
            iface_btn = Button(
                text='Edit Network Interfaces',
                size_hint=(1, None),
                height=35,
                background_color=(0.3, 0.7, 0.3, 1)
            )
            iface_btn.bind(on_press=lambda x: self.edit_network_interfaces(device))
            self.properties_content.add_widget(iface_btn)
            
            # Environment variables button
            env_btn = Button(
                text='Environment Variables',
                size_hint=(1, None),
                height=35,
                background_color=(0.5, 0.5, 0.8, 1)
            )
            env_btn.bind(on_press=lambda x: self.edit_environment_vars(device))
            self.properties_content.add_widget(env_btn)
            
            # Advanced settings button
            adv_btn = Button(
                text='Advanced Settings',
                size_hint=(1, None),
                height=35,
                background_color=(0.6, 0.6, 0.6, 1)
            )
            adv_btn.bind(on_press=lambda x: self.open_device_editor(device))
            self.properties_content.add_widget(adv_btn)
    
    def edit_network_interfaces(self, device):
        """Open network interface editor"""
        popup = Popup(
            title=f'Network Interfaces - {device.name}',
            size_hint=(0.7, 0.8)
        )
        
        editor = NetworkInterfaceEditor(
            device,
            on_save_callback=popup.dismiss
        )
        
        popup.content = editor
        popup.open()
    
    def edit_environment_vars(self, device):
        """Edit environment variables"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Instructions
        content.add_widget(
            Label(
                text='Environment Variables (one per line, KEY=VALUE format)',
                size_hint=(1, None),
                height=30
            )
        )
        
        # Text input for environment variables
        env_text = '\n'.join([f'{k}={v}' for k, v in device.config.environment_vars.items()])
        env_input = TextInput(
            text=env_text,
            size_hint=(1, 1),
            multiline=True
        )
        content.add_widget(env_input)
        
        # Buttons
        button_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        
        save_btn = Button(text='Save')
        cancel_btn = Button(text='Cancel')
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title=f'Environment Variables - {device.name}',
            content=content,
            size_hint=(0.6, 0.7)
        )
        
        def save_env(instance):
            device.config.environment_vars.clear()
            for line in env_input.text.split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    device.config.environment_vars[key.strip()] = value.strip()
            self.status_label.text = f"Updated environment variables for {device.name}"
            popup.dismiss()
        
        save_btn.bind(on_press=save_env)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def open_device_editor(self, device):
        """Open advanced device editor"""
        # This would open a comprehensive editor for all device settings
        # For now, we'll show a message
        self.status_label.text = "Advanced editor coming soon"
    
    def show_export_menu(self, instance):
        """Show export options menu"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Export options
        terraform_btn = Button(text='Export Terraform', size_hint=(1, None), height=40)
        terraform_btn.bind(on_press=lambda x: self.export_terraform(popup))
        content.add_widget(terraform_btn)
        
        compose_btn = Button(text='Export Docker Compose', size_hint=(1, None), height=40)
        compose_btn.bind(on_press=lambda x: self.export_docker_compose(popup))
        content.add_widget(compose_btn)
        
        svg_btn = Button(text='Export SVG Diagram', size_hint=(1, None), height=40)
        svg_btn.bind(on_press=lambda x: self.export_svg(popup))
        content.add_widget(svg_btn)
        
        both_btn = Button(text='Export All (TF + Compose + SVG)', size_hint=(1, None), height=40)
        both_btn.bind(on_press=lambda x: self.export_all(popup))
        content.add_widget(both_btn)
        
        popup = Popup(
            title='Export Options',
            content=content,
            size_hint=(0.4, 0.4)
        )
        popup.open()
    
    def export_terraform(self, popup=None):
        """Export to Terraform"""
        if popup:
            popup.dismiss()
        
        # Update project with canvas data
        self.sync_project_with_canvas()
        
        # Generate Terraform
        tf_content = TerraformExporter.export(self.project)
        
        # Save to file
        filename = f"{self.project.name.replace(' ', '_').lower()}.tf"
        with open(filename, 'w') as f:
            f.write(tf_content)
        
        self.status_label.text = f"Exported Terraform to {filename}"
    
    def export_docker_compose(self, popup=None):
        """Export to Docker Compose"""
        if popup:
            popup.dismiss()
        
        # Update project with canvas data
        self.sync_project_with_canvas()
        
        # Generate Docker Compose
        compose_content = DockerComposeExporter.export(self.project)
        
        # Save to file
        filename = f"{self.project.name.replace(' ', '_').lower()}-compose.yml"
        with open(filename, 'w') as f:
            f.write(compose_content)
        
        self.status_label.text = f"Exported Docker Compose to {filename}"
    
    def export_svg(self, popup=None):
        """Export to SVG"""
        if popup:
            popup.dismiss()
        
        filename = f"{self.project.name.replace(' ', '_').lower()}_diagram.svg"
        SVGExporter.export(self.canvas_widget, filename)
        self.status_label.text = f"Exported SVG to {filename}"
    
    def export_all(self, popup=None):
        """Export all formats"""
        if popup:
            popup.dismiss()
        
        self.export_terraform()
        self.export_docker_compose()
        self.export_svg()
        self.status_label.text = "Exported all formats successfully"
    
    def sync_project_with_canvas(self):
        """Sync project data with canvas state"""
        self.project.devices = self.canvas_widget.devices
        self.project.connections = self.canvas_widget.connections
        self.project.modified_at = datetime.now().isoformat()
    
    def save_project(self, instance=None):
        """Save project to file"""
        self.sync_project_with_canvas()
        
        filename = self.project_file or f"{self.project.name.replace(' ', '_').lower()}_project.json"
        
        with open(filename, 'w') as f:
            json.dump(self.project.to_dict(), f, indent=2)
        
        self.project_file = filename
        self.status_label.text = f"Project saved to {filename}"
    
    def load_project(self, instance=None):
        """Load project from file"""
        # File chooser would go here
        # For now, try to load default file
        try:
            with open('network_project.json', 'r') as f:
                data = json.load(f)
            
            self.project = NetworkProject.from_dict(data)
            self.canvas_widget.clear_canvas()
            
            # Load devices and connections to canvas
            for device in self.project.devices.values():
                self.canvas_widget.devices[device.id] = device
                widget = self.canvas_widget.add_device(device.type, device.x, device.y)
            
            for conn in self.project.connections.values():
                self.canvas_widget.connections[conn.id] = conn
            
            self.canvas_widget.draw_connections()
            
            # Update UI
            self.project_name_input.text = self.project.name
            self.project_desc_input.text = self.project.description
            self.project_label.text = f'[b]Project: {self.project.name}[/b]'
            
            self.status_label.text = "Project loaded successfully"
            
        except Exception as e:
            self.status_label.text = f"Failed to load project: {str(e)}"
    
    def new_project(self, instance=None):
        """Create new project"""
        self.project = NetworkProject(
            name="New Project",
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat()
        )
        self.project_file = None
        self.canvas_widget.clear_canvas()
        
        # Update UI
        self.project_name_input.text = self.project.name
        self.project_desc_input.text = self.project.description
        self.project_label.text = f'[b]Project: {self.project.name}[/b]'
        
        self.status_label.text = "New project created"
    
    def clear_canvas(self, instance):
        """Clear canvas with confirmation"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Clear all devices and connections?'))
        
        buttons = BoxLayout(spacing=10, size_hint=(1, 0.4))
        yes_btn = Button(text='Yes')
        no_btn = Button(text='No')
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Confirm Clear',
            content=content,
            size_hint=(0.4, 0.3)
        )
        
        yes_btn.bind(on_press=lambda x: self._do_clear(popup))
        no_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def _do_clear(self, popup):
        """Actually clear the canvas"""
        self.canvas_widget.clear_canvas()
        self.properties_content.clear_widgets()
        self.status_label.text = "Canvas cleared"
        popup.dismiss()
    
    def update_project_name(self, instance, value):
        """Update project name"""
        self.project.name = value
        self.project_label.text = f'[b]Project: {value}[/b]'
    
    def update_project_description(self, instance, value):
        """Update project description"""
        self.project.description = value
    
    def quick_save(self, instance):
        """Quick save project"""
        self.save_project()
    
    def undo(self, instance):
        """Undo last action"""
        self.status_label.text = "Undo not yet implemented"
    
    def redo(self, instance):
        """Redo last undone action"""
        self.status_label.text = "Redo not yet implemented"


def main():
    """Main entry point"""
    NetworkDesignerApp().run()


if __name__ == "__main__":
    main()
