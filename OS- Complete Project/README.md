# Advanced Automotive System GUI

A modern, feature-rich automotive system simulation with a graphical user interface. This application demonstrates various vehicle control systems, ADAS features, and infotainment capabilities.

## Features

### Vehicle Controls
- Real-time speed control (0-180 km/h)
- Multiple driving modes (Manual, Assisted, Autonomous)
- RPM and speed monitoring with smooth transitions
- Dynamic fuel level tracking with color-coded warnings
- Emergency braking system with visual feedback

### ADAS (Advanced Driver Assistance Systems)
- Adaptive Cruise Control (ACC)
- Lane Keeping Assist (LKA)
- Collision Detection
- Airbag System with deployment simulation
- Emergency Braking with automatic speed control
- Visual feedback for system status

### Infotainment System
- Media player with play/pause/next controls
- Audio file support with directory selection
- Enhanced navigation system with:
  - Multiple route options (Home → Office, Office → Mall, etc.)
  - Different map views (City, Highway, Country)
  - Real-time traffic updates
  - Dynamic ETA calculation
  - Animated vehicle movement
- Visual map representation with road markings

### Vehicle Diagnostics
- Engine temperature monitoring
- Battery voltage tracking
- Oil pressure monitoring
- Real-time system logs with severity levels
- User notes section
- Color-coded status indicators

## Requirements

- Python 3.8 or higher
- Required packages:
  - customtkinter>=5.2.0
  - pygame>=2.5.0
  - tkinter (included with Python)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Activate the virtual environment (if not already activated):
   ```bash
   # Windows
   .\.venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate
   ```

2. Run the application:
   ```bash
   python automotive_gui.py
   ```

## Usage

### Vehicle Controls
- Use the speed input field to set target speed (0-180 km/h)
- Select driving mode from the dropdown menu
- Monitor RPM and speed on the gauges
- Watch for fuel level warnings (color-coded indicators)
- Use emergency brake button for immediate stop

### ADAS Features
- Toggle ACC switch to enable adaptive cruise control
- Toggle LKA switch for lane keeping assistance
- Monitor collision warnings in the system log
- Test airbag deployment and reset functionality
- Use emergency brake with automatic speed control

### Infotainment
- Use media controls to play/pause/next tracks
- Select audio directory to load music files
- Use navigation controls to:
  - Select different routes (Home → Office, Office → Mall, etc.)
  - Change map views (City, Highway, Country)
  - Monitor traffic conditions
  - View ETA information
  - Watch animated vehicle movement

### Diagnostics
- Monitor real-time vehicle metrics
- View system logs for important events
- Add user notes in the notes section
- Check color-coded status indicators

## System Architecture

The application is built with a modular architecture:

- `automotive_gui.py`: Main GUI application with modern UI
- `vehicle_control.py`: Vehicle control system with state management
- `adas.py`: Advanced driver assistance systems
- `infotainment.py`: Media and navigation features
- `logger.py`: System logging functionality

## Safety Features

- Emergency braking system with visual feedback
- Collision detection and prevention
- Airbag deployment simulation
- Speed limiting and monitoring
- System state monitoring
- Thread-safe operations

## Development

### Code Structure
- Thread-safe implementation with locks
- Event-driven architecture
- Modular design for easy extension
- Comprehensive error handling
- Performance optimizations

### Best Practices
- Thread safety with locks
- Rate limiting for system stability
- Proper resource cleanup
- Comprehensive logging
- UI responsiveness optimization

## Troubleshooting

### Common Issues

1. **Application not starting**
   - Ensure Python 3.8+ is installed
   - Verify all dependencies are installed
   - Check virtual environment is activated
   - Verify tkinter is available

2. **Missing dependencies**
   - Run `pip install -r requirements.txt`
   - Ensure tkinter is available (included with Python)
   - Check for pygame and customtkinter installation

3. **Performance issues**
   - Close other resource-intensive applications
   - Check system resources
   - Reduce update frequency if needed
   - Monitor system logs for bottlenecks

### Error Messages

- Check the system log for detailed error information
- Common errors are logged with appropriate severity levels
- User-friendly error messages are displayed in the GUI
- Color-coded status indicators for system state

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- CustomTkinter for the modern UI components
- Pygame for audio support
- Python community for various libraries and tools 
