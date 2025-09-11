#!/usr/bin/env python3
"""
Custom Kivy widgets for Network Designer
"""

from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Line, Color, Rectangle, Ellipse, RoundedRectangle, PushMatrix, PopMatrix, Translate
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.vector import Vector

from models import NetworkDevice, DeviceType, NetworkInterface
from typing import Optional, Tuple, Dict, List


class SmoothDragBehavior:
    """Smooth dragging behavior for widgets"""
    
    dragging = BooleanProperty(False)
    drag_distance = NumericProperty(10)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._drag_touch = None
        self._drag_offset = (0, 0)
        self._last_pos = (0, 0)
        self._velocity = [0, 0]
        self._drag_clock = None
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'left':
            if not self._drag_touch:
                touch.grab(self)
                self._drag_touch = touch
                self._drag_offset = (self.x - touch.x, self.y - touch.y)
                self._last_pos = touch.pos
                self.dragging = True
                
                # Start velocity tracking
                if self._drag_clock:
                    self._drag_clock.cancel()
                self._drag_clock = Clock.schedule_interval(self._update_velocity, 1/60.0)
                return True
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False
    
    def on_touch_move(self, touch):
        if self._drag_touch and touch.grab_current == self:
            # Smooth position update
            new_x = touch.x + self._drag_offset[0]
            new_y = touch.y + self._drag_offset[1]
            
            # Apply smoothing
            self.x = self.x * 0.3 + new_x * 0.7
            self.y = self.y * 0.3 + new_y * 0.7
            
            self._last_pos = touch.pos
            return True
        return super().on_touch_move(touch) if hasattr(super(), 'on_touch_move') else False
    
    def on_touch_up(self, touch):
        if self._drag_touch and touch.grab_current == self:
            touch.ungrab(self)
            self._drag_touch = None
            self.dragging = False
            
            # Stop velocity tracking
            if self._drag_clock:
                self._drag_clock.cancel()
                self._drag_clock = None
            
            # Apply momentum
            if abs(self._velocity[0]) > 1 or abs(self._velocity[1]) > 1:
                anim = Animation(
                    x=self.x + self._velocity[0] * 5,
                    y=self.y + self._velocity[1] * 5,
                    duration=0.3,
                    t='out_cubic'
                )
                anim.start(self)
            
            return True
        return super().on_touch_up(touch) if hasattr(super(), 'on_touch_up') else False
    
    def _update_velocity(self, dt):
        """Update velocity for momentum"""
        if self._drag_touch:
            self._velocity[0] = (self._drag_touch.x - self._last_pos[0]) * 0.5
            self._velocity[1] = (self._drag_touch.y - self._last_pos[1]) * 0.5


