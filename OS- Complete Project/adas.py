from vehicle_control import Task, VehicleControlSystem
from typing import Optional, Dict, Any
import time
import math
from threading import Lock

class ADAS:
    def __init__(self, control_system: VehicleControlSystem):
        self.control_system = control_system
        self.airbag_deployed = False
        self.acc_active = False
        self.lka_active = False
        self.collision_warning_active = False
        self.last_safety_check = time.time()
        self.safety_check_interval = 0.1  # 100ms
        self.lock = Lock()  # Add lock for thread safety
        
        # Safety thresholds
        self.speed_threshold = 30  # km/h
        self.deceleration_threshold = 5  # km/h/s
        self.last_speed = 0
        self.last_check_time = time.time()
        
    def initialize_adaptive_cruise_control(self):
        """Initialize ACC with improved safety checks and thread safety"""
        with self.lock:
            if not self.acc_active:
                def acc_action():
                    try:
                        metrics = self.control_system.get_metrics()
                        current_speed = metrics["current_speed"]
                        
                        # Maintain safe distance and speed
                        if current_speed > 0:
                            # Simulate distance to vehicle ahead
                            distance = self._simulate_distance()
                            if distance < 50:  # Less than 50m
                                # Gradually reduce speed
                                target_speed = current_speed * 0.8
                                self.control_system.set_target_speed(target_speed)
                                self.control_system.logger.log(
                                    f"ACC: Reducing speed to maintain safe distance", "warning")
                            else:
                                # Resume normal speed
                                self.control_system.set_target_speed(
                                    self.control_system.assisted_speed)
                                
                    except Exception as e:
                        self.control_system.logger.log(
                            f"ACC error: {str(e)}", "error")
                        self.acc_active = False
                        
                task = Task("Adaptive Cruise Control", 1, acc_action)
                self.control_system.add_task(task)
                self.acc_active = True
                self.control_system.logger.log("ACC activated", "info")
            
    def initialize_lane_keeping_assist(self):
        """Initialize LKA with improved lane detection and thread safety"""
        with self.lock:
            if not self.lka_active:
                def lka_action():
                    try:
                        # Simulate lane position
                        lane_position = self._simulate_lane_position()
                        
                        if abs(lane_position) > 0.5:  # Drifting from center
                            # Simulate steering correction
                            correction = -lane_position * 0.1
                            self.control_system.logger.log(
                                f"LKA: Correcting steering by {correction:.2f} degrees")
                            
                    except Exception as e:
                        self.control_system.logger.log(
                            f"LKA error: {str(e)}", "error")
                        self.lka_active = False
                        
                task = Task("Lane Keeping Assist", 1, lka_action)
                self.control_system.add_task(task)
                self.lka_active = True
                self.control_system.logger.log("LKA activated", "info")
            
    def emergency_braking(self):
        """Enhanced emergency braking with collision detection and thread safety"""
        with self.lock:
            def emergency_action():
                try:
                    metrics = self.control_system.get_metrics()
                    current_speed = metrics["current_speed"]
                    
                    if current_speed > self.speed_threshold:
                        # Calculate deceleration
                        current_time = time.time()
                        time_diff = current_time - self.last_check_time
                        speed_diff = current_speed - self.last_speed
                        deceleration = speed_diff / time_diff if time_diff > 0 else 0
                        
                        if abs(deceleration) > self.deceleration_threshold:
                            self.control_system.logger.log(
                                "EMERGENCY: Sudden deceleration detected!", "warning")
                            self.deploy_airbags()
                            
                    self.control_system.emergency_brake()
                    self.last_speed = current_speed
                    self.last_check_time = time.time()
                    
                except Exception as e:
                    self.control_system.logger.log(
                        f"Emergency braking error: {str(e)}", "error")
                    
            task = Task("Emergency Braking", 0, emergency_action)
            self.control_system.add_task(task)
        
    def deploy_airbags(self):
        """Enhanced airbag deployment with safety checks and thread safety"""
        with self.lock:
            if not self.airbag_deployed:
                def airbag_action():
                    try:
                        self.control_system.logger.log(
                            "AIRBAG: Deploying airbags for passenger safety!", "warning")
                        self.airbag_deployed = True
                        
                        # Emergency stop the vehicle
                        self.control_system.emergency_brake()
                        self.control_system.set_current_speed(0)
                        self.control_system.set_target_speed(0)
                        
                        # Prevent speed from increasing
                        self.control_system.is_emergency_braking = True
                        
                        # Simulate post-crash safety systems
                        self._activate_post_crash_safety()
                        
                    except Exception as e:
                        self.control_system.logger.log(
                            f"Airbag deployment error: {str(e)}", "error")
                        
                task = Task("Airbag Deployment", 0, airbag_action)
                self.control_system.add_task(task)
            
    def reset_airbags(self):
        """Reset airbag system with safety checks and thread safety"""
        with self.lock:
            if self.airbag_deployed:
                def reset_action():
                    try:
                        # Check if it's safe to reset
                        if self._is_safe_to_reset():
                            self.control_system.logger.log(
                                "AIRBAG: Resetting airbag system", "info")
                            self.airbag_deployed = False
                            # Allow speed control again
                            self.control_system.is_emergency_braking = False
                        else:
                            self.control_system.logger.log(
                                "AIRBAG: Cannot reset - safety conditions not met", "warning")
                            
                    except Exception as e:
                        self.control_system.logger.log(
                            f"Airbag reset error: {str(e)}", "error")
                        
                task = Task("Airbag Reset", 2, reset_action)
                self.control_system.add_task(task)
            
    def check_collision_risk(self):
        """Enhanced collision risk detection with thread safety"""
        with self.lock:
            def collision_check():
                try:
                    metrics = self.control_system.get_metrics()
                    current_speed = metrics["current_speed"]
                    
                    # Check for sudden deceleration
                    if current_speed > self.speed_threshold:
                        time_diff = time.time() - self.last_check_time
                        speed_diff = current_speed - self.last_speed
                        deceleration = speed_diff / time_diff if time_diff > 0 else 0
                        
                        if abs(deceleration) > self.deceleration_threshold:
                            self.control_system.logger.log(
                                "WARNING: Sudden deceleration detected!", "warning")
                            self.deploy_airbags()
                            
                    # Update last values
                    self.last_speed = current_speed
                    self.last_check_time = time.time()
                    
                except Exception as e:
                    self.control_system.logger.log(
                        f"Collision check error: {str(e)}", "error")
                    
            task = Task("Collision Detection", 1, collision_check)
            self.control_system.add_task(task)
        
    def _simulate_distance(self) -> float:
        """Simulate distance to vehicle ahead"""
        # Simulate varying distance
        return 30 + 20 * math.sin(time.time())
        
    def _simulate_lane_position(self) -> float:
        """Simulate vehicle position relative to lane center"""
        # Simulate lane position (-1 to 1, where 0 is center)
        return math.sin(time.time() * 0.5)
        
    def _activate_post_crash_safety(self):
        """Activate post-crash safety systems with error handling"""
        try:
            # Simulate various safety systems
            self.control_system.logger.log("Activating post-crash safety systems", "info")
            
            # Ensure vehicle is completely stopped
            self.control_system.set_current_speed(0)
            self.control_system.set_target_speed(0)
            
            # Simulate hazard lights
            self.control_system.logger.log("Hazard lights activated", "info")
            
            # Simulate door unlock
            self.control_system.logger.log("Doors unlocked for emergency exit", "info")
            
        except Exception as e:
            self.control_system.logger.log(f"Error in post-crash safety: {str(e)}", "error")
            
    def _is_safe_to_reset(self) -> bool:
        """Check if it's safe to reset airbags with comprehensive checks"""
        try:
            metrics = self.control_system.get_metrics()
            
            # Check vehicle speed
            if metrics["current_speed"] > 0:
                return False
                
            # Check engine temperature
            if metrics["temp"] > 100:  # Too hot
                return False
                
            # Check battery voltage
            if metrics["voltage"] < 11.0:  # Low battery
                return False
                
            # Check if emergency systems are active
            if self.control_system.is_emergency_braking:
                return False
                
            return True
            
        except Exception as e:
            self.control_system.logger.log(f"Error checking safety conditions: {str(e)}", "error")
            return False  # Default to unsafe if check fails 