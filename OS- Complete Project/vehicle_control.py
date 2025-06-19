from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from threading import Thread, Lock, Event
import time
import random
from queue import Queue, Empty
import logging

@dataclass
class Task:
    name: str
    priority: int  # 0: Emergency, 1: High, 2: Normal
    action: Callable[[], None]

class DrivingMode(Enum):
    MANUAL = "Manual"
    ASSISTED = "Assisted"
    AUTONOMOUS = "Autonomous"

class VehicleControlSystem:
    def __init__(self, logger):
        self.logger = logger
        self.running = False
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.driving_mode = DrivingMode.MANUAL
        self.assisted_speed = 0.0
        self.is_emergency_braking = False
        self.task_queue = Queue()
        self.task_thread = None
        self.metrics_thread = None
        self.speed_thread = None
        self.stop_event = Event()
        self.lock = Lock()  # Add lock for thread safety
        self.max_queue_size = 100  # Limit queue size to prevent overload
        
        # Speed control parameters - adjusted for smoother transitions
        self.acceleration_rate = 0.3  # km/h per update (reduced from 2.0)
        self.deceleration_rate = 0.3  # km/h per update (reduced from 3.0)
        self.emergency_deceleration_rate = 0.5  # km/h per update (reduced from 10.0)
        self.last_speed_update = time.time()
        self.speed_update_interval = 0.05  # 50ms (reduced from 0.1)
        
        # Initialize metrics with stable values
        self.metrics = {
            "rpm": 800,  # Idle RPM
            "temp": 90,  # Normal operating temperature
            "voltage": 12.0,  # Normal battery voltage
            "oil": 45,  # Normal oil pressure
            "fuel": 100.0,  # Full fuel tank
            "current_speed": 0.0
        }
        
        # Add smoothing factors for gradual changes
        self.last_metrics_update = time.time()
        self.metrics_update_interval = 0.5  # Update every 500ms
        self.temp_smoothing = 0.1  # Slower temperature changes
        self.voltage_smoothing = 0.05  # Very slow voltage changes
        self.oil_smoothing = 0.15  # Moderate oil pressure changes
            
    def start(self):
        """Start the control system with improved thread safety"""
        with self.lock:
            if not self.running:
                self.running = True
                self.stop_event.clear()
                
                # Start task processing thread
                self.task_thread = Thread(target=self._process_tasks, daemon=True)
                self.task_thread.start()
                
                # Start metrics update thread
                self.metrics_thread = Thread(target=self._update_metrics, daemon=True)
                self.metrics_thread.start()
                
                # Start speed control thread
                self.speed_thread = Thread(target=self._update_speed, daemon=True)
                self.speed_thread.start()
                
                self.logger.log("Vehicle control system started", "info")
                
    def stop(self):
        """Stop the control system with proper cleanup"""
        with self.lock:
            if self.running:
                self.running = False
                self.stop_event.set()
                
                # Clear task queue
                while not self.task_queue.empty():
                    try:
                        self.task_queue.get_nowait()
                    except Empty:
                        break
                        
                # Wait for threads to finish
                if self.task_thread and self.task_thread.is_alive():
                    self.task_thread.join(timeout=1.0)
                if self.metrics_thread and self.metrics_thread.is_alive():
                    self.metrics_thread.join(timeout=1.0)
                if self.speed_thread and self.speed_thread.is_alive():
                    self.speed_thread.join(timeout=1.0)
                    
                self.logger.log("Vehicle control system stopped", "info")
                
    def _update_speed(self):
        """Update speed with smooth transitions"""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - self.last_speed_update >= self.speed_update_interval:
                    with self.lock:
                        if self.is_emergency_braking:
                            # Emergency braking - gradual deceleration
                            deceleration = min(self.emergency_deceleration_rate, self.current_speed * 0.1)
                            self.current_speed = max(0, self.current_speed - deceleration)
                            if self.current_speed == 0:
                                self.is_emergency_braking = False
                        else:
                            speed_diff = self.target_speed - self.current_speed
                            
                            if abs(speed_diff) > 0.1:  # Only update if difference is significant
                                # Calculate acceleration/deceleration based on speed difference
                                if speed_diff > 0:
                                    # Accelerating
                                    change = min(self.acceleration_rate, speed_diff * 0.05)
                                else:
                                    # Decelerating
                                    change = max(-self.deceleration_rate, speed_diff * 0.05)
                                    
                                # Apply speed change
                                self.current_speed += change
                                
                                # Ensure speed stays within limits
                                self.current_speed = max(0, min(self.current_speed, 180))
                    
                        # Update metrics
                        self.metrics["current_speed"] = self.current_speed
                                
                    self.last_speed_update = current_time
                    
                # Sleep to prevent CPU overuse
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.log(f"Error updating speed: {str(e)}", "error")
                time.sleep(0.1)  # Longer sleep on error
            
    def add_task(self, task: Task):
        """Add a task to the queue with size limit"""
        if self.task_queue.qsize() < self.max_queue_size:
            self.task_queue.put(task)
        else:
            self.logger.log("Task queue full, dropping task", "warning")
        
    def _process_tasks(self):
        """Process tasks with improved error handling and rate limiting"""
        while not self.stop_event.is_set():
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=0.1)
                
                # Execute task
                try:
                    task.action()
                except Exception as e:
                    self.logger.log(f"Error executing task {task.name}: {str(e)}", "error")
                    
                # Rate limiting
                time.sleep(0.01)  # 10ms delay between tasks
                
            except Empty:
                # No tasks, sleep briefly
                time.sleep(0.05)
            except Exception as e:
                self.logger.log(f"Error in task processing: {str(e)}", "error")
                time.sleep(0.1)  # Longer sleep on error
                
    def _update_metrics(self):
        """Update vehicle metrics with improved stability and realistic values"""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - self.last_metrics_update >= self.metrics_update_interval:
                    with self.lock:
                        # Update RPM based on speed with realistic ranges
                        base_rpm = 800  # Idle RPM
                        speed_factor = self.current_speed * 50  # RPM increases with speed
                        self.metrics["rpm"] = int(base_rpm + speed_factor)
                        
                        # Update temperature with gradual changes
                        target_temp = 90 + (self.metrics["rpm"] / 6000) * 20  # Temperature increases with RPM
                        current_temp = self.metrics["temp"]
                        self.metrics["temp"] = current_temp + (target_temp - current_temp) * self.temp_smoothing
                        
                        # Update voltage with very gradual changes
                        target_voltage = 12.0 - (self.metrics["rpm"] / 6000) * 0.5  # Voltage drops slightly with RPM
                        current_voltage = self.metrics["voltage"]
                        self.metrics["voltage"] = current_voltage + (target_voltage - current_voltage) * self.voltage_smoothing
                        
                        # Update oil pressure with moderate changes
                        target_oil = 45 + (self.metrics["rpm"] / 6000) * 15  # Oil pressure increases with RPM
                        current_oil = self.metrics["oil"]
                        self.metrics["oil"] = current_oil + (target_oil - current_oil) * self.oil_smoothing
                        
                    self.last_metrics_update = current_time
                    
                # Sleep to prevent CPU overuse
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.log(f"Error updating metrics: {str(e)}", "error")
                time.sleep(0.5)  # Longer sleep on error
                
    def set_target_speed(self, speed: float):
        """Set target speed with thread safety"""
        with self.lock:
            if not self.is_emergency_braking:
                self.target_speed = max(0, min(speed, 180))  # Limit speed to 0-180 km/h
                if speed == 0:
                    # Immediate deceleration when setting speed to 0
                    self.current_speed = 0
                    self.metrics["current_speed"] = 0
            
    def set_current_speed(self, speed: float):
        """Set current speed with thread safety"""
        with self.lock:
            if not self.is_emergency_braking:
                self.current_speed = max(0, min(speed, 180))
                self.metrics["current_speed"] = self.current_speed
                
    def set_driving_mode(self, mode: DrivingMode):
        """Set driving mode with thread safety"""
        with self.lock:
            self.driving_mode = mode
            if mode == DrivingMode.ASSISTED:
                self.assisted_speed = self.current_speed
                
    def emergency_brake(self):
        """Emergency brake with thread safety"""
        with self.lock:
            self.is_emergency_braking = True
            self.target_speed = 0
            self.current_speed = 0
            self.metrics["current_speed"] = 0
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics with thread safety"""
        with self.lock:
            return self.metrics.copy()
            
    def set_fuel_level(self, level: float):
        """Set fuel level with thread safety"""
        with self.lock:
            self.metrics["fuel"] = max(0, min(level, 100))  # Limit fuel to 0-100% 