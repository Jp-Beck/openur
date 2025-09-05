# OpenUR

A comprehensive Python library for controlling Universal Robots through their TCP/IP interfaces. OpenUR provides a unified interface for Dashboard Server, RTDE (Real-Time Data Exchange), and URScript commands.

## Features

- **Dashboard Server Integration**: Complete control over robot state, programs, and safety
- **RTDE Support**: Real-time data exchange for monitoring and control
- **URScript Interface**: Send and execute URScript programs
- **Context Manager Support**: Safe resource management with automatic cleanup
- **Comprehensive Error Handling**: Robust error handling and connection management
- **CLI Tools**: Command-line interface for configuration and testing

## Installation

```bash
pip install OpenUr
```

## Quick Start

```python
from openur import OpenUR

# Connect to robot
with OpenUR('192.168.1.11') as robot:
    # Check robot status
    if robot.is_in_remote():
        print("Robot is in remote control mode")

    # Get current joint positions
    joint_positions = robot.actual_q()
    print(f"Current joint positions: {joint_positions}")

    # Move robot
    robot.movej([0, -1.57, 0, -1.57, 0, 0])
```

## CLI Commands

### Create RTDE Configuration

```bash
openur make .                    # Create rtde_configuration.xml in current directory
openur make /path/to/config      # Create in specified directory
openur make . --force           # Overwrite existing file
```

### Test Robot Connection

```bash
openur test 192.168.1.11        # Test connection to robot
openur test 192.168.1.11 -t 30  # Test with 30 second timeout
```

## Configuration

Before using OpenUR, you need to create an RTDE configuration file:

```bash
openur make .
```

This creates `rtde_configuration.xml` with the necessary fields for data exchange.

## Documentation

For full documentation visit [Documentation](https://jp-beck.github.io/learnur/OpenUr/).

## Requirements

- Python 3.7+
- numpy>=1.19.4,<2.0.0
- math3d>=3.3.5

## License

GNU GPL v3 License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Project Structure

```
openur/
├── dashboard/          # Dashboard server interface
├── rtde_command/       # RTDE data exchange
├── urscript/          # URScript interface
├── connections/       # Connection management
└── cli.py            # Command-line interface
```

## Support

For support and questions, please open an issue on GitHub.
