import argparse
import os
import sys
import logging

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='OpenUR command line interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  openur make .                    # Create rtde_configuration.xml in current directory
  openur make /path/to/config      # Create rtde_configuration.xml in specified directory
  openur test 192.168.1.11        # Test connection to robot
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Make command
    make_parser = subparsers.add_parser('make', help='Create RTDE configuration file')
    make_parser.add_argument('directory', help='Directory to create rtde_configuration.xml in')
    make_parser.add_argument('--force', '-f', action='store_true',
                           help='Overwrite existing configuration file')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test robot connection')
    test_parser.add_argument('ip_address', help='Robot IP address')
    test_parser.add_argument('--timeout', '-t', type=int, default=10,
                           help='Connection timeout in seconds')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'make':
            make(args.directory, args.force)
        elif args.command == 'test':
            test_connection(args.ip_address, args.timeout)
    except Exception as e:
        logging.error(f"Command failed: {e}")
        sys.exit(1)

def make(directory, force=False):
    """Create RTDE configuration file."""
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    path = os.path.join(directory, 'rtde_configuration.xml')

    if os.path.exists(path) and not force:
        raise FileExistsError(f"File already exists: {path}. Use --force to overwrite.")

    content = '''<?xml version="1.0"?>
<rtde_config>
	<recipe key="rco">
		<field name="actual_q" type="VECTOR6D"/>
		<field name="actual_digital_input_bits" type="UINT64"/>
		<field name="actual_digital_output_bits" type="UINT64"/>
		<field name="actual_TCP_pose" type="VECTOR6D"/>
		<field name="actual_TCP_speed" type="VECTOR6D"/>
		<field name="actual_TCP_force" type="VECTOR6D"/>
		<field name="robot_mode" type="INT32"/>
		<field name="safety_mode" type="INT32"/>
		<field name="runtime_state" type="UINT32"/>
	</recipe>
	<recipe key="rci">
		<field name="speed_slider_mask" type="UINT32"/>
		<field name="speed_slider_fraction" type="DOUBLE"/>
		<field name="standard_digital_output_mask" type="UINT8"/>
		<field name="standard_digital_output" type="UINT8"/>
		<field name="configurable_digital_output_mask" type="UINT8"/>
		<field name="configurable_digital_output" type="UINT8"/>
	</recipe>
</rtde_config>
'''

    with open(path, 'w') as f:
        f.write(content)

    absolute_path = os.path.abspath(path)
    print(f'RTDE configuration file created at: {absolute_path}')

def test_connection(ip_address, timeout):
    """Test connection to robot."""
    try:
        from openur import OpenUR
        print(f"Testing connection to robot at {ip_address}...")

        with OpenUR(ip_address) as robot:
            if robot.is_connected():
                print("✓ Connection successful!")
                print(f"  Robot IP: {robot.ip_address}")
                print(f"  RTDE connected: {robot.rtde_cmd.is_connected()}")
                print(f"  Dashboard connected: {robot.dashboard.is_connected()}")
            else:
                print("✗ Connection failed!")
                sys.exit(1)

    except ImportError:
        print("Error: OpenUR package not properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)
