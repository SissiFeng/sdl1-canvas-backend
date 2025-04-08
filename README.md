# Automated Electrochemical Experiment System

A modular and robust system for automated electrochemical experiments, integrating Opentrons liquid handling, Arduino-controlled pumps, and Biologic potentiostat control.

## Features

- **Automated Workflow**: Full automation of electrodeposition and characterization experiments
- **Modular Design**: Clean separation of device control, experiment management, and data handling
- **Robust Error Handling**: Comprehensive error detection and recovery mechanisms
- **Flexible Configuration**: Easy-to-modify experiment parameters through command-line interface
- **Detailed Logging**: Complete experiment tracking and debugging support

## System Requirements

- Python 3.8 or higher
- Opentrons OT-2 robot
- Arduino-controlled pump system
- Biologic potentiostat
- Linux/macOS/Windows operating system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/automated-electrochemical-experiment.git
cd automated-electrochemical-experiment
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
automated-electrochemical-experiment/
├── src/
│   ├── config/
│   │   ├── device_config.py
│   │   └── experiment_config.py
│   ├── core/
│   │   ├── devices/
│   │   │   ├── base_device.py
│   │   │   ├── opentrons_device.py
│   │   │   ├── arduino_device.py
│   │   │   └── biologic_device.py
│   │   └── experiment/
│   │       └── experiment_manager.py
│   ├── utils/
│   │   ├── logging_utils.py
│   │   └── data_utils.py
│   └── main.py
├── data/
├── logs/
├── requirements.txt
└── README.md
```

## Usage

### Basic Usage

Run a complete experiment (both deposition and characterization):
```bash
python src/main.py --run-number 001 --well C5 --experiment-type full
```

Run only deposition experiment:
```bash
python src/main.py --run-number 002 --well C5 --experiment-type deposition --deposition-current -0.003
```

Run only characterization experiment:
```bash
python src/main.py --run-number 003 --well C5 --experiment-type characterization
```

### Command Line Arguments

Required arguments:
- `--run-number`: Experiment run number
- `--well`: Well position to test (e.g., 'C5')
- `--experiment-type`: Type of experiment ('deposition', 'characterization', or 'full')

Optional arguments:
- `--robot-ip`: Opentrons robot IP address (default: 100.67.89.154)
- `--arduino-port`: Arduino device port
- `--biologic-port`: Biologic device USB port (default: USB0)
- `--deposition-current`: Deposition current in amperes (default: -0.002)
- `--deposition-duration`: Deposition duration in seconds (default: 60)

## Data Output

Experiment data is organized in the following structure:
```
data/
└── YYYYMMDD_RUN/
    ├── deposition/
    │   └── YYYYMMDD_RUN_XX_TECHNIQUE.csv
    └── characterization/
        └── YYYYMMDD_RUN_XX_TECHNIQUE.csv
```

Each experiment creates a new directory with the format `YYYYMMDD_RUN`, containing separate subdirectories for deposition and characterization data.

## Logging

Logs are stored in the `logs/` directory with the format `YYYYMMDD_RUN.log`. They include:
- Device connection status
- Experiment progress
- Error messages and stack traces
- Operation timestamps

## Error Handling

The system implements comprehensive error handling:
- Automatic retry for device connections
- Safe cleanup on failure
- Detailed error logging
- Graceful experiment termination

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Opentrons team for their robotics platform
- Biologic for their potentiostat control libraries
- The electrochemistry research community 
