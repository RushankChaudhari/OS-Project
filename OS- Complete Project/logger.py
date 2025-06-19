import logging
from datetime import datetime
import os

class VehicleLogger:
    def __init__(self):
        # Get the current directory (OS folder)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create logs directory in the OS folder if it doesn't exist
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

        # Configure logging
        self.logger = logging.getLogger('VehicleLogger')
        self.logger.setLevel(logging.INFO)

        # Create file handler with log file in the OS folder
        log_file = os.path.join(self.logs_dir, f'vehicle_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter with more detailed information
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log the initialization
        self.logger.info(f"Logger initialized. Log file: {log_file}")

    def log(self, message: str, level: str = "info"):
        """Log a message with the specified level"""
        if level.lower() == "error":
            self.logger.error(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
            
    def get_latest_log_file(self) -> str:
        """Get the path of the most recent log file"""
        try:
            log_files = [f for f in os.listdir(self.logs_dir) if f.endswith('.log')]
            if not log_files:
                return None
            latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(self.logs_dir, x)))
            return os.path.join(self.logs_dir, latest_log)
        except Exception as e:
            self.logger.error(f"Error getting latest log file: {str(e)}")
            return None 