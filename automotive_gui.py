import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk  
from vehicle_control import VehicleControlSystem, DrivingMode
from adas import ADAS
from infotainment import InfotainmentSystem
from logger import VehicleLogger
from threading import Thread, Lock
import time
from tkinter import filedialog
import os
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import pygame

@dataclass
class MapCache:
    """Cache for map data to improve performance"""
    map_type: str
    width: int
    height: int
    elements: list

class ModernAutomotiveGUI:
    def __init__(self, root): 
        self.root = root
        self.root.title("Advanced Automotive System")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize logger
        self.logger = VehicleLogger()
        
        # Initialize systems
        self.control_system = VehicleControlSystem(self.logger)
        self.adas = ADAS(self.control_system)
        self.infotainment = InfotainmentSystem(self.control_system)
        
        # Initialize state management
        self.state_lock = Lock()
        self.map_cache: Optional[MapCache] = None
        self.is_loading = False
        
        # Setup GUI
        self.setup_gui()
        
        # Start systems
        self.control_system.start()
        self.start_metrics_update()
        
        # Add tooltips
        self.setup_tooltips()
        
    def setup_tooltips(self):
        """Setup tooltips for various controls"""
        self.create_tooltip(self.speed_entry, "Enter target speed (0-180 km/h)")
        self.create_tooltip(self.mode_menu, "Select driving mode")
        self.create_tooltip(self.acc_switch, "Enable/disable adaptive cruise control")
        self.create_tooltip(self.lka_switch, "Enable/disable lane keeping assist")
        
    def create_tooltip(self, widget, text):
        """Create a tooltip for a given widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, justify='left',
                           background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
                
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            
        widget.bind('<Enter>', show_tooltip)
        
    def show_loading(self, show: bool):
        """Show/hide loading indicator"""
        if show:
            self.is_loading = True
            self.loading_label = ctk.CTkLabel(self.root, text="Loading...",
                                            font=("Arial", 14, "bold"))
            self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.is_loading = False
            if hasattr(self, 'loading_label'):
                self.loading_label.destroy()
                
    def validate_speed_input(self, speed_str: str) -> Optional[float]:
        """Validate speed input"""
        try:
            speed = float(speed_str)
            if 0 <= speed <= 180:
                return speed
            else:
                messagebox.showwarning("Invalid Speed",
                                     "Speed must be between 0 and 180 km/h")
                return None
        except ValueError:
            messagebox.showwarning("Invalid Input",
                                 "Please enter a valid number")
            return None
            
    def set_target_speed(self):
        """Set target speed with validation"""
        if self.emergency_brake_active:
            messagebox.showwarning("Emergency Brake Active",
                                 "Cannot change speed while emergency brake is active")
            return
            
        speed = self.validate_speed_input(self.speed_entry.get())
        if speed is not None:
            self.control_system.set_target_speed(speed)
            self.start_speed_transition(speed)
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(speed))
            
    @lru_cache(maxsize=32)
    def get_map_elements(self, map_type: str, width: int, height: int) -> list:
        """Cache map elements for better performance"""
        elements = []
        if map_type == "City Map":
            # City map elements
            elements.extend([
                ("rect", 0, 0, width, height, "#1a1a1a", ""),  # Background
                # Add other city map elements...
            ])
        elif map_type == "Highway Map":
            # Highway map elements
            elements.extend([
                ("rect", 0, 0, width, height, "#1a1a1a", ""),  # Background
                # Add other highway map elements...
            ])
        else:  # Country Map
            # Country map elements
            elements.extend([
                ("rect", 0, 0, width, height, "#1a1a1a", ""),  # Background
                # Add other country map elements...
            ])
        return elements
        
    def draw_map(self, map_type):
        """Draw a simple map with just the road and points"""
        # Clear all existing elements
        self.nav_canvas.delete("all")
        
        width = self.nav_canvas.winfo_width()
        height = self.nav_canvas.winfo_height()
        
        # Draw simple background
        self.nav_canvas.create_rectangle(0, 0, width, height, fill="#1a1a1a", outline="", tags="map")
        
        # Draw the road
        road_width = 40
        road_y = height/2
        self.nav_canvas.create_rectangle(10, road_y-road_width/2, width-10, road_y+road_width/2,
                                       fill="#333333", outline="#666666", width=2, tags="map")
        
        # Draw road markings
        for i in range(10, width-10, 40):
            self.nav_canvas.create_rectangle(i, road_y-5, i+20, road_y+5,
                                           fill="#ffffff", outline="", tags="map")
        
        # Draw start and end points
        start_radius = 25
        self.nav_canvas.create_oval(20, road_y-start_radius, 20+start_radius*2, road_y+start_radius,
                                   fill="#4CAF50", outline="#45a049", width=2, tags="map")
        self.nav_canvas.create_text(20+start_radius, road_y-start_radius-10,
                                  text="Start", fill="white", font=("Arial", 10, "bold"), tags="map")
        
        end_radius = 25
        self.nav_canvas.create_oval(width-20-end_radius*2, road_y-end_radius,
                                   width-20, road_y+end_radius,
                                   fill="#F44336", outline="#da190b", width=2, tags="map")
        self.nav_canvas.create_text(width-20-end_radius, road_y-end_radius-10,
                                  text="End", fill="white", font=("Arial", 10, "bold"), tags="map")
        
    def select_audio_directory(self):
        """Select audio directory with error handling"""
        try:
            directory = filedialog.askdirectory()
            if directory:
                self.show_loading(True)
                self.infotainment.load_audio_files(directory)
                if self.infotainment.tracks:
                    self.track_label.configure(
                        text=f"Loaded {len(self.infotainment.tracks)} tracks")
                else:
                    self.track_label.configure(text="No audio files found")
        except Exception as e:
            self.logger.log(f"Error loading audio files: {str(e)}", "error")
            messagebox.showerror("Error",
                               "Failed to load audio files. Please try again.")
        finally:
            self.show_loading(False)
            
    def start_metrics_update(self):
        """Start metrics update with improved performance and stability"""
        def update():
            last_update = time.time()
            update_interval = 0.1  # 100ms
            
            while True:
                try:
                    current_time = time.time()
                    if current_time - last_update >= update_interval:
                        with self.state_lock:
                            metrics = self.control_system.get_metrics()
                            # Use after_idle to safely update GUI from thread
                            self.root.after_idle(lambda m=metrics: self.update_gui_metrics(m))
                        last_update = current_time
                    time.sleep(0.01)  # Small sleep to prevent CPU overuse
                except Exception as e:
                    self.logger.log(f"Error in metrics update: {str(e)}", "error")
                    time.sleep(1)  # Longer sleep on error to prevent tight loop
                    
        self.metrics_thread = Thread(target=update, daemon=True)
        self.metrics_thread.start()
        
    def update_gui_metrics(self, metrics: Dict[str, Any]):
        """Update GUI metrics with thread safety and error handling"""
        try:
            if not self.root.winfo_exists():  # Check if window still exists
                return
                
            # Update main tab
            rpm = metrics["rpm"]
            self.rpm_gauge.set(rpm / 6000)
            self.rpm_value.configure(text=f"{rpm} RPM")
            
            # Update speed display
            current_speed = metrics["current_speed"]
            self.speed_label.configure(
                text=f"Current Speed: {current_speed:.1f} km/h")
            
            # Update fuel level with consumption based on speed
            fuel_consumption = (current_speed / 100) * 0.1
            current_fuel = max(0, metrics["fuel"] - fuel_consumption)
            self.control_system.set_fuel_level(current_fuel)
            
            self.fuel_gauge.set(current_fuel / 100)
            self.fuel_value.configure(text=f"{current_fuel:.1f}%")
            
            # Update fuel gauge color based on level
            if current_fuel <= 20:
                self.fuel_gauge.configure(progress_color="#dc3545")
                self.fuel_warning.configure(text="Low Fuel Warning!")
            elif current_fuel <= 50:
                self.fuel_gauge.configure(progress_color="#ffc107")
                self.fuel_warning.configure(text="")
            else:
                self.fuel_gauge.configure(progress_color="#28a745")
                self.fuel_warning.configure(text="")
            
            # Update diagnostics
            self.temp_label.configure(
                text=f"Engine Temperature: {metrics['temp']}°C")
            self.voltage_label.configure(
                text=f"Battery Voltage: {metrics['voltage']:.1f}V")
            self.oil_label.configure(
                text=f"Oil Pressure: {metrics['oil']}psi")
                
        except Exception as e:
            self.logger.log(f"Error updating metrics: {str(e)}", "error")
            
    def on_closing(self):
        """Handle application closing with proper cleanup"""
        try:
            # Stop all systems
            self.control_system.stop()
            
            # Clean up infotainment resources
            if hasattr(self, 'infotainment'):
                self.infotainment.cleanup()
                
            # Stop navigation if running
            if hasattr(self, 'nav_running') and self.nav_running:
                self.nav_running = False
                self.nav_canvas.delete("all")
                
            # Clean up pygame
            if hasattr(self.infotainment, 'pygame'):
                pygame.mixer.quit()
                
            # Stop metrics thread
            if hasattr(self, 'metrics_thread'):
                self.metrics_thread = None
                
            # Log shutdown
            self.logger.log("Application shutting down", "info")
            
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            self.logger.log(f"Error during shutdown: {str(e)}", "error")
            # Force destroy even if there's an error
            self.root.destroy()

    def setup_gui(self):
        # Main container with grid layout
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid weights for better layout
        self.main_container.grid_columnconfigure(0, weight=3)  # Left side (main controls + infotainment)
        self.main_container.grid_columnconfigure(1, weight=2)  # Right side (ADAS + diagnostics)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)
        
        # Create the four main sections
        self.setup_main_controls()  # Top left
        self.setup_adas_controls()  # Top right
        self.setup_infotainment_controls()  # Bottom left
        self.setup_diagnostics_controls()  # Bottom right
        
    def setup_main_controls(self):
        # Main controls frame (top left)
        main_frame = ctk.CTkFrame(self.main_container)
        main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Title
        ctk.CTkLabel(main_frame, text="Vehicle Controls", 
                    font=("Arial", 16, "bold")).pack(pady=5)
        
        # Driving mode selection
        mode_frame = ctk.CTkFrame(main_frame)
        mode_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(mode_frame, text="Driving Mode").pack(side="left", padx=5)
        
        modes = [mode.value for mode in DrivingMode]
        self.mode_var = tk.StringVar(value=DrivingMode.MANUAL.value)
        self.mode_menu = ctk.CTkOptionMenu(mode_frame, values=modes,
                                    variable=self.mode_var,
                                    command=self.change_driving_mode)
        self.mode_menu.pack(side="left", padx=5)
        
        # Speed control
        speed_frame = ctk.CTkFrame(main_frame)
        speed_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(speed_frame, text="Target Speed (km/h):").pack(side="left", padx=5)
        self.speed_entry = ctk.CTkEntry(speed_frame, width=100)
        self.speed_entry.pack(side="left", padx=5)
        self.speed_entry.insert(0, "0")
        
        ctk.CTkButton(speed_frame, text="Set Speed",
                     command=self.set_target_speed).pack(side="left", padx=5)
        
        # Current speed display
        self.speed_label = ctk.CTkLabel(speed_frame, text="Current Speed: 0 km/h",
                                      font=("Arial", 24))
        self.speed_label.pack(side="left", padx=20)
        
        # Engine RPM Gauge
        rpm_frame = ctk.CTkFrame(main_frame)
        rpm_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(rpm_frame, text="Engine RPM").pack()
        self.rpm_gauge = ctk.CTkProgressBar(rpm_frame)
        self.rpm_gauge.pack(fill="x", padx=5, pady=5)
        self.rpm_value = ctk.CTkLabel(rpm_frame, text="0 RPM")
        self.rpm_value.pack()
        
        # Fuel gauge with improved visualization
        fuel_frame = ctk.CTkFrame(main_frame)
        fuel_frame.pack(fill="x", padx=5, pady=5)
        
        # Fuel header with level
        fuel_header = ctk.CTkFrame(fuel_frame)
        fuel_header.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(fuel_header, text="Fuel Level").pack(side="left")
        self.fuel_value = ctk.CTkLabel(fuel_header, text="100%")
        self.fuel_value.pack(side="right")
        
        # Fuel gauge with color indication
        self.fuel_gauge = ctk.CTkProgressBar(fuel_frame)
        self.fuel_gauge.pack(fill="x", padx=5, pady=5)
        self.fuel_gauge.set(1.0)  # Start at 100%
        
        # Fuel warning indicator
        self.fuel_warning = ctk.CTkLabel(fuel_frame, text="", text_color="#dc3545")
        self.fuel_warning.pack(pady=2)
        
    def setup_adas_controls(self):
        # ADAS controls frame (top right)
        adas_frame = ctk.CTkFrame(self.main_container)
        adas_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Title
        ctk.CTkLabel(adas_frame, text="ADAS Features", 
                    font=("Arial", 16, "bold")).pack(pady=5)
        
        # ACC Frame
        acc_frame = ctk.CTkFrame(adas_frame)
        acc_frame.pack(fill="x", padx=5, pady=5)
        
        self.acc_switch = ctk.CTkSwitch(acc_frame, text="Adaptive Cruise Control",
                                      command=self.toggle_acc)
        self.acc_switch.pack(side="left", padx=5)
        
        # LKA Frame
        lka_frame = ctk.CTkFrame(adas_frame)
        lka_frame.pack(fill="x", padx=5, pady=5)
        
        self.lka_switch = ctk.CTkSwitch(lka_frame, text="Lane Keeping Assist",
                                      command=self.toggle_lka)
        self.lka_switch.pack(side="left", padx=5)
        
        # Airbag System Frame
        airbag_frame = ctk.CTkFrame(adas_frame)
        airbag_frame.pack(fill="x", padx=5, pady=5)
        
        # Airbag Status
        self.airbag_status = ctk.CTkLabel(airbag_frame, text="Airbag Status: Ready",
                                        font=("Arial", 12))
        self.airbag_status.pack(side="left", padx=5)
        
        # Airbag Controls
        airbag_controls = ctk.CTkFrame(airbag_frame)
        airbag_controls.pack(side="right", padx=5)
        
        self.deploy_airbag_btn = ctk.CTkButton(airbag_controls, text="Deploy Airbags",
                                             command=self.deploy_airbags,
                                             fg_color="#dc3545",
                                             hover_color="#c82333")
        self.deploy_airbag_btn.pack(side="left", padx=2)
        
        self.reset_airbag_btn = ctk.CTkButton(airbag_controls, text="Reset Airbags",
                                            command=self.reset_airbags,
                                            fg_color="#28a745",
                                            hover_color="#218838")
        self.reset_airbag_btn.pack(side="left", padx=2)
        
        # Emergency Brake Frame
        emergency_frame = ctk.CTkFrame(adas_frame)
        emergency_frame.pack(fill="x", padx=5, pady=5)
        
        # Emergency Brake Button
        self.emergency_brake_btn = ctk.CTkButton(emergency_frame, text="Emergency Brake",
                     command=self.emergency_brake,
                     fg_color="red", hover_color="darkred")
        self.emergency_brake_btn.pack(side="left", padx=5, pady=10)
        
        # Reset Emergency Brake Button
        self.reset_emergency_brake_btn = ctk.CTkButton(emergency_frame, text="Reset Emergency Brake",
                     command=self.reset_emergency_brake,
                     fg_color="#28a745", hover_color="#218838",
                     state="disabled")
        self.reset_emergency_brake_btn.pack(side="left", padx=5, pady=10)
        
    def setup_infotainment_controls(self):
        # Infotainment frame (bottom left)
        infotainment_frame = ctk.CTkFrame(self.main_container)
        infotainment_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Title
        ctk.CTkLabel(infotainment_frame, text="Infotainment System", 
                    font=("Arial", 16, "bold")).pack(pady=5)
        
        # Media player
        media_frame = ctk.CTkFrame(infotainment_frame)
        media_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(media_frame, text="Play",
                     command=self.toggle_play).pack(side="left", padx=5)
        ctk.CTkButton(media_frame, text="Pause",
                     command=self.infotainment.pause_media).pack(side="left", padx=5)
        ctk.CTkButton(media_frame, text="Next",
                     command=self.infotainment.next_track).pack(side="left", padx=5)
        
        # Track info
        self.track_label = ctk.CTkLabel(media_frame, text="Track: 1")
        self.track_label.pack(side="left", padx=20)
        
        # Audio file selection
        audio_frame = ctk.CTkFrame(infotainment_frame)
        audio_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(audio_frame, text="Select Audio Directory",
                     command=self.select_audio_directory).pack(pady=5)
        
        # Navigation
        nav_frame = ctk.CTkFrame(infotainment_frame)
        nav_frame.pack(fill="x", padx=5, pady=5)
        
        # Enhanced navigation display
        self.setup_enhanced_navigation(nav_frame)
        
    def setup_enhanced_navigation(self, parent_frame):
        # Navigation title with modern styling
        nav_title_frame = ctk.CTkFrame(parent_frame)
        nav_title_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(nav_title_frame, text="Navigation System", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=5)
        
        # Add navigation control button with improved styling
        self.nav_running = False
        self.nav_control_btn = ctk.CTkButton(nav_title_frame, text="Start Navigation",
                                           command=self.toggle_navigation,
                                           width=120,
                                           fg_color="#2196F3",
                                           hover_color="#1976D2")
        self.nav_control_btn.pack(side="right", padx=5)
        
        # Navigation controls with improved layout
        nav_controls_frame = ctk.CTkFrame(parent_frame)
        nav_controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Route selection with enhanced options
        route_frame = ctk.CTkFrame(nav_controls_frame)
        route_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(route_frame, text="Route:").pack(side="left", padx=5)
        self.route_var = tk.StringVar(value="Home → Office")
        route_menu = ctk.CTkOptionMenu(route_frame, 
                                     values=["Home → Office", "Office → Mall", "Mall → Home", "Custom Route"],
                                     variable=self.route_var, 
                                     command=self.change_route)
        route_menu.pack(side="left", padx=5)
        
        # Map selection with visual indicators
        map_frame = ctk.CTkFrame(nav_controls_frame)
        map_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(map_frame, text="Map:").pack(side="left", padx=5)
        self.map_var = tk.StringVar(value="City Map")
        map_menu = ctk.CTkOptionMenu(map_frame, 
                                   values=["City Map", "Highway Map", "Country Map"],
                                   variable=self.map_var, 
                                   command=self.change_map)
        map_menu.pack(side="left", padx=5)
        
        # Enhanced navigation display with better resolution
        self.nav_canvas = tk.Canvas(parent_frame, height=200, bg="#1a1a1a", highlightthickness=0)
        self.nav_canvas.pack(fill="x", padx=5, pady=5)
        
        # Navigation info panel
        info_frame = ctk.CTkFrame(parent_frame)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        # ETA and traffic info with improved layout
        self.eta_label = ctk.CTkLabel(info_frame, text="ETA: 25 minutes", font=("Arial", 12))
        self.eta_label.pack(side="left", padx=5)
        
        self.traffic_label = ctk.CTkLabel(info_frame, text="Traffic: Moderate", font=("Arial", 12))
        self.traffic_label.pack(side="right", padx=5)
        
        # Initialize car position
        self.car_x = 20 + 25  # start_radius
        self.car_speed = 0
        self.car_target_speed = 5
        self.car_acceleration = 0.1
        self.emergency_brake_active = False
        
        # Draw initial map and route
        self.draw_map(self.map_var.get())
        self.draw_route(self.route_var.get())
        
    def draw_route(self, route):
        """Handle route changes - simplified to just update ETA"""
        try:
            # Update ETA based on route
            if route == "Home → Office":
                self.eta_label.configure(text="ETA: 25 minutes")
            elif route == "Office → Mall":
                self.eta_label.configure(text="ETA: 15 minutes")
            elif route == "Mall → Home":
                self.eta_label.configure(text="ETA: 35 minutes")
            else:  # Custom Route
                self.eta_label.configure(text="ETA: Calculating...")
                
            # Update traffic
            traffic = random.choice(["Light", "Moderate", "Heavy"])
            self.traffic_label.configure(text=f"Traffic: {traffic}")
            
        except Exception as e:
            self.logger.log(f"Error changing route: {str(e)}", "error")
        
    def animate_car(self):
        """Animate the car with simple graphics"""
        if not hasattr(self, 'car_x') or not self.nav_running:
            # Clean up car elements when stopping
            self.nav_canvas.delete("car")
            return
            
        width = self.nav_canvas.winfo_width()
        height = self.nav_canvas.winfo_height()
        road_y = height/2
        
        # Clear previous car
        self.nav_canvas.delete("car")
        
        # Gradually increase speed
        if self.car_speed < self.car_target_speed:
            self.car_speed += self.car_acceleration
        
        # Draw simple car
        car_y = road_y - 15
        
        # Car body
        self.nav_canvas.create_rectangle(self.car_x, car_y, self.car_x+40, car_y+30,
                                       fill="#2196F3", outline="#1976D2", width=2, tags="car")
        
        # Car windows
        self.nav_canvas.create_rectangle(self.car_x+5, car_y+5, self.car_x+35, car_y+15,
                                       fill="#1976D2", outline="#1565C0", width=1, tags="car")
        
        # Car wheels
        wheel_radius = 5
        # Front wheels
        self.nav_canvas.create_oval(self.car_x+5, car_y+25, self.car_x+15, car_y+35,
                                  fill="#424242", outline="#212121", width=2, tags="car")
        # Rear wheels
        self.nav_canvas.create_oval(self.car_x+25, car_y+25, self.car_x+35, car_y+35,
                                  fill="#424242", outline="#212121", width=2, tags="car")
        
        # Move car
        self.car_x += self.car_speed
        
        # Check if car reached the end
        if self.car_x < width-20-50:  # 50 is the end radius * 2
            self.root.after(20, self.animate_car)
        else:
            # Reset car position and speed
            self.car_x = 20 + 25  # start_radius
            self.car_speed = 0
            if self.nav_running:
                self.root.after(1000, self.animate_car)
            else:
                # Clean up car elements when stopping
                self.nav_canvas.delete("car")
        
    def toggle_navigation(self):
        """Toggle navigation state and update button text"""
        try:
            self.nav_running = not self.nav_running
            if self.nav_running:
                self.nav_control_btn.configure(text="Stop Navigation")
                # Initialize car position
                self.car_x = 20 + 25  # start_radius
                self.car_speed = 0
                self.car_target_speed = 5
                self.animate_car()
            else:
                self.nav_control_btn.configure(text="Start Navigation")
                self.nav_running = False
                
        except Exception as e:
            self.logger.log(f"Error toggling navigation: {str(e)}", "error")
            self.nav_running = False
            self.nav_control_btn.configure(text="Start Navigation")

    def emergency_brake(self):
        # Set emergency brake flag
        self.emergency_brake_active = True
        
        # Call the ADAS emergency braking function
        self.adas.emergency_braking()
        
        # Let the vehicle control system handle the emergency braking
        self.control_system.emergency_brake()
        
        # Reset car position in navigation if it's running
        if hasattr(self, 'car_x'):
            self.car_x = 20
            self.car_speed = 0
            self.car_target_speed = 0
        
        # Prevent speed from increasing while emergency brake is active
        self.control_system.set_target_speed(0)
        
        # Disable emergency brake button and enable reset button
        self.emergency_brake_btn.configure(state="disabled")
        self.reset_emergency_brake_btn.configure(state="normal")
        
    def reset_emergency_brake(self):
        self.emergency_brake_active = False
        # Re-enable emergency brake button and disable reset button
        self.emergency_brake_btn.configure(state="normal")
        self.reset_emergency_brake_btn.configure(state="disabled")
        
    def change_map(self, map_type):
        """Change the map type - simplified to just redraw the basic map"""
        self.draw_map(map_type)
        
    def deploy_airbags(self):
        """Handle airbag deployment"""
        self.adas.deploy_airbags()
        self.airbag_status.configure(text="Airbag Status: Deployed",
                                   text_color="#dc3545")
        self.deploy_airbag_btn.configure(state="disabled")
        self.reset_airbag_btn.configure(state="normal")
        
    def reset_airbags(self):
        """Handle airbag reset"""
        self.adas.reset_airbags()
        self.airbag_status.configure(text="Airbag Status: Ready",
                                   text_color="#28a745")
        self.deploy_airbag_btn.configure(state="normal")
        self.reset_airbag_btn.configure(state="disabled")

    def change_route(self, route):
        """Handle route changes - simplified to just update ETA"""
        try:
            # Update ETA based on route
            if route == "Home → Office":
                self.eta_label.configure(text="ETA: 25 minutes")
            elif route == "Office → Mall":
                self.eta_label.configure(text="ETA: 15 minutes")
            elif route == "Mall → Home":
                self.eta_label.configure(text="ETA: 35 minutes")
            else:  # Custom Route
                self.eta_label.configure(text="ETA: Calculating...")
                
            # Update traffic
            traffic = random.choice(["Light", "Moderate", "Heavy"])
            self.traffic_label.configure(text=f"Traffic: {traffic}")
            
        except Exception as e:
            self.logger.log(f"Error changing route: {str(e)}", "error")

    def change_driving_mode(self, mode):
        self.control_system.set_driving_mode(DrivingMode(mode))
        
    def toggle_acc(self):
        if self.acc_switch.get():
            self.adas.initialize_adaptive_cruise_control()
        
    def toggle_lka(self):
        if self.lka_switch.get():
            self.adas.initialize_lane_keeping_assist()
            
    def toggle_play(self):
        if not self.infotainment.is_playing:
            self.infotainment.play_media()
            self.track_label.configure(text=f"Track: {self.infotainment.current_track + 1}")
            
    def start_speed_transition(self, target_speed):
        if self.emergency_brake_active:
            return
            
        current_speed = self.control_system.get_metrics()["current_speed"]
        speed_diff = target_speed - current_speed
        
        if abs(speed_diff) > 0.1:  # Continue until we're very close to target
            # Let the vehicle control system handle the speed transition
            self.control_system.set_target_speed(target_speed)
            
            # Update the display
            self.speed_label.configure(text=f"Current Speed: {current_speed:.1f} km/h")
            
            # Continue monitoring the transition
            self.root.after(50, lambda: self.start_speed_transition(target_speed))
        else:
            # Ensure we reach exactly the target speed
            self.control_system.set_current_speed(target_speed)
            self.speed_label.configure(text=f"Current Speed: {target_speed:.1f} km/h")

    def setup_diagnostics_controls(self):
        """Setup the diagnostics panel"""
        # Diagnostics frame (bottom right)
        diagnostics_frame = ctk.CTkFrame(self.main_container)
        diagnostics_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Title
        ctk.CTkLabel(diagnostics_frame, text="Vehicle Diagnostics", 
                    font=("Arial", 16, "bold")).pack(pady=5)
        
        # Engine metrics
        metrics_frame = ctk.CTkFrame(diagnostics_frame)
        metrics_frame.pack(fill="x", padx=5, pady=5)
        
        # Create labels for various metrics
        self.temp_label = ctk.CTkLabel(metrics_frame, text="Engine Temperature: --°C")
        self.temp_label.pack(pady=2)
        
        self.voltage_label = ctk.CTkLabel(metrics_frame, text="Battery Voltage: --V")
        self.voltage_label.pack(pady=2)
        
        self.oil_label = ctk.CTkLabel(metrics_frame, text="Oil Pressure: --psi")
        self.oil_label.pack(pady=2)
        
        # System Log Section
        log_section = ctk.CTkFrame(diagnostics_frame)
        log_section.pack(fill="both", expand=True, padx=5, pady=5)
        
        # System Messages Label
        ctk.CTkLabel(log_section, text="System Messages", 
                    font=("Arial", 12, "bold")).pack(pady=2)
        
        # System Log Text Box
        self.log_text = ctk.CTkTextbox(log_section, height=100)
        self.log_text.pack(fill="x", padx=5, pady=2)
        
        # User Notes Label
        ctk.CTkLabel(log_section, text="User Notes", 
                    font=("Arial", 12, "bold")).pack(pady=2)
        
        # User Notes Text Box
        self.user_notes = ctk.CTkTextbox(log_section, height=100)
        self.user_notes.pack(fill="x", padx=5, pady=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernAutomotiveGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 