class NetworkDeviceWidget(SmoothDragBehavior, Widget):
    """Enhanced network device widget with smooth dragging"""
    
    device_id = StringProperty("")
    device_type = StringProperty("")
    device_name = StringProperty("")
    selected = BooleanProperty(False)
    hover = BooleanProperty(False)
    
    def __init__(self, device: NetworkDevice, canvas_widget, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.canvas_widget = canvas_widget
        self.device_id = device.id
        self.device_type = device.type.value
        self.device_name = device.name
        self.size = (90, 110)
        self.size_hint = (None, None)
        self.pos = (device.x, device.y)
        
        # Animation properties
        self._scale = 1.0
        self._rotation = 0
        self._glow_opacity = 0
        
        # Bind events
        self.bind(pos=self.on_pos_change)
        self.bind(selected=self.on_selection_change)
        self.bind(dragging=self.on_dragging_change)
        
        # Initial draw
        Clock.schedule_once(lambda dt: self.draw_device(), 0)
    
    def on_pos_change(self, instance, value):
        """Update device position when widget moves"""
        self.device.x = self.x
        self.device.y = self.y
        if hasattr(self.canvas_widget, 'update_connections'):
            self.canvas_widget.update_connections()
    
    def on_selection_change(self, instance, value):
        """Animate selection change"""
        if value:
            anim = Animation(_scale=1.1, _glow_opacity=0.5, duration=0.2, t='out_cubic')
        else:
            anim = Animation(_scale=1.0, _glow_opacity=0, duration=0.2, t='out_cubic')
        anim.bind(on_progress=lambda *args: self.draw_device())
        anim.start(self)
    
    def on_dragging_change(self, instance, value):
        """Animate dragging state"""
        if value:
            anim = Animation(_rotation=2, duration=0.1)
        else:
            anim = Animation(_rotation=0, duration=0.2, t='out_elastic')
        anim.bind(on_progress=lambda *args: self.draw_device())
        anim.start(self)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.canvas_widget.edit_device(self.device)
                return True
            else:
                self.canvas_widget.select_device(self)
                return super().on_touch_down(touch)
        return False
    
    def draw_device(self):
        """Draw device with animations"""
        self.canvas.clear()
        
        with self.canvas:
            # Save matrix state
            PushMatrix()
            
            # Apply transformations
            Translate(self.x + self.width/2, self.y + self.height/2)
            
            # Glow effect
            if self._glow_opacity > 0:
                Color(0.3, 0.6, 1, self._glow_opacity)
                Ellipse(
                    pos=(-self.width/2 - 10, -self.height/2 - 10),
                    size=(self.width + 20, self.height + 20)
                )
            
            # Selection highlight
            if self.selected:
                Color(0.2, 0.6, 1, 0.3)
                RoundedRectangle(
                    pos=(-self.width/2 - 5, -self.height/2 - 5),
                    size=(self.width + 10, self.height + 10),
                    radius=[(10, 10)]
                )
            
            # Device icon
            icon_color = self.get_device_color()
            Color(*icon_color)
            
            # Scale for animation
            scale_offset = (self._scale - 1) * 20
            
            # Draw device shape based on type
            if self.device.type == DeviceType.COMPUTER:
                self._draw_computer(-scale_offset)
            elif self.device.type == DeviceType.ROUTER:
                self._draw_router(-scale_offset)
            elif self.device.type == DeviceType.SWITCH:
                self._draw_switch(-scale_offset)
            elif self.device.type == DeviceType.FIREWALL:
                self._draw_firewall(-scale_offset)
            elif self.device.type == DeviceType.DATABASE:
                self._draw_database(-scale_offset)
            elif self.device.type == DeviceType.LOADBALANCER:
                self._draw_loadbalancer(-scale_offset)
            
            # Interface indicators
            self._draw_interfaces()
            
            # Restore matrix state
            PopMatrix()
            
            # Device name (outside transformation)
            Color(0.1, 0.1, 0.1, 1)
            Label(
                text=self.device_name,
                pos=(self.x - 10, self.y - 25),
                size=(self.width + 20, 20),
                font_size='11sp'
            )
    
    def _draw_computer(self, offset):
        """Draw computer icon"""
        # Monitor
        Color(0.3, 0.5, 0.8, 1)
        RoundedRectangle(
            pos=(-25 + offset/2, -10 + offset/2),
            size=(50 - offset, 35 - offset),
            radius=[(3, 3)]
        )
        # Screen
        Color(0.1, 0.1, 0.2, 1)
        Rectangle(
            pos=(-20 + offset/2, -5 + offset/2),
            size=(40 - offset, 25 - offset)
        )
        # Base
        Color(0.4, 0.4, 0.4, 1)
        Rectangle(pos=(-10, -20), size=(20, 8))
        Rectangle(pos=(-15, -25), size=(30, 5))
    
    def _draw_router(self, offset):
        """Draw router icon"""
        Color(0.3, 0.7, 0.4, 1)
        # Diamond shape
        Line(points=[
            0, -30 + offset,
            25 - offset/2, 0,
            0, 30 - offset,
            -25 + offset/2, 0,
            0, -30 + offset
        ], width=2.5, close=True)
        # Antenna
        Color(0.2, 0.2, 0.2, 1)
        Line(points=[-10, 30 - offset, -15, 40 - offset], width=2)
        Line(points=[10, 30 - offset, 15, 40 - offset], width=2)
    
    def _draw_switch(self, offset):
        """Draw switch icon"""
        Color(0.7, 0.7, 0.3, 1)
        RoundedRectangle(
            pos=(-30 + offset/2, -15 + offset/2),
            size=(60 - offset, 30 - offset),
            radius=[(3, 3)]
        )
        # Ports
        Color(0.2, 0.2, 0.2, 1)
        for i in range(4):
            Rectangle(
                pos=(-25 + i*15, -10),
                size=(10, 6)
            )
            Rectangle(
                pos=(-25 + i*15, 5),
                size=(10, 6)
            )
    
    def _draw_firewall(self, offset):
        """Draw firewall icon"""
        Color(0.8, 0.3, 0.3, 1)
        # Shield shape
        Line(points=[
            0, -35 + offset,
            20 - offset/2, -20,
            20 - offset/2, 10,
            0, 30 - offset,
            -20 + offset/2, 10,
            -20 + offset/2, -20,
            0, -35 + offset
        ], width=2.5, close=True)
        # Lock symbol
        Color(1, 1, 1, 0.8)
        Ellipse(pos=(-8, -5), size=(16, 16))
    
    def _draw_database(self, offset):
        """Draw database icon"""
        Color(0.6, 0.4, 0.7, 1)
        # Cylinder
        Ellipse(pos=(-20 + offset/2, 15), size=(40 - offset, 15))
        Rectangle(pos=(-20 + offset/2, -10), size=(40 - offset, 25))
        Ellipse(pos=(-20 + offset/2, -20), size=(40 - offset, 15))
        # Data lines
        Color(1, 1, 1, 0.3)
        for i in range(3):
            Line(points=[-15, -10 + i*10, 15, -10 + i*10], width=1)
    
    def _draw_loadbalancer(self, offset):
        """Draw load balancer icon"""
        Color(0.4, 0.7, 0.7, 1)
        Ellipse(
            pos=(-25 + offset/2, -25 + offset/2),
            size=(50 - offset, 50 - offset)
        )
        # Arrows
        Color(1, 1, 1, 0.9)
        Line(points=[-10, 0, 10, 0], width=2, arrow=True)
        Line(points=[0, -10, 0, 10], width=2)
    
    def _draw_interfaces(self):
        """Draw network interface indicators"""
        if self.device.config and self.device.config.interfaces:
            Color(0.2, 0.8, 0.2, 0.8)
            num_interfaces = len(self.device.config.interfaces)
            for i, iface in enumerate(self.device.config.interfaces):
                angle = (360 / max(num_interfaces, 4)) * i
                # Draw small circles for interfaces
                if iface.ip_address:
                    Color(0.2, 0.8, 0.2, 1)
                else:
                    Color(0.5, 0.5, 0.5, 0.5)
                Ellipse(
                    pos=(self.width/2 - 20 + i*10 - self.width/2, -self.height/2 + 5),
                    size=(6, 6)
                )
    
    def get_device_color(self):
        """Get color based on device type"""
        colors = {
            DeviceType.COMPUTER: (0.3, 0.5, 0.8, 1),
            DeviceType.ROUTER: (0.3, 0.7, 0.4, 1),
            DeviceType.SWITCH: (0.7, 0.7, 0.3, 1),
            DeviceType.FIREWALL: (0.8, 0.3, 0.3, 1),
            DeviceType.DATABASE: (0.6, 0.4, 0.7, 1),
            DeviceType.LOADBALANCER: (0.4, 0.7, 0.7, 1)
        }
        return colors.get(self.device.type, (0.5, 0.5, 0.5, 1))


class NetworkInterfaceEditor(BoxLayout):
    """Widget for editing network interfaces"""
    
    def __init__(self, device: NetworkDevice, on_save_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.on_save_callback = on_save_callback
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10
        self.interface_rows = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the interface editor UI"""
        # Title
        title = Label(text='Network Interfaces', size_hint=(1, None), height=30)
        self.add_widget(title)
        
        # Interface list header
        header = GridLayout(cols=6, size_hint=(1, None), height=30, spacing=5)
        header.add_widget(Label(text='Name', size_hint=(0.15, 1)))
        header.add_widget(Label(text='IP Address', size_hint=(0.2, 1)))
        header.add_widget(Label(text='Subnet Mask', size_hint=(0.2, 1)))
        header.add_widget(Label(text='Gateway', size_hint=(0.2, 1)))
        header.add_widget(Label(text='Primary', size_hint=(0.1, 1)))
        header.add_widget(Label(text='Actions', size_hint=(0.15, 1)))
        self.add_widget(header)
        
        # Scrollable interface list
        scroll = ScrollView(size_hint=(1, 1))
        self.interface_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.interface_list.bind(minimum_height=self.interface_list.setter('height'))
        scroll.add_widget(self.interface_list)
        self.add_widget(scroll)
        
        # Load existing interfaces
        if self.device.config:
            for interface in self.device.config.interfaces:
                self.add_interface_row(interface)
        
        # Add new interface button
        add_btn = Button(text='Add Interface', size_hint=(1, None), height=35)
        add_btn.bind(on_press=self.add_new_interface)
        self.add_widget(add_btn)
        
        # Save/Cancel buttons
        button_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        save_btn = Button(text='Save')
        save_btn.bind(on_press=self.save_interfaces)
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=self.cancel)
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        self.add_widget(button_layout)
    
    def add_interface_row(self, interface: NetworkInterface):
        """Add a row for editing an interface"""
        row = GridLayout(cols=6, size_hint=(1, None), height=35, spacing=5)
        
        # Name input
        name_input = TextInput(text=interface.name, multiline=False, size_hint=(0.15, 1))
        row.add_widget(name_input)
        
        # IP address input
        ip_input = TextInput(text=interface.ip_address, multiline=False, 
                           hint_text='192.168.1.10', size_hint=(0.2, 1))
        row.add_widget(ip_input)
        
        # Subnet mask input
        subnet_input = TextInput(text=interface.subnet_mask, multiline=False,
                               hint_text='255.255.255.0', size_hint=(0.2, 1))
        row.add_widget(subnet_input)
        
        # Gateway input
        gateway_input = TextInput(text=interface.gateway, multiline=False,
                                hint_text='192.168.1.1', size_hint=(0.2, 1))
        row.add_widget(gateway_input)
        
        # Primary checkbox
        from kivy.uix.checkbox import CheckBox
        primary_check = CheckBox(active=interface.is_primary, size_hint=(0.1, 1))
        primary_check.bind(active=lambda cb, value: self.set_primary(interface, value))
        row.add_widget(primary_check)
        
        # Delete button
        delete_btn = Button(text='Delete', size_hint=(0.15, 1))
        delete_btn.bind(on_press=lambda x: self.delete_interface(row, interface))
        row.add_widget(delete_btn)
        
        # Store references
        row.interface = interface
        row.inputs = {
            'name': name_input,
            'ip': ip_input,
            'subnet': subnet_input,
            'gateway': gateway_input,
            'primary': primary_check
        }
        
        self.interface_list.add_widget(row)
        self.interface_rows.append(row)
    
    def add_new_interface(self, instance):
        """Add a new interface"""
        new_interface = NetworkInterface(
            name=f"eth{len(self.interface_rows)}",
            is_primary=len(self.interface_rows) == 0
        )
        self.add_interface_row(new_interface)
    
    def delete_interface(self, row, interface):
        """Delete an interface"""
        self.interface_list.remove_widget(row)
        self.interface_rows.remove(row)
        
        # Update primary if needed
        if interface.is_primary and self.interface_rows:
            self.interface_rows[0].inputs['primary'].active = True
    
    def set_primary(self, interface, is_primary):
        """Set an interface as primary"""
        if is_primary:
            # Unset other primaries
            for row in self.interface_rows:
                if row.interface != interface:
                    row.inputs['primary'].active = False
    
    def save_interfaces(self, instance):
        """Save all interface configurations"""
        if self.device.config:
            # Clear existing interfaces
            self.device.config.interfaces.clear()
            
            # Add updated interfaces
            for row in self.interface_rows:
                interface = row.interface
                interface.name = row.inputs['name'].text
                interface.ip_address = row.inputs['ip'].text
                interface.subnet_mask = row.inputs['subnet'].text
                interface.gateway = row.inputs['gateway'].text
                interface.is_primary = row.inputs['primary'].active
                
                # Calculate CIDR from subnet mask
                if interface.subnet_mask:
                    try:
                        mask_bits = sum(bin(int(x)).count('1') 
                                      for x in interface.subnet_mask.split('.'))
                        interface.cidr = mask_bits
                    except:
                        interface.cidr = 24
                
                self.device.config.interfaces.append(interface)
        
        if self.on_save_callback:
            self.on_save_callback()
    
    def cancel(self, instance):
        """Cancel editing"""
        if self.on_save_callback:
            self.on_save_callback()


class NetworkCanvas(FloatLayout):
    """Enhanced canvas with smooth animations and better performance"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.devices = {}
        self.connections = {}
        self.device_widgets = {}
        self.selected_device = None
        self.connection_mode = False
        self.connection_start = None
        self.temp_line = None
        
        # Performance optimizations
        self._update_scheduled = False
        self._connection_cache = {}
        
        # Background
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Grid background
        self.draw_grid()
        
        # Bind events
        self.bind(size=self.update_bg, pos=self.update_bg)
    
    def draw_grid(self):
        """Draw grid background for better alignment"""
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 0.5)
            # Draw grid lines
            grid_size = 50
            for i in range(0, 2000, grid_size):
                Line(points=[i, 0, i, 2000], width=0.5)
                Line(points=[0, i, 2000, i], width=0.5)
    
    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def add_device(self, device_type, x, y):
        """Add a new device with animation"""
        # Snap to grid
        grid_size = 25
        x = round(x / grid_size) * grid_size
        y = round(y / grid_size) * grid_size
        
        # Ensure position is within bounds
        x = max(50, min(x, self.width - 100))
        y = max(50, min(y, self.height - 100))
        
        from models import NetworkDevice
        device = NetworkDevice(type=device_type, x=x, y=y)
        device.name = f"{device_type.value}_{len([d for d in self.devices.values() if d.type == device_type]) + 1}"
        
        self.devices[device.id] = device
        
        # Create widget with animation
        widget = NetworkDeviceWidget(device, self)
        widget.opacity = 0
        self.device_widgets[device.id] = widget
        self.add_widget(widget)
        
        # Animate appearance
        anim = Animation(opacity=1, duration=0.3, t='out_cubic')
        anim.start(widget)
        
        return device
    
    def select_device(self, widget):
        """Select a device with animation"""
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
                self.draw_temp_connection()
            elif widget != self.connection_start:
                self.create_connection(self.connection_start, widget)
                self.connection_start = None
                self.connection_mode = False
                self.clear_temp_connection()
    
    def draw_temp_connection(self):
        """Draw temporary connection line while connecting"""
        if self.connection_start:
            with self.canvas.after:
                Color(0.5, 0.5, 0.5, 0.5)
                self.temp_line = Line(
                    points=[
                        self.connection_start.x + self.connection_start.width/2,
                        self.connection_start.y + self.connection_start.height/2,
                        self.connection_start.x + self.connection_start.width/2,
                        self.connection_start.y + self.connection_start.height/2
                    ],
                    width=2,
                    dash_length=5,
                    dash_offset=2
                )
    
    def clear_temp_connection(self):
        """Clear temporary connection line"""
        if self.temp_line:
            self.canvas.after.remove(self.temp_line)
            self.temp_line = None
    
    def create_connection(self, source_widget, target_widget):
        """Create a connection with animation"""
        from models import Connection
        conn = Connection(
            source_id=source_widget.device.id,
            target_id=target_widget.device.id
        )
        self.connections[conn.id] = conn
        
        # Update device connections
        source_widget.device.add_connection(target_widget.device.id)
        target_widget.device.add_connection(source_widget.device.id)
        
        # Animate connection creation
        self.animate_connection(conn)
        
        # Schedule connection redraw
        self.schedule_connection_update()
    
    def animate_connection(self, connection):
        """Animate a new connection"""
        # Get widgets
        source = self.device_widgets.get(connection.source_id)
        target = self.device_widgets.get(connection.target_id)
        
        if source and target:
            # Create animated line
            with self.canvas.before:
                Color(0.2, 0.6, 1, 0)
                line = Line(
                    points=[
                        source.x + source.width/2,
                        source.y + source.height/2,
                        source.x + source.width/2,
                        source.y + source.height/2
                    ],
                    width=3
                )
            
            # Animate to target
            def update_line(animation, widget, progress):
                if source and target:
                    sx = source.x + source.width/2
                    sy = source.y + source.height/2
                    tx = target.x + target.width/2
                    ty = target.y + target.height/2
                    
                    line.points = [
                        sx, sy,
                        sx + (tx - sx) * progress,
                        sy + (ty - sy) * progress
                    ]
            
            anim = Animation(duration=0.3)
            anim.bind(on_progress=update_line)
            anim.bind(on_complete=lambda *args: self.draw_connections())
            anim.start(self)
    
    def schedule_connection_update(self):
        """Schedule connection update for performance"""
        if not self._update_scheduled:
            self._update_scheduled = True
            Clock.schedule_once(lambda dt: self.draw_connections(), 0.1)
    
    def draw_connections(self):
        """Draw all connections with caching for performance"""
        self._update_scheduled = False
        
        # Clear previous connection lines
        self.canvas.before.clear()
        
        # Redraw background and grid
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.draw_grid()
        
        # Draw connections
        with self.canvas.before:
            for conn in self.connections.values():
                source = self.device_widgets.get(conn.source_id)
                target = self.device_widgets.get(conn.target_id)
                
                if source and target:
                    # Calculate connection points
                    sx = source.x + source.width/2
                    sy = source.y + source.height/2
                    tx = target.x + target.width/2
                    ty = target.y + target.height/2
                    
                    # Draw connection line with gradient effect
                    Color(0.2, 0.2, 0.2, 0.6)
                    Line(points=[sx, sy, tx, ty], width=2.5)
                    
                    # Draw connection dots at endpoints
                    Color(0.3, 0.6, 0.9, 0.8)
                    Ellipse(pos=(sx - 4, sy - 4), size=(8, 8))
                    Ellipse(pos=(tx - 4, ty - 4), size=(8, 8))
    
    def update_connections(self):
        """Update connections when devices move"""
        self.schedule_connection_update()
    
    def edit_device(self, device):
        """Open device editor"""
        if hasattr(self.app_instance, 'open_device_editor'):
            self.app_instance.open_device_editor(device)
    
    def delete_selected(self):
        """Delete selected device with animation"""
        if self.selected_device:
            device_id = self.selected_device.device.id
            widget = self.selected_device
            
            # Animate removal
            anim = Animation(opacity=0, _scale=0.5, duration=0.3, t='in_cubic')
            anim.bind(on_complete=lambda *args: self._complete_deletion(device_id, widget))
            anim.start(widget)
    
    def _complete_deletion(self, device_id, widget):
        """Complete device deletion after animation"""
        # Remove connections
        conns_to_delete = []
        for conn_id, conn in self.connections.items():
            if conn.source_id == device_id or conn.target_id == device_id:
                conns_to_delete.append(conn_id)
        
        for conn_id in conns_to_delete:
            del self.connections[conn_id]
        
        # Update other devices' connections
        for device in self.devices.values():
            device.remove_connection(device_id)
        
        # Remove widget and device
        self.remove_widget(widget)
        del self.devices[device_id]
        del self.device_widgets[device_id]
        
        self.selected_device = None
        self.draw_connections()
    
    def clear_canvas(self):
        """Clear all devices with animation"""
        # Animate all widgets disappearing
        for widget in list(self.device_widgets.values()):
            anim = Animation(opacity=0, duration=0.3)
            anim.bind(on_complete=lambda a, w: self.remove_widget(w))
            anim.start(widget)
        
        # Clear data after animation
        Clock.schedule_once(lambda dt: self._clear_data(), 0.4)
    
    def _clear_data(self):
        """Clear all data structures"""
        self.devices.clear()
        self.connections.clear()
        self.device_widgets.clear()
        self.selected_device = None
        self.draw_connections()
    
    def on_touch_down(self, touch):
        """Handle touch events with smooth interaction"""
        # Check if placing new device
        if hasattr(self.app_instance, 'placing_device_type'):
            device_type = self.app_instance.placing_device_type
            self.add_device(device_type, touch.x, touch.y)
            delattr(self.app_instance, 'placing_device_type')
            return True
        
        # Update temp connection line if in connection mode
        if self.connection_mode and self.connection_start:
            return True
        
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Update temporary connection line"""
        if self.connection_mode and self.connection_start and self.temp_line:
            self.temp_line.points = [
                self.connection_start.x + self.connection_start.width/2,
                self.connection_start.y + self.connection_start.height/2,
                touch.x,
                touch.y
            ]
            return True
        return super().on_touch_move(touch)